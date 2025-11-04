"""Port Monitoring Detail Plugin

This plugin handles TCP/UDP port monitoring configuration.

Plugin Identification:
---------------------
Identifies monitoring details with monitoring_type = "PORT".

Purpose:
--------
Configures network port monitoring including:
    - Port number to check
    - Response time thresholds
    - Port connectivity verification

Input Format:
-------------
CSV Format (monitoring_N columns):
    monitoring_type = PORT
    monitoring_0 = port (port number, e.g., 80, 443, 3306)
    monitoring_1 = warning (response time in seconds, default: 1)
    monitoring_2 = critical (response time in seconds, default: 10)

Parameters:
-----------
- port: Port number to monitor
    Examples:
        80 → HTTP
        443 → HTTPS
        22 → SSH
        3306 → MySQL
        5432 → PostgreSQL
        8080 → Alternative HTTP

- warning: Warning threshold for response time (seconds)
    Default: 1 second
    Example: warning=2 → Warn if port takes > 2 seconds to respond

- critical: Critical threshold for response time (seconds)
    Default: 10 seconds
    Example: critical=5 → Alert if port takes > 5 seconds to respond

Template Usage:
---------------
The 'ports' property is populated as a list on the application/host.
Templates can iterate over this list to generate individual checks.

Example template:
    {% for port in application.ports %}
    define service {
        host_name               {{ application.host_name }}
        service_description     Port {{ port.port }}
        check_command           check_tcp!{{ port.port }}!{{ port.warning }}!{{ port.critical }}
    }
    {% endfor %}

Configuration Examples:
----------------------
CSV datasource (applicationdetails.csv):
    host_name,name,type,monitoring_type,monitoring_0,monitoring_1,monitoring_2
    webserver01,apache,webserver,PORT,80,1,5
    webserver01,apache,webserver,PORT,443,1,5
    dbserver01,mysql,database,PORT,3306,2,10
    appserver01,tomcat,appserver,PORT,8080,1,5

Explanation:
    - webserver01: Monitor HTTP (80) and HTTPS (443) with 1s/5s thresholds
    - dbserver01: Monitor MySQL (3306) with 2s/10s thresholds
    - appserver01: Monitor Tomcat (8080) with 1s/5s thresholds

Common Ports:
-------------
Web Services:
    80 - HTTP
    443 - HTTPS
    8080, 8443 - Alternative HTTP/HTTPS

Databases:
    3306 - MySQL/MariaDB
    5432 - PostgreSQL
    1521 - Oracle
    1433 - MS SQL Server
    27017 - MongoDB
    6379 - Redis

Application Servers:
    8080 - Tomcat
    9000 - PHP-FPM
    3000 - Node.js (common default)

System Services:
    22 - SSH
    25 - SMTP
    110 - POP3
    143 - IMAP
    389 - LDAP

Classes:
--------
- MonitoringDetailPort: Port monitoring detail
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import coshsh
from coshsh.monitoringdetail import MonitoringDetail


def __detail_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify PORT monitoring details.

    Called by the plugin factory system to determine if a monitoring
    detail should be upgraded to a MonitoringDetailPort object.

    Args:
        params: Monitoring detail attributes dictionary

    Returns:
        MonitoringDetailPort class if monitoring_type="PORT"
        None if no match

    Example:
        params = {'monitoring_type': 'PORT', 'monitoring_0': '80'}
        Returns: MonitoringDetailPort class

        params = {'monitoring_type': 'PROCESS', 'monitoring_0': 'httpd'}
        Returns: None
    """
    if params is None:
        params = {}

    if params.get("monitoring_type") == "PORT":
        return MonitoringDetailPort
    return None


class MonitoringDetailPort(coshsh.monitoringdetail.MonitoringDetail):
    """Port monitoring detail.

    Represents a TCP/UDP port to be monitored, with response time thresholds.

    Attributes:
        monitoring_type: Always "PORT"
        port: Port number to monitor
        warning: Warning threshold for response time (seconds)
        critical: Critical threshold for response time (seconds)

    Class Attributes:
        property: "ports" - property name on application/host
        property_type: list - stored as a list

    Example:
        detail = MonitoringDetailPort({
            'monitoring_type': 'PORT',
            'monitoring_0': '443',
            'monitoring_1': '1',
            'monitoring_2': '5'
        })

        # Used in template:
        for port in application.ports:
            print(f"Check port {port.port} with thresholds {port.warning}s/{port.critical}s")
    """

    # Property name added to application/host
    property = "ports"

    # Property type (list allows multiple ports)
    property_type = list

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize port monitoring detail.

        Args:
            params: Dictionary with port parameters

        CSV Format:
            monitoring_0: port (port number) - REQUIRED
            monitoring_1: warning (response time in seconds, default: 1)
            monitoring_2: critical (response time in seconds, default: 10)

        Note:
            Thresholds indicate response times in seconds. If the port
            connection takes longer than these thresholds, an alert
            is generated.
        """
        self.monitoring_type = params["monitoring_type"]
        self.port = params["monitoring_0"]

        # Response time thresholds (in seconds)
        # These are shown as examples - actual usage depends on check command
        self.warning = params.get("monitoring_1", "1")
        self.critical = params.get("monitoring_2", "10")

    def __str__(self) -> str:
        """Return string representation for debugging.

        Returns:
            String containing just the port number

        Example:
            "80"
            "443"
            "3306"

        Note:
            Simple format for quick identification in logs.
        """
        return f"{self.port}"
