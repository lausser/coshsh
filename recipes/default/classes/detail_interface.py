"""Network Interface Monitoring Detail Plugin

This plugin handles network interface monitoring configuration.

Plugin Identification:
---------------------
Identifies monitoring details with monitoring_type = "INTERFACE".

Purpose:
--------
Configures network interface monitoring including:
    - Network interface status (up/down)
    - Traffic monitoring (bandwidth utilization)
    - Error/discard counters
    - Interface availability

Typical Use Cases:
-----------------
- Server network interfaces (eth0, eth1, ens3, etc.)
- Switch/router interfaces (GigabitEthernet0/1, etc.)
- Virtual interfaces (bond0, vlan100, etc.)
- Wireless interfaces (wlan0, etc.)

Input Format:
-------------
CSV Format (monitoring_N columns):
    monitoring_type = INTERFACE
    monitoring_0 = name (interface name)

Parameters:
-----------
- name: Network interface name
    Examples:
        Linux: eth0, eth1, ens3, ens4, bond0, br0
        Windows: "Intel(R) PRO/1000", "Local Area Connection"
        Network devices: GigabitEthernet0/1, FastEthernet1/0/1
        Virtual: vlan100, tun0, docker0

Template Usage:
---------------
The 'interfaces' property is populated as a list on the application/host.
Templates can iterate over this list to generate individual checks.

Example template:
    {% for iface in application.interfaces %}
    define service {
        host_name               {{ application.host_name }}
        service_description     Interface {{ iface.name }}
        check_command           check_interface!{{ iface.name }}
    }
    {% endfor %}

Configuration Examples:
----------------------
CSV datasource (applicationdetails.csv):
    host_name,name,type,monitoring_type,monitoring_0
    server01,os,linux,INTERFACE,eth0
    server01,os,linux,INTERFACE,eth1
    server02,os,linux,INTERFACE,bond0
    switch01,os,network,INTERFACE,GigabitEthernet0/1
    switch01,os,network,INTERFACE,GigabitEthernet0/2

Explanation:
    - server01: Monitor eth0 and eth1 network interfaces
    - server02: Monitor bonded interface bond0
    - switch01: Monitor switch ports GigabitEthernet0/1 and 0/2

Common Interface Names:
----------------------
Linux:
    - eth0, eth1, ... (legacy naming)
    - ens3, ens4, ... (systemd predictable names)
    - enp0s3, enp0s8, ... (PCI-based naming)
    - bond0, bond1, ... (bonded interfaces)
    - br0, br1, ... (bridge interfaces)
    - vlan100, vlan200, ... (VLAN interfaces)
    - docker0 (Docker bridge)
    - wlan0, wlan1 (wireless)

Windows:
    - "Local Area Connection"
    - "Ethernet"
    - "Wi-Fi"
    - "Intel(R) PRO/1000 MT Network Connection"

Network Devices (Cisco, etc.):
    - GigabitEthernet0/1, GigabitEthernet1/0/1
    - FastEthernet0/1
    - TenGigabitEthernet1/1
    - Port-channel1 (EtherChannel)

Monitoring Checks:
-----------------
Typical interface checks include:
    - Status: Is interface up/down?
    - Traffic: Bandwidth utilization (in/out)
    - Errors: Error counters
    - Discards: Packet discard counters
    - Duplex: Half/full duplex
    - Speed: Interface speed

Classes:
--------
- MonitoringDetailInterface: Network interface monitoring detail
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import coshsh
from coshsh.monitoringdetail import MonitoringDetail


def __detail_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify INTERFACE monitoring details.

    Called by the plugin factory system to determine if a monitoring
    detail should be upgraded to a MonitoringDetailInterface object.

    Args:
        params: Monitoring detail attributes dictionary

    Returns:
        MonitoringDetailInterface class if monitoring_type="INTERFACE"
        None if no match

    Example:
        params = {'monitoring_type': 'INTERFACE', 'monitoring_0': 'eth0'}
        Returns: MonitoringDetailInterface class

        params = {'monitoring_type': 'PORT', 'monitoring_0': '80'}
        Returns: None
    """
    if params is None:
        params = {}

    if params.get("monitoring_type") == "INTERFACE":
        return MonitoringDetailInterface
    return None


class MonitoringDetailInterface(coshsh.monitoringdetail.MonitoringDetail):
    """Network interface monitoring detail.

    Represents a network interface to be monitored.

    Attributes:
        monitoring_type: Always "INTERFACE"
        name: Network interface name (e.g., eth0, GigabitEthernet0/1)

    Class Attributes:
        property: "interfaces" - property name on application/host
        property_type: list - stored as a list

    Example:
        detail = MonitoringDetailInterface({
            'monitoring_type': 'INTERFACE',
            'monitoring_0': 'eth0'
        })

        # Used in template:
        for iface in application.interfaces:
            print(f"Check interface {iface.name}")
    """

    # Property name added to application/host
    property = "interfaces"

    # Property type (list allows multiple interfaces)
    property_type = list

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize network interface monitoring detail.

        Args:
            params: Dictionary with interface parameters

        CSV Format:
            monitoring_0: name (interface name, optional)

        Note:
            Interface name is optional. If not provided, templates
            may monitor all interfaces or use default interface.
        """
        self.monitoring_type = params["monitoring_type"]
        self.name = params.get("monitoring_0", None)
