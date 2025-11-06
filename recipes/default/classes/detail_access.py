"""Access Method Detail Plugin

This plugin specifies the access method for monitoring an application.

Plugin Identification:
---------------------
Identifies monitoring details with monitoring_type = "ACCESS".

Purpose:
--------
Defines how the monitoring system should access/check the application:
    - ssh: Remote SSH-based checks
    - snmp: SNMP protocol checks
    - agent: Local agent-based checks
    - http/https: Web-based checks
    - tcp: Direct TCP connection checks

Use Cases:
----------
- Template selection based on access method
- Different check commands per access type
- Protocol-specific monitoring configuration
- Access method documentation

Input Format:
-------------
CSV Format (monitoring_N columns):
    monitoring_type = ACCESS
    monitoring_0 = access_method

Parameters:
-----------
- access_method: How to access the application
    Examples:
        ssh - SSH remote checks (Linux/Unix)
        snmp - SNMP protocol (network devices, servers)
        agent - Local monitoring agent (NSClient++, NRPE)
        http/https - Web-based checks
        tcp - Direct TCP port checks
        icmp - Ping/ICMP checks
        wmi - Windows WMI checks

Template Usage:
---------------
The 'access' property is set as a string value on the application/host.
Templates use this to generate appropriate check commands.

Example template:
    {% if application.access == 'ssh' %}
    define service {
        host_name               {{ application.host_name }}
        service_description     CPU Usage
        check_command           check_by_ssh!{{ application.host_name }}!check_cpu
    }
    {% elif application.access == 'snmp' %}
    define service {
        host_name               {{ application.host_name }}
        service_description     CPU Usage
        check_command           check_snmp_cpu!{{ application.host_name }}
    }
    {% elif application.access == 'agent' %}
    define service {
        host_name               {{ application.host_name }}
        service_description     CPU Usage
        check_command           check_nrpe!{{ application.host_name }}!check_cpu
    }
    {% endif %}

Configuration Examples:
----------------------
CSV datasource (applicationdetails.csv):
    host_name,name,type,monitoring_type,monitoring_0
    linux01,os,linux,ACCESS,ssh
    switch01,os,network,ACCESS,snmp
    win01,os,windows,ACCESS,agent
    web01,apache,webserver,ACCESS,http

Explanation:
    - linux01: Use SSH for remote checks
    - switch01: Use SNMP for network device monitoring
    - win01: Use agent (NSClient++) for Windows monitoring
    - web01: Use HTTP for web application checks

Common Access Methods:
---------------------
Linux/Unix Systems:
    ssh - SSH-based remote execution
    snmp - SNMP monitoring
    agent - NRPE agent

Windows Systems:
    agent - NSClient++ agent
    wmi - Windows WMI
    snmp - SNMP (if enabled)

Network Devices:
    snmp - Primary method for switches, routers, firewalls
    ssh - CLI-based checks (some devices)

Web Applications:
    http/https - Web-based health checks
    tcp - Port connectivity checks

Classes:
--------
- MonitoringDetailAccess: Access method specification
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import coshsh
from coshsh.monitoringdetail import MonitoringDetail


def __detail_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify ACCESS monitoring details.

    Called by the plugin factory system to determine if a monitoring
    detail should be upgraded to a MonitoringDetailAccess object.

    Args:
        params: Monitoring detail attributes dictionary

    Returns:
        MonitoringDetailAccess class if monitoring_type="ACCESS"
        None if no match

    Example:
        params = {'monitoring_type': 'ACCESS', 'monitoring_0': 'ssh'}
        Returns: MonitoringDetailAccess class

        params = {'monitoring_type': 'TAG', 'monitoring_0': 'production'}
        Returns: None
    """
    if params is None:
        params = {}

    if params.get("monitoring_type") == "ACCESS":
        return MonitoringDetailAccess
    return None


class MonitoringDetailAccess(coshsh.monitoringdetail.MonitoringDetail):
    """Access method monitoring detail.

    Specifies how the monitoring system should access/check the application.

    Attributes:
        monitoring_type: Always "ACCESS"
        access: Access method (ssh, snmp, agent, http, etc.)

    Class Attributes:
        property: "access" - property name on application/host
        property_type: str - stored as string value
        property_flat: True - value stored directly (not nested object)

    Example:
        detail = MonitoringDetailAccess({
            'monitoring_type': 'ACCESS',
            'monitoring_0': 'ssh'
        })

        # Used in template:
        if application.access == 'ssh':
            # Use SSH-based checks
            pass
    """

    # Property name added to application/host
    property = "access"

    # Property type (string value)
    property_type = str

    # Flat property (access value stored directly, not as object)
    property_flat = True

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize access method detail.

        Args:
            params: Dictionary with access parameters

        CSV Format:
            monitoring_0: access (access method) - REQUIRED

        Note:
            Typically only one ACCESS per application. Common values:
            ssh, snmp, agent, http, https, tcp, icmp, wmi
        """
        self.monitoring_type = params["monitoring_type"]
        self.access = params["monitoring_0"]

    def __str__(self) -> str:
        """Return string representation for debugging.

        Returns:
            String containing the access method

        Example:
            "ssh"
            "snmp"
            "agent"

        Note:
            Returns the access method for logging/debugging.
        """
        return f"{self.access}"
