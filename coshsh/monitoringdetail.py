#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""MonitoringDetail class for monitoring-specific configuration details.

This module defines the MonitoringDetail class which represents
additional monitoring configuration data (e.g., SNMP credentials,
database connection strings, API endpoints) that augment applications.
"""

from __future__ import annotations

import sys
import os
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

import coshsh

logger = logging.getLogger('coshsh')


class MonitoringDetailNotImplemented(Exception):
    """Raised when no plugin can handle a specific monitoring detail type."""
    pass


class MonitoringDetail(coshsh.item.Item):
    """Represents additional monitoring configuration details.

    MonitoringDetails provide extra configuration data needed for monitoring
    specific applications. Examples include:
        - SNMP community strings and OIDs
        - Database connection credentials
        - API endpoints and authentication tokens
        - Custom check parameters

    Plugin Discovery ("Reblessing" Pattern):
        Like Contact and Application, MonitoringDetail uses the reblessing
        pattern. The base class searches for a plugin that can handle the
        specific monitoring_type, then transforms into that specialized class.

    Attributes:
        monitoring_type: Type of monitoring detail (e.g., "SNMP", "URL", "DB")
        monitoring_0: Primary parameter value (type depends on monitoring_type)
        monitoring_1-N: Additional parameters as needed
        host_name: Host this detail applies to
        application_name: Application this detail applies to (optional)
        application_type: Application type (optional)

    Name Mapping:
        For compatibility, "name" and "type" parameters are automatically
        mapped to "application_name" and "application_type":
            params['name'] -> params['application_name']
            params['type'] -> params['application_type']

    Example Configuration:
        MonitoringDetail({
            'monitoring_type': 'URL',
            'monitoring_0': 'http://example.com/api/health',
            'host_name': 'web-server-01',
            'application_name': 'webapp',
            'application_type': 'webservice'
        })

    Plugin Files:
        Plugin files should be named "detail_*.py" and contain a
        __detail_ident__ function that returns True/False to indicate
        if the plugin handles this detail type.

    Comparison:
        MonitoringDetails are ordered by (monitoring_type, monitoring_0)
        for sorting and deduplication purposes.
    """

    # Plugin discovery configuration
    class_factory: List[tuple] = []
    class_file_prefixes = ["detail_"]
    class_file_ident_function = "__detail_ident__"
    my_type = "detail"

    # Columns that should be lowercased
    lower_columns = ['name', 'type', 'application_name', 'application_type']

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """Initialize a MonitoringDetail with plugin-based specialization.

        This method implements the "reblessing" pattern:
        1. Normalizes lowercase columns
        2. Maps "name"/"type" to "application_name"/"application_type"
        3. Searches for matching plugin class via get_class()
        4. If found, changes self.__class__ to the plugin class
        5. Re-initializes as the specialized class
        6. If no plugin found, raises MonitoringDetailNotImplemented

        Args:
            params: Dictionary of detail attributes including:
                - monitoring_type: Required - type of monitoring detail
                - monitoring_0: Primary parameter
                - host_name: Host this detail applies to
                - application_name/name: Application identifier
                - application_type/type: Application type

        Raises:
            MonitoringDetailNotImplemented: When no plugin can handle
                the specified monitoring_type

        Note:
            Unlike Contact, if no plugin is found, this raises an
            exception rather than using a generic fallback class.
        """
        params = params or {}

        # Only do initialization if we're the base MonitoringDetail class
        if self.__class__.__name__ == "MonitoringDetail":
            # Normalize lowercase columns
            for column in self.__class__.lower_columns:
                try:
                    if column in params and params[column] is not None:
                        params[column] = params[column].lower()
                except (AttributeError, TypeError):
                    if column in params:
                        params[column] = None

            # Map name/type to application_name/application_type
            # Details can be host-level or application-level
            if 'name' in params:
                params['application_name'] = params['name']
                del params['name']
            if 'type' in params:
                params['application_type'] = params['type']
                del params['type']

            # Search for specialized plugin class
            newcls = self.__class__.get_class(params)
            if newcls:
                # Rebless to specialized class
                self.__class__ = newcls
                super(MonitoringDetail, self).__init__(params)
                self.__init__(params)
            else:
                # No plugin found - this is an error
                mon_type = params.get("monitoring_type", "unknown")
                host = params.get("host_name", "unkn. host")
                app = params.get("application_name", "unkn. application")
                logger.info(
                    f"monitoring detail of type {mon_type} for host {host} / "
                    f"appl {app} had a problem"
                )
                raise MonitoringDetailNotImplemented(
                    f"No plugin found for monitoring detail type: {mon_type}"
                )
        else:
            # We've already been reblessed - subclass handles init
            pass

    def fingerprint(self) -> int:
        """Return unique identifier for this detail.

        Returns:
            Python object id (memory address)

        Note:
            Uses id(self) rather than constructing from attributes
            because monitoring details can have arbitrary attributes.
            Each detail instance is considered unique.
        """
        return id(self)

    def application_fingerprint(self) -> str:
        """Return fingerprint for the application this detail belongs to.

        Returns:
            Application fingerprint string in format:
                - "<host>+<app_name>+<app_type>" for application details
                - "<host>" for host-level details

        Raises:
            ValueError: If unable to construct a valid fingerprint

        Note:
            Used to associate this detail with its parent application
            or host during object graph construction.
        """
        if (hasattr(self, 'application_name') and self.application_name and
            hasattr(self, 'application_type') and self.application_type):
            return f"{self.host_name}+{self.application_name}+{self.application_type}"
        elif hasattr(self, 'host_name') and self.host_name:
            return f"{self.host_name}"
        else:
            raise ValueError("Cannot construct application fingerprint - missing required attributes")

    def __eq__(self, other: object) -> bool:
        """Check equality based on monitoring_type and monitoring_0.

        Args:
            other: Another MonitoringDetail to compare

        Returns:
            True if monitoring_type and monitoring_0 match
        """
        if not isinstance(other, MonitoringDetail):
            return NotImplemented
        return (
            (self.monitoring_type, str(self.monitoring_0)) ==
            (other.monitoring_type, str(other.monitoring_0))
        )

    def __ne__(self, other: object) -> bool:
        """Check inequality based on monitoring_type and monitoring_0."""
        if not isinstance(other, MonitoringDetail):
            return NotImplemented
        return (
            (self.monitoring_type, str(self.monitoring_0)) !=
            (other.monitoring_type, str(other.monitoring_0))
        )

    def __lt__(self, other: MonitoringDetail) -> bool:
        """Check less-than for sorting by monitoring_type and monitoring_0."""
        if not isinstance(other, MonitoringDetail):
            return NotImplemented
        return (
            (self.monitoring_type, str(self.monitoring_0)) <
            (other.monitoring_type, str(other.monitoring_0))
        )

    def __le__(self, other: MonitoringDetail) -> bool:
        """Check less-than-or-equal for sorting."""
        if not isinstance(other, MonitoringDetail):
            return NotImplemented
        return (
            (self.monitoring_type, str(self.monitoring_0)) <=
            (other.monitoring_type, str(other.monitoring_0))
        )

    def __gt__(self, other: MonitoringDetail) -> bool:
        """Check greater-than for sorting."""
        if not isinstance(other, MonitoringDetail):
            return NotImplemented
        return (
            (self.monitoring_type, str(self.monitoring_0)) >
            (other.monitoring_type, str(other.monitoring_0))
        )

    def __ge__(self, other: MonitoringDetail) -> bool:
        """Check greater-than-or-equal for sorting."""
        if not isinstance(other, MonitoringDetail):
            return NotImplemented
        return (
            (self.monitoring_type, str(self.monitoring_0)) >=
            (other.monitoring_type, str(other.monitoring_0))
        )

    def __repr__(self) -> str:
        """Return string representation for debugging.

        Returns:
            String showing monitoring_type and monitoring_0
        """
        return f"{self.monitoring_type} {self.monitoring_0}"
