"""Monitoring Depth Detail Plugin

This plugin configures monitoring depth/verbosity levels.

Plugin Identification:
---------------------
Identifies monitoring details with monitoring_type = "DEPTH".

Purpose:
--------
Controls how detailed/verbose monitoring should be for an application:
    - Level 0: Disabled (ignore monitoring)
    - Level 1: Minimum monitoring (basic checks only)
    - Level 2: Standard monitoring (common checks)
    - Level 3+: Detailed/expert monitoring (all checks, debugging)

Use Cases:
----------
- Gradually enable monitoring (start at level 1, increase over time)
- Reduce check load during incidents (temporarily lower depth)
- Different monitoring levels for dev/test/prod environments
- Conditional check generation in templates

Input Format:
-------------
CSV Format (monitoring_N columns):
    monitoring_type = DEPTH
    monitoring_0 = level (integer 0-n, default: 1)

Parameters:
-----------
- level: Monitoring depth level (integer)
    Values:
        0 = Disabled (no monitoring)
        1 = Minimum (basic health checks only)
        2 = Standard (typical production monitoring)
        3 = Detailed (comprehensive monitoring)
        4+ = Expert/Debug (all available checks)

Template Usage:
---------------
The 'monitoring_depth' property is set as an integer value on the
application/host. Templates use this to conditionally generate checks.

Example template:
    {% if application.monitoring_depth >= 1 %}
    define service {
        host_name               {{ application.host_name }}
        service_description     Basic Health Check
        check_command           check_health
    }
    {% endif %}

    {% if application.monitoring_depth >= 2 %}
    define service {
        host_name               {{ application.host_name }}
        service_description     Performance Metrics
        check_command           check_performance
    }
    {% endif %}

    {% if application.monitoring_depth >= 3 %}
    define service {
        host_name               {{ application.host_name }}
        service_description     Detailed Diagnostics
        check_command           check_diagnostics
    }
    {% endif %}

Configuration Examples:
----------------------
CSV datasource (applicationdetails.csv):
    host_name,name,type,monitoring_type,monitoring_0
    prod01,app,webserver,DEPTH,2
    test01,app,webserver,DEPTH,3
    dev01,app,webserver,DEPTH,1
    legacy01,app,old,DEPTH,0

Explanation:
    - prod01: Level 2 (standard production monitoring)
    - test01: Level 3 (detailed test environment monitoring)
    - dev01: Level 1 (minimal dev monitoring)
    - legacy01: Level 0 (disabled, being decommissioned)

Monitoring Level Guidelines:
---------------------------
Level 0 (Disabled):
    - System being decommissioned
    - Temporary disable during maintenance
    - Not yet ready for monitoring

Level 1 (Minimum):
    - Basic health check only
    - Is the application responding?
    - Development environments
    - Low-priority systems

Level 2 (Standard):
    - Production monitoring baseline
    - Health, performance, key metrics
    - Typical for most applications
    - Recommended default

Level 3 (Detailed):
    - Test/staging environments
    - Critical production systems
    - Comprehensive monitoring
    - All standard checks plus extras

Level 4+ (Expert/Debug):
    - Troubleshooting scenarios
    - All available checks enabled
    - May include expensive operations
    - Use sparingly in production

Classes:
--------
- MonitoringDetailDepth: Monitoring depth/verbosity level
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import coshsh
from coshsh.monitoringdetail import MonitoringDetail


def __detail_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify DEPTH monitoring details.

    Called by the plugin factory system to determine if a monitoring
    detail should be upgraded to a MonitoringDetailDepth object.

    Args:
        params: Monitoring detail attributes dictionary

    Returns:
        MonitoringDetailDepth class if monitoring_type="DEPTH"
        None if no match

    Example:
        params = {'monitoring_type': 'DEPTH', 'monitoring_0': '2'}
        Returns: MonitoringDetailDepth class

        params = {'monitoring_type': 'TAG', 'monitoring_0': 'production'}
        Returns: None
    """
    if params is None:
        params = {}

    if params.get("monitoring_type") == "DEPTH":
        return MonitoringDetailDepth
    return None


class MonitoringDetailDepth(coshsh.monitoringdetail.MonitoringDetail):
    """Monitoring depth level detail.

    Describes how deep/verbose the monitoring of an application should be.
    Levels are 0 (ignore), 1 (minimum) ... n (expert level, debugging).

    Attributes:
        monitoring_type: Always "DEPTH"
        monitoring_depth: Depth level (integer 0-n)

    Class Attributes:
        property: "monitoring_depth" - property name on application/host
        property_type: int - stored as integer
        property_flat: True - value is stored directly (not nested object)

    Example:
        detail = MonitoringDetailDepth({
            'monitoring_type': 'DEPTH',
            'monitoring_0': '2'
        })

        # Used in template:
        if application.monitoring_depth >= 2:
            # Generate standard monitoring checks
            pass
    """

    # Property name added to application/host
    property = "monitoring_depth"

    # Property type (integer value)
    property_type = int

    # Flat property (stored directly as value, not nested object)
    property_flat = True

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize monitoring depth detail.

        Args:
            params: Dictionary with depth parameters

        CSV Format:
            monitoring_0: level (integer, default: 1)

        Note:
            The depth is converted to integer. If not provided or
            invalid, defaults to level 1 (minimum monitoring).
        """
        self.monitoring_type = params["monitoring_type"]
        self.monitoring_depth = int(params.get("monitoring_0", 1))

    def __str__(self) -> str:
        """Return string representation for debugging.

        Returns:
            String containing the monitoring depth level

        Example:
            "0" (disabled)
            "1" (minimum)
            "2" (standard)
            "3" (detailed)

        Note:
            Returns the depth as a string for logging/debugging.
        """
        return f"{self.monitoring_depth}"
