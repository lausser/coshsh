#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""HostGroup class for organizing hosts into logical groups.

This module defines the HostGroup class which groups hosts together for
organizational and monitoring purposes. Host groups can be used for
bulk operations, reporting, and visualization.
"""

from __future__ import annotations

import os
from typing import Dict, Any, Optional, List

import coshsh


class HostGroup(coshsh.item.Item):
    """Represents a logical group of hosts.

    HostGroups organize hosts by function, location, or any other criterion.
    They are useful for:
        - Organizing hosts in monitoring UI
        - Applying bulk operations
        - Reporting and analytics
        - Access control

    Attributes:
        hostgroup_name: Unique name of the host group
        alias: Human-readable description
        members: List of host names in this group (managed automatically)
        contacts: List of contact names for this group
        contactgroups: List of contact group names for this group
        templates: List of template names to inherit from

    Example Configuration:
        HostGroup({
            'hostgroup_name': 'webservers',
            'alias': 'Web Server Farm',
            'notes': 'Production web servers in datacenter A'
        })

    Automatic Membership:
        Hosts are automatically added to groups when they specify
        hostgroups attribute: host.hostgroups = ['webservers', 'production']

    Template Rendering:
        Renders to Nagios/Icinga hostgroup configuration using
        the 'hostgroup' template.
    """

    template_rules = [
        coshsh.templaterule.TemplateRule(
            needsattr=None,
            template="hostgroup",
            self_name="hostgroup",
            unique_attr="hostgroup_name",
            unique_config="hostgroup_%s"
        )
    ]

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """Initialize a HostGroup.

        Args:
            params: Dictionary of host group attributes including:
                - hostgroup_name: Required unique identifier
                - alias: Optional human-readable name
                - notes: Optional description/notes
        """
        params = params or {}

        # Initialize collections
        self.members: List[str] = []
        self.contacts: List[str] = []
        self.contactgroups: List[str] = []
        self.templates: List[str] = []

        super().__init__(params)

    def is_correct(self) -> bool:
        """Check if this hostgroup is valid.

        Returns:
            Always returns True (hostgroups are always valid once created)

        Note:
            This method exists for API compatibility with other Item types
        """
        return True

    def write_config(
        self,
        target_dir: str,
        want_tool: Optional[str] = None
    ) -> None:
        """Write hostgroup configuration files to disk.

        Creates a subdirectory under target_dir/hostgroups/<hostgroup_name>/
        and writes all config files for the specified tool(s).

        Args:
            target_dir: Base directory for output
            want_tool: Optional specific tool to write configs for
                      (e.g., "nagios", "icinga"). If None, writes all tools.

        Example:
            hostgroup.write_config("/etc/nagios/objects", "nagios")
            # Creates: /etc/nagios/objects/hostgroups/webservers/hostgroup_webservers.cfg
        """
        my_target_dir = os.path.join(target_dir, "hostgroups", self.hostgroup_name)

        if not os.path.exists(my_target_dir):
            os.makedirs(my_target_dir)

        for tool in self.config_files:
            if not want_tool or want_tool == tool:
                for filename in self.config_files[tool]:
                    content = self.config_files[tool][filename]
                    filepath = os.path.join(my_target_dir, filename)

                    with open(filepath, "w") as f:
                        f.write(content)

    def create_members(self) -> None:
        """Create or update member list.

        Note:
            Members are typically added automatically when hosts
            specify this hostgroup in their hostgroups attribute.
            This method exists for API compatibility.
        """
        pass

    def create_contacts(self) -> None:
        """Create or update contact associations.

        Note:
            This method exists for API compatibility.
            Contact handling is typically done in the recipe.
        """
        pass

    def create_templates(self) -> None:
        """Create or update template relationships.

        Note:
            This method exists for API compatibility.
            Template handling is typically done during rendering.
        """
        pass
