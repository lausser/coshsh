#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Host class for representing monitored hosts/devices.

This module defines the Host class which represents a single host or device
in the monitoring system. Hosts are the primary objects in coshsh - they
contain applications, have attributes, and generate monitoring configurations.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List

import coshsh


class Host(coshsh.item.Item):
    """Represents a single host or device in the monitoring system.

    A Host is a physical or virtual machine, network device, or any other
    entity that can be monitored. Each host can have multiple applications
    running on it and various attributes.

    Attributes:
        host_name: Unique identifier for the host (FQDN recommended)
        address: IP address or resolvable hostname
        alias: Human-readable alias (defaults to host_name)
        type: Host type (e.g., "server", "switch", "storage")
        os: Operating system (e.g., "linux", "windows", "ios")
        hardware: Hardware type or model
        virtual: Virtualization type (e.g., "vmware", "kvm", "physical")
        location: Physical location
        department: Organizational unit
        hostgroups: List of hostgroup names this host belongs to
        contacts: List of contact names for notifications
        contact_groups: List of contact group names for notifications
        templates: List of template names to inherit from
        ports: List of ports (default: [22])
        macros: Dict of custom macros for this host

    Column Normalization:
        The following attributes are automatically lowercased:
        - address, type, os, hardware, virtual, location, department

    Example Configuration:
        Host({
            'host_name': 'web-server-01.example.com',
            'address': '192.168.1.10',
            'alias': 'Web Server 01',
            'type': 'server',
            'os': 'linux',
            'hardware': 'dell r740',
            'virtual': 'vmware',
            'location': 'datacenter-a',
            'department': 'web-services'
        })

    Template Rendering:
        Renders to Nagios/Icinga host configuration using the 'host' template.

    Applications:
        Hosts contain Application objects which represent services/software
        running on the host. Applications are added via datasources.
    """

    template_rules = [
        coshsh.templaterule.TemplateRule(
            needsattr=None,
            template="host",
            self_name="host"
        )
    ]

    # Columns that should be automatically lowercased
    lower_columns = [
        'address', 'type', 'os', 'hardware',
        'virtual', 'location', 'department'
    ]

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """Initialize a Host.

        Args:
            params: Dictionary of host attributes including:
                - host_name: Required unique identifier
                - address: Required IP address or hostname
                - type, os, hardware, virtual, location, department: Optional attributes
                - Any other attributes are set dynamically

        The __init__ method performs these operations:
        1. Normalizes lower_columns to lowercase
        2. Initializes collections (hostgroups, contacts, etc.)
        3. Calls parent Item.__init__
        4. Sets default alias if not provided
        5. Initializes macros dict
        6. Sets up fingerprint lambda
        """
        params = params or {}

        # Normalize lowercase columns
        for column in self.__class__.lower_columns:
            try:
                if column in params and params[column] is not None:
                    params[column] = params[column].lower()
            except (AttributeError, TypeError):
                # Handle non-string values
                if column in params:
                    params[column] = None

        # Initialize collections
        self.hostgroups: List[str] = []
        self.contacts: List[str] = []
        self.contact_groups: List[str] = []
        self.templates: List[str] = []
        self.ports: List[int] = [22]  # Default SSH port, can be changed with PORT detail

        # Call parent constructor
        super().__init__(params)

        # Set alias default
        self.alias = getattr(self, 'alias', self.host_name)

        # Initialize macros if not present
        if not hasattr(self, "macros"):
            self.macros: Dict[str, Any] = {}

        # Set up fingerprint lambda for compatibility
        self.fingerprint = lambda s=self: s.__class__.fingerprint(params)

    @classmethod
    def fingerprint(cls, params: Dict[str, Any]) -> str:
        """Return unique identifier for this host.

        Args:
            params: Dictionary containing host_name

        Returns:
            The host_name which uniquely identifies this host

        Note:
            Used for deduplication and lookups in object dictionaries.
            Each host must have a unique host_name.
        """
        return f"{params['host_name']}"

    def is_correct(self) -> bool:
        """Check if this host is valid.

        Returns:
            True if host has a non-None host_name, False otherwise

        Note:
            This is a basic validation. More complex validation
            could be added in subclasses.
        """
        return hasattr(self, 'host_name') and self.host_name is not None

    def create_hostgroups(self) -> None:
        """Create or update hostgroup associations.

        Note:
            Hostgroups are typically managed automatically by the recipe.
            This method exists for API compatibility and can be overridden
            in subclasses for custom logic.
        """
        pass

    def create_contacts(self) -> None:
        """Create or update contact associations.

        Note:
            Contacts are typically managed via datasources.
            This method exists for API compatibility and can be overridden
            in subclasses for custom logic.
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

    def __str__(self) -> str:
        """Return human-readable string representation.

        Returns:
            String showing host_name and address
        """
        address = getattr(self, 'address', 'no-address')
        return f"Host({self.host_name} @ {address})"
