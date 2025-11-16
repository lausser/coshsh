r"""Filesystem Monitoring Detail Plugin

This plugin handles filesystem/disk space monitoring configuration.

Plugin Identification:
---------------------
Identifies monitoring details with monitoring_type = "FILESYSTEM".

Purpose:
--------
Configures filesystem monitoring including:
    - Disk space usage monitoring
    - Warning/critical thresholds
    - Percentage or absolute size units
    - Optional filesystem handling
    - Inode usage monitoring (Linux)

Input Formats:
--------------
Two input formats are supported:

1. CSV Format (monitoring_N columns):
    monitoring_type = FILESYSTEM
    monitoring_0 = path (e.g., /var, C:\, /home)
    monitoring_1 = warning (default: 10)
    monitoring_2 = critical (default: 5)
    monitoring_3 = units (default: %)
    monitoring_4 = optional (default: 0 = required)
    monitoring_5 = iwarning (default: 0 = disabled)
    monitoring_6 = icritical (default: 0 = disabled)

2. Named Format (direct attributes):
    monitoring_type = FILESYSTEM
    path = /var
    warning = 10
    critical = 5
    units = %
    optional = 0

Parameters:
-----------
- path: Filesystem mount point or drive letter
    Examples: /var, /home, C:\, D:\Data

- warning/critical: Thresholds for alerting
    With units=%: Remaining free space percentage (10 = alert at 10% free)
    With units=MB/GB: Remaining free space in absolute size
    Examples:
        warning=10, critical=5, units=% → Alert at 10%/5% free
        warning=1000, critical=500, units=MB → Alert at 1GB/500MB free

- units: Measurement unit (default: %)
    Values: %, MB, GB, TB, KB
    Example: units=GB for gigabytes

- optional: Whether filesystem is optional (default: 0)
    Values: 0 (required, alert if missing), 1 (optional, skip if missing)
    Use for dynamically mounted filesystems or removable drives

- iwarning/icritical: Inode usage thresholds (Linux only)
    Percentage thresholds for inode usage
    Example: iwarning=10, icritical=5 → Alert at 10%/5% inodes free

Template Usage:
---------------
The 'filesystems' property is populated as a list on the application/host.
Templates can iterate over this list to generate individual checks.

Example template (os_linux_fs.tpl):
    {% for fs in application.filesystems %}
    define service {
        host_name               {{ application.host_name }}
        service_description     Disk {{ fs.path }}
        check_command           check_disk!{{ fs.warning }}!{{ fs.critical }}!{{ fs.path }}
        {% if fs.optional %}
        # Optional filesystem - no alert if unmounted
        {% endif %}
    }
    {% endfor %}

Configuration Examples:
----------------------
CSV datasource (applicationdetails.csv):
    host_name,name,type,monitoring_type,monitoring_0,monitoring_1,monitoring_2,monitoring_3,monitoring_4
    server01,os,linux,FILESYSTEM,/var,10,5,%,0
    server01,os,linux,FILESYSTEM,/home,15,10,%,0
    server01,os,linux,FILESYSTEM,/backup,20,10,%,1
    winserver,os,windows,FILESYSTEM,C:\,10,5,%,0
    winserver,os,windows,FILESYSTEM,D:\,1000,500,GB,0

Explanation:
    - server01 /var: Alert at 10%/5% free (required)
    - server01 /home: Alert at 15%/10% free (required)
    - server01 /backup: Alert at 20%/10% free (optional - skip if unmounted)
    - winserver C:\: Alert at 10%/5% free (required)
    - winserver D:\: Alert at 1000GB/500GB free (required)

Classes:
--------
- MonitoringDetailFilesystem: Filesystem monitoring detail
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import coshsh
from coshsh.monitoringdetail import MonitoringDetail


def __detail_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify FILESYSTEM monitoring details.

    Called by the plugin factory system to determine if a monitoring
    detail should be upgraded to a MonitoringDetailFilesystem object.

    Args:
        params: Monitoring detail attributes dictionary

    Returns:
        MonitoringDetailFilesystem class if monitoring_type="FILESYSTEM"
        None if no match

    Example:
        params = {'monitoring_type': 'FILESYSTEM', 'monitoring_0': '/var'}
        Returns: MonitoringDetailFilesystem class

        params = {'monitoring_type': 'PROCESS', 'monitoring_0': 'httpd'}
        Returns: None
    """
    if params is None:
        params = {}

    if params.get("monitoring_type") == "FILESYSTEM":
        return MonitoringDetailFilesystem
    return None


