"""Process Monitoring Detail Plugin

This plugin handles process/service monitoring configuration.

Plugin Identification:
---------------------
Identifies monitoring details with monitoring_type = "PROCESS".

Purpose:
--------
Configures process monitoring including:
    - Process name or pattern matching
    - Instance count thresholds (using Nagios range syntax)
    - Process aliases for display names

Input Format:
-------------
CSV Format (monitoring_N columns):
    monitoring_type = PROCESS
    monitoring_0 = name (process name or pattern)
    monitoring_1 = warning (default: "1:1" = exactly 1 instance)
    monitoring_2 = critical (default: "1:" = at least 1 instance)
    monitoring_3 = alias (display name, defaults to name)

Parameters:
-----------
- name: Process name or pattern to match
    Examples:
        httpd → Match process named "httpd"
        java.*tomcat → Match pattern (if supported by check command)
        sshd → Match SSH daemon

- warning: Warning threshold using Nagios range syntax
    Format: [start]:[end]
    Examples:
        "1:1" → Exactly 1 instance (default warning)
        "1:5" → Between 1 and 5 instances
        "5:" → At least 5 instances
        ":10" → At most 10 instances
        "0:0" → Zero instances (process should not run)

- critical: Critical threshold using Nagios range syntax
    Format: [start]:[end]
    Examples:
        "1:" → At least 1 instance (default critical)
        "1:3" → Between 1 and 3 instances
        "2:" → At least 2 instances
        "0:0" → Zero instances

- alias: Display name for the process (optional)
    Used in service descriptions
    Defaults to the process name if not specified

Nagios Range Syntax:
--------------------
Range syntax defines acceptable values:
    "10" → Alert if NOT equal to 10
    "10:" → Alert if less than 10
    ":10" → Alert if greater than 10
    "10:20" → Alert if outside 10-20 range
    "@10:20" → Alert if inside 10-20 range (inverted)

Common patterns for process counts:
    "1:1" → Exactly 1 (typical for singleton daemons)
    "1:" → At least 1 (process must be running)
    "0:0" → Exactly 0 (process should NOT run)
    "2:5" → Between 2 and 5 (load-balanced services)

Template Usage:
---------------
The 'processes' property is populated as a list on the application/host.
Templates can iterate over this list to generate individual checks.

Example template:
    {% for proc in application.processes %}
    define service {
        host_name               {{ application.host_name }}
        service_description     Process {{ proc.alias }}
        check_command           check_procs!{{ proc.warning }}!{{ proc.critical }}!{{ proc.name }}
    }
    {% endfor %}

Configuration Examples:
----------------------
CSV datasource (applicationdetails.csv):
    host_name,name,type,monitoring_type,monitoring_0,monitoring_1,monitoring_2,monitoring_3
    server01,os,linux,PROCESS,httpd,1:10,1:,Apache
    server01,os,linux,PROCESS,sshd,1:1,1:,SSH Daemon
    server02,os,linux,PROCESS,mysqld,1:1,1:,MySQL
    server03,app,tomcat,PROCESS,java,1:5,1:,Tomcat

Explanation:
    - server01 httpd: 1-10 instances warn, ≥1 crit, display as "Apache"
    - server01 sshd: Exactly 1 warn, ≥1 crit, display as "SSH Daemon"
    - server02 mysqld: Exactly 1 warn, ≥1 crit, display as "MySQL"
    - server03 java: 1-5 instances warn, ≥1 crit, display as "Tomcat"

Classes:
--------
- MonitoringDetailProcess: Process monitoring detail
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any

import coshsh
from coshsh.monitoringdetail import MonitoringDetail

logger = logging.getLogger('coshsh')


def __detail_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify PROCESS monitoring details.

    Called by the plugin factory system to determine if a monitoring
    detail should be upgraded to a MonitoringDetailProcess object.

    Args:
        params: Monitoring detail attributes dictionary

    Returns:
        MonitoringDetailProcess class if monitoring_type="PROCESS"
        None if no match

    Example:
        params = {'monitoring_type': 'PROCESS', 'monitoring_0': 'httpd'}
        Returns: MonitoringDetailProcess class

        params = {'monitoring_type': 'PORT', 'monitoring_0': '80'}
        Returns: None
    """
    if params is None:
        params = {}

    if params.get("monitoring_type") == "PROCESS":
        return MonitoringDetailProcess
    return None


class MonitoringDetailProcess(coshsh.monitoringdetail.MonitoringDetail):
    """Process monitoring detail.

    Represents a process to be monitored, with instance count thresholds.

    Attributes:
        monitoring_type: Always "PROCESS"
        name: Process name or pattern to match
        warning: Warning threshold (Nagios range syntax)
        critical: Critical threshold (Nagios range syntax)
        alias: Display name for the process

    Class Attributes:
        property: "processes" - property name on application/host
        property_type: list - stored as a list
        mandatory_fields: ["monitoring_0"] - required fields

    Example:
        detail = MonitoringDetailProcess({
            'monitoring_type': 'PROCESS',
            'monitoring_0': 'httpd',
            'monitoring_1': '1:10',
            'monitoring_2': '1:',
            'monitoring_3': 'Apache'
        })

        # Used in template:
        for proc in application.processes:
            print(f"Check {proc.alias}: {proc.name} count {proc.warning}/{proc.critical}")
    """

    # Property name added to application/host
    property = "processes"

    # Property type (list allows multiple processes)
    property_type = list

    # Required fields for validation
    mandatory_fields = ["monitoring_0"]

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize process monitoring detail.

        Args:
            params: Dictionary with process parameters

        CSV Format:
            monitoring_0: name (process name/pattern) - REQUIRED
            monitoring_1: warning (default: "1:1")
            monitoring_2: critical (default: "1:")
            monitoring_3: alias (default: same as name)

        Note:
            If monitoring_0 is missing, logs an error but continues.
            This allows graceful degradation for malformed input.
        """
        try:
            self.monitoring_type = params["monitoring_type"]

            # Check for mandatory field
            if "monitoring_0" not in params:
                logger.info(
                    f"mandatory parameter monitoring_0 missing "
                    f"{params.get('host_name')}:{params.get('name')}:{params.get('type')}"
                )

            # Process configuration
            self.name = params["monitoring_0"]
            self.warning = params.get("monitoring_1", "1:1")
            self.critical = params.get("monitoring_2", "1:")
            self.alias = params.get("monitoring_3", self.name)

        except Exception:
            # Silently fail on initialization errors
            # This maintains backward compatibility with malformed data
            pass

    def __str__(self) -> str:
        """Return string representation for debugging.

        Returns:
            String in format: "name warning:critical:0:100"

        Example:
            "httpd 1:10:1::0:100"

        Note:
            Format may be used by legacy templates or debugging.
            The "0:100" suffix is a legacy artifact.
        """
        return f"{self.name} {self.warning}:{self.critical}:0:100"
