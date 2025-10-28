#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Datasource class for reading monitoring data from external sources.

This module defines the Datasource class which reads monitoring configuration
data from various sources (databases, CSV files, REST APIs, etc.) and creates
coshsh objects (Hosts, Applications, Contacts, etc.).
"""

from __future__ import annotations

import sys
import os
import re
import logging
import socket
from typing import Dict, Any, Optional, List

import coshsh

logger = logging.getLogger('coshsh')


class DatasourceNotImplemented(Exception):
    """Raised when no datasource plugin can handle the specified type."""
    pass


class DatasourceNotReady(Exception):
    """Raised when datasource is currently being updated.

    This indicates a temporary condition - the datasource exists but
    is not yet ready for reading.
    """
    pass


class DatasourceNotCurrent(Exception):
    """Raised when datasource was not updated recently.

    This indicates stale data - it makes no sense to continue
    processing with outdated information.
    """
    pass


class DatasourceNotAvailable(Exception):
    """Raised when datasource cannot be accessed.

    This indicates a connectivity or access problem with the
    data source (network error, authentication failure, etc.).
    """
    pass


class DatasourceCorrupt(Exception):
    """Raised when datasource data is corrupt or invalid.

    This indicates the data source is accessible but contains
    malformed or inconsistent data.
    """
    pass


class Datasource(coshsh.datainterface.CoshshDatainterface):
    """Base class for data sources that populate monitoring objects.

    A Datasource reads configuration data from external sources and
    creates coshsh objects. Examples include:
        - Database datasources (MySQL, PostgreSQL, Oracle)
        - File-based datasources (CSV, JSON, YAML)
        - REST API datasources
        - LDAP/Active Directory datasources
        - Custom datasources via plugins

    Plugin Discovery ("Reblessing" Pattern):
        Like Application and Contact, Datasource uses the reblessing
        pattern. The base class searches for a plugin that can handle
        the specified datasource type, then transforms into that class.

    Attributes:
        name: Unique identifier for this datasource
        objects: Dict of object collections by type (hosts, applications, etc.)
        hostname_transform_ops: List of hostname transformation operations

    Recipe Parameters:
        Parameters prefixed with "recipe_" are also set as attributes
        and made available as short names:
            recipe_foo=bar -> sets both self.recipe_foo and params['foo']

    Environment Substitution:
        String parameters containing %ENV_VAR% are expanded using
        environment variables.

    Hostname Transformation:
        Datasources can transform hostnames using operations like:
            - strip_domain: Remove domain suffix
            - to_lower: Convert to lowercase
            - to_upper: Convert to uppercase
            - append_domain: Add FQDN via getfqdn()
            - resolve_ip: Convert IP to hostname
            - resolve_dns: Resolve via DNS

    Object Storage:
        Objects are stored in self.objects dictionary:
            self.objects['hosts'][fingerprint] = host_object
            self.objects['applications'][fingerprint] = app_object

    Plugin Files:
        Plugin files should be named "datasource*.py" and contain
        a __ds_ident__ function that returns True/False to indicate
        if it handles this datasource type.

    Example Configuration:
        [datasource:mydb]
        type = mysql
        host = %DB_HOST%
        user = monitoring
        database = cmdb
        hostname_transform = strip_domain,to_lower
    """

    my_type = 'datasource'
    class_file_prefixes = ["datasource"]
    class_file_ident_function = "__ds_ident__"
    class_factory: List[tuple] = []

    def __init__(self, **params: Any):
        """Initialize a Datasource with plugin-based specialization.

        This method implements the "reblessing" pattern:
        1. Processes recipe_* parameters
        2. Expands environment variables in string parameters
        3. Searches for matching plugin class via get_class()
        4. If found, changes self.__class__ to the plugin class
        5. Re-initializes as the specialized class
        6. If not found, raises DatasourceNotImplemented

        Args:
            **params: Datasource configuration parameters including:
                - name: Required unique identifier
                - type: Datasource type (used for plugin matching)
                - recipe_*: Recipe-specific parameters
                - hostname_transform: Comma-separated transform operations
                - Additional type-specific parameters

        Raises:
            DatasourceNotImplemented: When no plugin can handle
                the specified datasource type

        Note:
            Environment variables in parameters are expanded:
                %DB_HOST% -> value of DB_HOST environment variable
        """
        # Process recipe_* parameters - copy to both self.recipe_* and short name
        for key in [k for k in params if k.startswith("recipe_")]:
            setattr(self, key, params[key])
            short = key.replace("recipe_", "")
            if short not in params:
                params[short] = params[key]

        # Expand environment variables in string parameters
        for key in list(params.keys()):
            if isinstance(params[key], str):
                params[key] = re.sub('%.*?%', coshsh.util.substenv, params[key])

        # Check if we're the base Datasource class
        if self.__class__ == Datasource:
            # Search for specialized plugin class
            newcls = self.__class__.get_class(params)
            if newcls:
                # Rebless to specialized class
                self.__class__ = newcls
                self.__init__(**params)
            else:
                # No plugin found - this is an error
                logger.critical(f'datasource for {params} is not implemented', exc_info=1)
                raise DatasourceNotImplemented(
                    f"No plugin found for datasource: {params.get('name', 'unknown')}"
                )
        else:
            # We've been reblessed - initialize datasource state
            setattr(self, 'name', params["name"])

            # Parse hostname transformation operations
            self.hostname_transform_ops: List[str] = []
            if "hostname_transform" in params and params["hostname_transform"]:
                self.hostname_transform_ops = [
                    op.strip() for op in params["hostname_transform"].split(",")
                ]

            # Initialize object storage
            self.objects: Dict[str, Dict[Any, Any]] = {}

    def open(self, **kwargs: Any) -> None:
        """Open connection to datasource.

        Subclasses should override this to establish connections
        to databases, open files, authenticate with APIs, etc.

        Args:
            **kwargs: Additional parameters for opening the datasource

        Note:
            Called by the recipe before read() is called.
        """
        pass

    def read(self, **kwargs: Any) -> None:
        """Read data from datasource and populate objects.

        Subclasses must override this to:
        1. Read data from the external source
        2. Create coshsh objects (Hosts, Applications, etc.)
        3. Add objects via self.add()

        Args:
            **kwargs: Additional parameters for reading

        Note:
            This is the main method datasources must implement.
        """
        pass

    def close(self) -> None:
        """Close connection to datasource.

        Subclasses should override this to close database connections,
        file handles, API sessions, etc.

        Note:
            Called by the recipe after read() completes.
        """
        pass

    def add(self, objtype: str, obj: Any) -> None:
        """Add an object to this datasource's collection.

        Args:
            objtype: Type of object (e.g., 'hosts', 'applications', 'contacts')
            obj: The object to add (must have fingerprint() method)

        Note:
            - Objects are stored by fingerprint for deduplication
            - Applications are automatically linked to their parent host
            - Object additions are recorded in chronicle for debugging
        """
        try:
            self.objects[objtype][obj.fingerprint()] = obj
        except KeyError:
            # First object of this type
            self.objects[objtype] = {}
            self.objects[objtype][obj.fingerprint()] = obj

        # Link applications to their parent host
        if objtype == 'applications':
            if self.find('hosts', obj.host_name):
                setattr(obj, 'host', self.get('hosts', obj.host_name))

        # Record in chronicle for debugging
        obj.record_in_chronicle(f"added to {objtype} in datasource {self.name}")

    def get(self, objtype: str, fingerprint: Any) -> Optional[Any]:
        """Get an object by type and fingerprint.

        Args:
            objtype: Type of object (e.g., 'hosts', 'applications')
            fingerprint: Object fingerprint (unique identifier)

        Returns:
            The object if found, None otherwise

        Example:
            host = datasource.get('hosts', 'web-server-01')
        """
        try:
            return self.objects[objtype][fingerprint]
        except (KeyError, TypeError):
            return None

    def getall(self, objtype: str) -> List[Any]:
        """Get all objects of a specific type.

        Args:
            objtype: Type of objects to retrieve

        Returns:
            List of objects, empty list if no objects of that type

        Example:
            all_hosts = datasource.getall('hosts')
        """
        try:
            return list(self.objects[objtype].values())
        except KeyError:
            return []

    def find(self, objtype: str, fingerprint: Any) -> bool:
        """Check if an object exists.

        Args:
            objtype: Type of object
            fingerprint: Object fingerprint

        Returns:
            True if object exists, False otherwise

        Example:
            if datasource.find('hosts', 'web-server-01'):
                # host exists
        """
        return objtype in self.objects and fingerprint in self.objects[objtype]

    def transform_hostname(self, hostname: str) -> str:
        """Transform hostname according to configured operations.

        Applies hostname_transform_ops in order. Operations include:
            - strip_domain: Remove domain suffix (foo.example.com -> foo)
            - to_lower: Convert to lowercase
            - to_upper: Convert to uppercase
            - append_domain: Add FQDN via socket.getfqdn()
            - resolve_ip: Convert IP address to hostname
            - resolve_dns: Resolve hostname via DNS

        Args:
            hostname: Original hostname

        Returns:
            Transformed hostname

        Example:
            # With ops: ['strip_domain', 'to_lower']
            'WEB-SERVER-01.example.com' -> 'web-server-01'

        Note:
            - IP addresses are preserved for strip_domain
            - DNS operations can fail - errors are logged but not fatal
            - Operations are applied in sequence
        """
        original = hostname

        def is_ip(s: str) -> bool:
            """Check if string is a valid IPv4 address."""
            try:
                socket.inet_aton(s)
                return True
            except socket.error:
                return False

        for op in self.hostname_transform_ops:
            if op == "strip_domain":
                if not is_ip(hostname):
                    hostname = hostname.split('.')[0]
            elif op == "to_lower":
                hostname = hostname.lower()
            elif op == "to_upper":
                hostname = hostname.upper()
            elif op == "append_domain":
                try:
                    fqdn = socket.getfqdn(hostname)
                    hostname = fqdn
                except Exception as e:
                    logger.warning(f"append_domain failed for {hostname}: {e}")
            elif op == "resolve_ip":
                if is_ip(hostname):
                    try:
                        hostname = socket.gethostbyaddr(hostname)[0]
                    except Exception as e:
                        logger.warning(f"resolve_ip failed for {hostname}: {e}")
            elif op == "resolve_dns":
                try:
                    hostname = socket.getfqdn(hostname)
                except Exception as e:
                    logger.warning(f"resolve_dns failed for {hostname}: {e}")
            else:
                logger.warning(f"Unknown hostname transform operation: {op}")

        logger.debug(f"Transformed hostname: {original} -> {hostname}")
        return hostname
