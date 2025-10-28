#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""ContactGroup class for organizing notification contacts.

This module defines the ContactGroup class which groups contacts together
for notification purposes. Contact groups can be assigned to hosts and
services to control who receives alerts.
"""

from __future__ import annotations

import os
from typing import Dict, Any, Optional, List

import coshsh


class ContactGroup(coshsh.item.Item):
    """Represents a group of contacts for notifications.

    ContactGroups organize contacts into logical groups (e.g., by team,
    shift, or responsibility area). They can be assigned to hosts and
    services to control notification routing.

    Attributes:
        contactgroup_name: Unique name of the contact group
        alias: Human-readable alias/description (optional)
        members: List of contact names in this group

    Example Configuration:
        ContactGroup({
            'contactgroup_name': 'linux-admins',
            'alias': 'Linux System Administrators'
        })

    Usage in Host/Service:
        A host or service can specify contact_groups to receive notifications:
        host.contact_groups = ['linux-admins', 'oncall-team']
    """

    template_rules = [
        coshsh.templaterule.TemplateRule(
            template="contactgroup",
            self_name="contactgroup",
            unique_attr="contactgroup_name",
            unique_config="contactgroup_%s"
        )
    ]

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """Initialize a ContactGroup.

        Args:
            params: Dictionary of contact group attributes including:
                - contactgroup_name: Required unique identifier
                - alias: Optional human-readable name
        """
        params = params or {}
        self.members: List[str] = []
        super().__init__(params)

        # Set up fingerprint as lambda for compatibility
        self.fingerprint = lambda s=self: s.__class__.fingerprint(params)

    @classmethod
    def fingerprint(cls, params: Dict[str, Any]) -> str:
        """Return unique identifier for this contact group.

        Args:
            params: Dictionary containing contactgroup_name

        Returns:
            The contactgroup_name which uniquely identifies this group

        Note:
            Used for deduplication and lookups in object dictionaries
        """
        return f"{params['contactgroup_name']}"

    def __str__(self) -> str:
        """Return human-readable string representation.

        Returns:
            String in format "contactgroup <contactgroup_name>"
        """
        return f"contactgroup {self.contactgroup_name}"
