"""Database Tablespace Monitoring Detail Plugin

This plugin handles database tablespace monitoring configuration.

Plugin Identification:
---------------------
Identifies monitoring details with monitoring_type = "TABLESPACE".

Purpose:
--------
Configures database tablespace monitoring including:
    - Tablespace space usage
    - Free space thresholds
    - Tablespace growth monitoring
    - Capacity planning

Supported Databases:
-------------------
- Oracle: SYSTEM, SYSAUX, USERS, TEMP, UNDO tablespaces
- PostgreSQL: pg_default, pg_global tablespaces
- DB2: SYSCATSPACE, USERSPACE1, TEMPSPACE1
- MySQL InnoDB: system tablespace, file-per-table tablespaces

Input Format:
-------------
CSV Format (monitoring_N columns):
    monitoring_type = TABLESPACE
    monitoring_0 = name (tablespace name)
    monitoring_1 = warning (default: 10)
    monitoring_2 = critical (default: 5)
    monitoring_3 = units (default: %)

Parameters:
-----------
- name: Tablespace name
    Examples:
        Oracle: SYSTEM, USERS, TEMP, UNDO, DATA
        PostgreSQL: pg_default, pg_global
        DB2: SYSCATSPACE, USERSPACE1
        MySQL: innodb_system, mysql

- warning: Warning threshold for free space
    Default: 10 (10% free space remaining)
    With units=%: Percentage of free space
    With units=GB: Gigabytes of free space

- critical: Critical threshold for free space
    Default: 5 (5% free space remaining)
    With units=%: Percentage of free space
    With units=GB: Gigabytes of free space

- units: Measurement units
    Default: % (percentage)
    Options: %, MB, GB, TB, KB

Template Usage:
---------------
The 'tablespaces' property is populated as a list on the application/host.
Templates can iterate over this list to generate individual checks.

Example template:
    {% for ts in application.tablespaces %}
    define service {
        host_name               {{ application.host_name }}
        service_description     Tablespace {{ ts.name }}
        check_command           check_tablespace!{{ ts.name }}!{{ ts.warning }}!{{ ts.critical }}
    }
    {% endfor %}

Configuration Examples:
----------------------
CSV datasource (applicationdetails.csv):
    host_name,name,type,monitoring_type,monitoring_0,monitoring_1,monitoring_2,monitoring_3
    oradb01,oracle,database,TABLESPACE,SYSTEM,10,5,%
    oradb01,oracle,database,TABLESPACE,USERS,15,10,%
    oradb01,oracle,database,TABLESPACE,DATA,20,10,%
    pgdb01,postgres,database,TABLESPACE,pg_default,10,5,%
    db2db01,db2,database,TABLESPACE,USERSPACE1,10,5,%

Explanation:
    - oradb01 SYSTEM: Oracle system tablespace, alert at 10%/5% free
    - oradb01 USERS: Oracle users tablespace, alert at 15%/10% free
    - oradb01 DATA: Oracle data tablespace, alert at 20%/10% free
    - pgdb01 pg_default: PostgreSQL default tablespace, alert at 10%/5% free
    - db2db01 USERSPACE1: DB2 user tablespace, alert at 10%/5% free

Common Tablespace Names:
-----------------------
Oracle:
    - SYSTEM (system catalog)
    - SYSAUX (auxiliary system)
    - USERS (default user data)
    - TEMP (temporary)
    - UNDO (undo segments)
    - Custom data tablespaces: DATA, INDEXES, etc.

PostgreSQL:
    - pg_default (default tablespace)
    - pg_global (shared system catalogs)
    - Custom tablespaces

DB2:
    - SYSCATSPACE (system catalog)
    - TEMPSPACE1 (temporary)
    - USERSPACE1 (default user data)

MySQL InnoDB:
    - innodb_system (system tablespace)
    - mysql (mysql system database)
    - Custom file-per-table tablespaces

Monitoring Best Practices:
--------------------------
1. System tablespaces: Monitor closely (lower thresholds)
2. Temp tablespaces: May fill temporarily, higher thresholds
3. Data tablespaces: Monitor growth trends
4. Set alerts based on growth rate and business hours

Classes:
--------
- MonitoringDetailTablespace: Database tablespace monitoring detail
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import coshsh
from coshsh.monitoringdetail import MonitoringDetail


def __detail_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify TABLESPACE monitoring details.

    Called by the plugin factory system to determine if a monitoring
    detail should be upgraded to a MonitoringDetailTablespace object.

    Args:
        params: Monitoring detail attributes dictionary

    Returns:
        MonitoringDetailTablespace class if monitoring_type="TABLESPACE"
        None if no match

    Example:
        params = {'monitoring_type': 'TABLESPACE', 'monitoring_0': 'USERS'}
        Returns: MonitoringDetailTablespace class

        params = {'monitoring_type': 'VOLUME', 'monitoring_0': 'vg0/lv_data'}
        Returns: None
    """
    if params is None:
        params = {}

    if params.get("monitoring_type") == "TABLESPACE":
        return MonitoringDetailTablespace
    return None


class MonitoringDetailTablespace(coshsh.monitoringdetail.MonitoringDetail):
    """Database tablespace monitoring detail.

    Represents a database tablespace to be monitored, with free space thresholds.

    Attributes:
        monitoring_type: Always "TABLESPACE"
        name: Tablespace name
        warning: Warning threshold (free space)
        critical: Critical threshold (free space)
        units: Measurement units (%, MB, GB, TB, KB)

    Class Attributes:
        property: "tablespaces" - property name on application/host
        property_type: list - stored as a list

    Example:
        detail = MonitoringDetailTablespace({
            'monitoring_type': 'TABLESPACE',
            'monitoring_0': 'USERS',
            'monitoring_1': '10',
            'monitoring_2': '5',
            'monitoring_3': '%'
        })

        # Used in template:
        for ts in application.tablespaces:
            print(f"Check tablespace {ts.name} at {ts.warning}/{ts.critical}{ts.units}")
    """

    # Property name added to application/host
    property = "tablespaces"

    # Property type (list allows multiple tablespaces)
    property_type = list

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize database tablespace monitoring detail.

        Args:
            params: Dictionary with tablespace parameters

        CSV Format:
            monitoring_0: name (tablespace name) - REQUIRED
            monitoring_1: warning (default: 10)
            monitoring_2: critical (default: 5)
            monitoring_3: units (default: %)

        Note:
            Thresholds represent free space. Lower values trigger alerts.
            Example: warning=10, critical=5 means alert at 10%/5% free.
        """
        self.monitoring_type = params["monitoring_type"]
        self.name = params["monitoring_0"]
        self.warning = params.get("monitoring_1", "10")
        self.critical = params.get("monitoring_2", "5")
        self.units = params.get("monitoring_3", "%")

    def __str__(self) -> str:
        """Return string representation for debugging.

        Returns:
            String in format: "name warning:critical:0:100"

        Example:
            "USERS 10:5:0:100"
            "SYSTEM 10:5:0:100"

        Note:
            Format may be used by legacy templates or debugging.
            The "0:100" represents min:max range (0-100%).
        """
        return f"{self.name} {self.warning}:{self.critical}:0:100"
