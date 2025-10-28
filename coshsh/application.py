#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Application class for representing software/services running on hosts.

This module defines the Application class which represents software
applications, services, or operating systems running on monitored hosts.
Applications support plugin-based specialization through the "reblessing" pattern.
"""

from __future__ import annotations

import sys
import os
import logging
from typing import Dict, Any, Optional, List, Callable

import coshsh

logger = logging.getLogger('coshsh')


class Application(coshsh.item.Item):
    """Represents a software application or service on a host.

    An Application is a piece of software running on a host that needs
    monitoring. Examples include:
        - Web servers (Apache, Nginx)
        - Databases (MySQL, PostgreSQL, Oracle)
        - Application servers (Tomcat, JBoss)
        - Operating systems (Linux, Windows)
        - Custom applications

    Plugin Discovery ("Reblessing" Pattern):
        Like Contact and MonitoringDetail, Application uses the reblessing
        pattern. The base class searches for a plugin that can handle the
        specific application type, then transforms into that specialized class.

    Attributes:
        name: Application instance name (e.g., "apache-prod")
        type: Application type (e.g., "webserver", "database")
        host_name: Host this application runs on
        component: Application component identifier
        version: Application version
        patchlevel: Patch level or minor version
        contact_groups: List of contact group names for notifications
        fingerprint: Callable returning unique identifier

    Column Normalization:
        The following attributes are automatically lowercased:
        - name, type, component, version, patchlevel

    Example Configuration:
        Application({
            'host_name': 'web-server-01',
            'name': 'apache-prod',
            'type': 'webserver',
            'version': '2.4',
            'component': 'frontend'
        })

    Plugin Files:
        Plugin files should be named with prefixes:
        - "app_*.py" for application-specific plugins
        - "os_*.py" for operating system plugins

        Each plugin must contain a __mi_ident__ function that returns
        True/False to indicate if it handles this application.

    Generic Fallback:
        If no plugin matches, the application becomes a GenericApplication
        which can still render monitoring configuration if it has
        monitoring_details with processes, ports, URLs, etc.

    Template Rendering:
        Applications render to Nagios/Icinga service configurations.
        Each application plugin defines its own template_rules.
    """

    # Plugin discovery configuration
    class_factory: List[tuple] = []
    class_file_prefixes = ["app_", "os_"]
    class_file_ident_function = "__mi_ident__"
    my_type = "application"

    # Columns that should be lowercased
    lower_columns = ['name', 'type', 'component', 'version', 'patchlevel']

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """Initialize an Application with plugin-based specialization.

        This method implements the "reblessing" pattern:
        1. Normalizes lowercase columns
        2. Searches for matching plugin class via get_class()
        3. If found, changes self.__class__ to the plugin class
        4. Re-initializes as the specialized class
        5. If not found, becomes GenericApplication

        Args:
            params: Dictionary of application attributes including:
                - host_name: Required - host this application runs on
                - name: Required - application instance name
                - type: Required - application type
                - version, component, patchlevel: Optional attributes

        Note:
            The contact_groups list is initialized before calling
            parent __init__ to ensure it's available during reblessing.
        """
        params = params or {}

        # Only do initialization if we're the base Application class
        if self.__class__.__name__ == "Application":
            # Normalize lowercase columns
            for column in self.__class__.lower_columns:
                try:
                    if column in params and params[column] is not None:
                        params[column] = params[column].lower()
                except (AttributeError, TypeError):
                    if column in params:
                        params[column] = None

            # Search for specialized plugin class
            newcls = self.__class__.get_class(params)
            if newcls:
                # Rebless to specialized class
                self.__class__ = newcls
                self.contact_groups: List[str] = []
                super(Application, self).__init__(params)
                self.__init__(params)
                self.fingerprint: Callable = lambda s=self: s.__class__.fingerprint(params)
            else:
                # No plugin found - use GenericApplication
                logger.debug(f'this will be Generic {params}')
                self.__class__ = GenericApplication
                self.contact_groups = []
                super(Application, self).__init__(params)
                self.__init__(params)
                self.fingerprint = lambda s=self: s.__class__.fingerprint(params)
        else:
            # We've already been reblessed - subclass handles init
            pass

    @classmethod
    def fingerprint(cls, params: Optional[Dict[str, Any]] = None) -> str:
        """Return unique identifier for this application.

        Args:
            params: Dictionary containing host_name, name, and type

        Returns:
            Fingerprint string in format: "<host_name>+<name>+<type>"

        Note:
            Used for deduplication and lookups. Applications are unique
            per host based on name and type combination.
        """
        params = params or {}
        return f"{params['host_name']}+{params['name']}+{params['type']}"

    def create_servicegroups(self) -> None:
        """Create or update service group associations.

        Note:
            Service groups are typically managed automatically by the recipe.
            This method exists for API compatibility and can be overridden
            in subclasses for custom logic.
        """
        pass

    def create_contacts(self) -> None:
        """Create or update contact associations.

        Note:
            Contacts are typically managed via datasources or inherited
            from hosts. This method exists for API compatibility and can
            be overridden in subclasses for custom logic.
        """
        pass

    def create_templates(self) -> None:
        """Create or update template relationships.

        Note:
            Templates are typically set via datasources or plugins.
            This method exists for API compatibility and can be overridden
            in subclasses for custom logic.
        """
        pass


class GenericApplication(Application):
    """Fallback application class when no specialized plugin matches.

    GenericApplication handles applications that don't have a specific
    plugin. It can still generate monitoring configuration if the
    application has monitoring_details with discoverable attributes
    like processes, ports, URLs, filesystems, etc.

    Template Rules:
        Uses the "app_generic_default" template with unique configuration
        per application type and name.

    Conditional Rendering:
        Only renders configuration if the application has at least one
        of these attributes (populated by monitoring_details):
            - processes: Process names to monitor
            - filesystems: Filesystem mount points
            - cfgfiles: Configuration files to check
            - files: Generic files to monitor
            - ports: Network ports to check
            - urls: URLs to monitor
            - services: Windows services to monitor

    Example:
        An unknown application type with monitoring details:

        app = GenericApplication({
            'host_name': 'server-01',
            'name': 'custom-app',
            'type': 'unknown'
        })

        # Add monitoring details via datasource
        app.processes = ['custom-daemon']
        app.ports = [8080, 8443]

        # Will render generic monitoring configuration
    """

    template_rules = [
        coshsh.templaterule.TemplateRule(
            needsattr=None,
            template="app_generic_default",
            unique_attr=['type', 'name'],
            unique_config="app_%s_%s_default"
        )
    ]

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """Initialize a GenericApplication.

        Args:
            params: Dictionary of application attributes
        """
        params = params or {}
        super().__init__(params)

    def render(
        self,
        template_cache: Any,
        jinja2: Any,
        recipe: Any
    ) -> int:
        """Render generic application configuration.

        This method checks if the application has any discoverable
        monitoring attributes. If it does, it renders configuration
        using the generic template. If not, it returns 0 to indicate
        no configuration should be generated.

        Args:
            template_cache: Template cache object
            jinja2: Jinja2 environment
            recipe: Recipe object containing configuration

        Returns:
            Result of parent render() if attributes found, 0 otherwise

        Note:
            The check for monitoring attributes prevents generating
            empty configuration files for applications with no
            actual monitoring details.
        """
        # Check if we have any monitorable attributes
        has_monitoring = any([
            hasattr(self, "processes") and self.processes,
            hasattr(self, "filesystems") and self.filesystems,
            hasattr(self, "cfgfiles") and self.cfgfiles,
            hasattr(self, "files") and self.files,
            hasattr(self, "ports") and self.ports,
            hasattr(self, "urls") and self.urls,
            hasattr(self, "services") and self.services
        ])

        if has_monitoring:
            return super().render(template_cache, jinja2, recipe)
        else:
            # No monitoring details - don't generate empty config
            return 0