class MonitoringDetailFilesystem(coshsh.monitoringdetail.MonitoringDetail):
    r"""Filesystem monitoring detail.

    Represents a filesystem to be monitored, with thresholds and options.

    Attributes:
        monitoring_type: Always "FILESYSTEM"
        path: Filesystem mount point or drive letter (e.g., /var, C:\)
        warning: Warning threshold (free space)
        critical: Critical threshold (free space)
        units: Measurement units (%, MB, GB, TB, KB)
        optional: Whether filesystem is optional (True/False)
        iwarning: Inode warning threshold (Linux only)
        icritical: Inode critical threshold (Linux only)

    Class Attributes:
        property: "filesystems" - property name on application/host
        property_type: list - stored as a list
        unique_attribute: "path" - each path should be unique

    Example:
        detail = MonitoringDetailFilesystem({
            'monitoring_type': 'FILESYSTEM',
            'path': '/var',
            'warning': '10',
            'critical': '5',
            'units': '%',
            'optional': '0'
        })

        # Used in template:
        for fs in application.filesystems:
            print(f"Check {fs.path} at {fs.warning}/{fs.critical}{fs.units}")
    """

    # Property name added to application/host
    property = "filesystems"

    # Property type (list allows multiple filesystems)
    property_type = list

    # Unique identifier attribute (each path should be unique)
    unique_attribute = "path"

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize filesystem monitoring detail.

        Supports two input formats:
        1. CSV format with monitoring_0..monitoring_6
        2. Named format with direct attributes

        Args:
            params: Dictionary with filesystem parameters

        CSV Format:
            monitoring_0: path
            monitoring_1: warning (default: 10)
            monitoring_2: critical (default: 5)
            monitoring_3: units (default: %)
            monitoring_4: optional (default: 0)
            monitoring_5: iwarning (default: 0)
            monitoring_6: icritical (default: 0)

        Named Format:
            path: Filesystem path
            warning: Warning threshold (default: 10)
            critical: Critical threshold (default: 5)
            units: Measurement units (default: %)
            optional: Optional filesystem (default: 0)
        """
        self.monitoring_type = params["monitoring_type"]

        if "monitoring_0" in params:
            # CSV format with monitoring_N columns
            self.path = params["monitoring_0"]
            self.warning = str(params.get("monitoring_1", "10"))
            self.critical = str(params.get("monitoring_2", "5"))
            self.units = params.get("monitoring_3", "%")
            self.optional = bool(params.get("monitoring_4", "0"))
            self.iwarning = str(params.get("monitoring_5", "0"))
            self.icritical = str(params.get("monitoring_6", "0"))
        else:
            # Named format with direct attributes
            self.path = params["path"]
            self.warning = str(params.get("warning", "10"))
            self.critical = str(params.get("critical", "5"))
            self.units = params.get("units", "%")
            self.optional = bool(params.get("optional", "0"))
            # Named format doesn't support inode thresholds yet
            self.iwarning = "0"
            self.icritical = "0"

        # Ensure units has a value (default to %)
        if not self.units:
            self.units = "%"

    def __str__(self) -> str:
        """Return string representation for debugging.

        Returns:
            String in format: "path warning:critical:0:100"

        Example:
            "/var 10:5:0:100"

        Note:
            Format may be used by legacy templates or debugging.
            The "0:100" represents min:max range (0-100%).
        """
        return f"{self.path} {self.warning}:{self.critical}:0:100"
