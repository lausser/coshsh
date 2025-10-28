#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Dependency class for host dependency relationships.

This module defines the Dependency class which represents parent-child
relationships between hosts in monitoring configurations.
"""

from __future__ import annotations

from typing import Dict, Any, Optional


class Dependency:
    """Represents a dependency relationship between two hosts.

    Dependencies define parent-child relationships in monitoring.
    When a parent host fails, notifications for dependent child hosts
    can be suppressed to avoid alert storms.

    Attributes:
        host_name: The dependent (child) host name
        parent_host_name: The parent host name

    Example:
        A server depends on its network switch. If the switch fails,
        we don't want alerts for the server being unreachable:

        Dependency({
            'host_name': 'web-server-01',
            'parent_host_name': 'switch-core-01'
        })

    Usage:
        Dependencies are typically created by datasources when reading
        network topology or infrastructure data.
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """Initialize a Dependency relationship.

        Args:
            params: Dictionary containing:
                - host_name: Required - the dependent host
                - parent_host_name: Required - the parent host
        """
        params = params or {}
        self.host_name: str = params["host_name"]
        self.parent_host_name: str = params["parent_host_name"]

    def __str__(self) -> str:
        """Return human-readable string representation.

        Returns:
            String showing the dependency relationship
        """
        return f"Dependency({self.host_name} depends on {self.parent_host_name})"
