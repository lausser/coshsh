"""SNMP v1/v2c Login Credentials Monitoring Detail Plugin

This plugin handles SNMP v1 and v2c community-based authentication for monitoring.

Plugin Identification:
---------------------
Identifies monitoring details with monitoring_type = "LOGINSNMPV2".

Purpose:
--------
Stores SNMP community strings and protocol versions for monitoring
network devices and systems that support SNMP v1/v2c:
    - Network switches and routers
    - Servers with SNMP agents
    - Storage devices
    - UPS systems
    - Printers and other SNMP-enabled hardware

SNMP Protocol Versions:
-----------------------
- SNMPv1: Original protocol (1988), simple community-based auth
- SNMPv2c: Updated protocol (1996), community-based auth with improvements
- SNMPv3: Modern protocol with user-based security (see detail_loginsnmpv3.py)

This plugin handles v1 and v2c only. For v3, use LOGINSNMPV3 type.

Security Warning:
----------------
SNMP community strings are transmitted in plain text and provide no
encryption. For production use:
    - Use read-only communities when possible
    - Consider using SNMPv3 with encryption (authPriv)
    - Restrict SNMP access by IP/network ACLs
    - Use non-default community strings
    - Consider vault integration: @VAULT[snmp_community]

Input Format:
-------------
CSV Format (monitoring_N columns):
    monitoring_type = LOGINSNMPV2
    monitoring_0 = community string (with optional version prefix)

Parameters:
-----------
- community: SNMP community string with optional version prefix
    Format: [v1:|v2:]community_string

    Examples:
        "public" → Uses SNMPv2c with community "public"
        "v2:public" → Explicitly uses SNMPv2c with community "public"
        "v1:public" → Uses SNMPv1 with community "public"
        "@VAULT[SNMP_COMMUNITY]" → Community from vault (v2c)
        "v1:@VAULT[SNMP_COMMUNITY]" → Community from vault (v1)

    Default: "public" (if not specified or empty)
    Special: "_none_" (used when empty to indicate no community)

Version Prefix:
    - "v1:" → Forces SNMPv1 protocol
    - "v2:" → Forces SNMPv2c protocol
    - No prefix → Defaults to SNMPv2c

Typical Community Strings:
    - "public" (read-only, common default - CHANGE IN PRODUCTION!)
    - "private" (read-write, common default - CHANGE IN PRODUCTION!)
    - Custom strings (e.g., "monitoring", "ro_community")

Template Usage:
---------------
The 'loginsnmpv2' property is set as a single object on the application/host
(not a list, since there's typically one SNMP community per device).

Example template:
    {% if application.loginsnmpv2 %}
    define service {
        host_name               {{ application.host_name }}
        service_description     SNMP Interface Check
        check_command           check_snmp_interface!{{ application.loginsnmpv2.community }}!{{ application.loginsnmpv2.protocol }}
    }
    {% endif %}

Configuration Examples:
----------------------
CSV datasource (applicationdetails.csv):
    host_name,name,type,monitoring_type,monitoring_0
    switch01,os,network,LOGINSNMPV2,public
    switch02,os,network,LOGINSNMPV2,v2:monitoring_ro
    router01,os,network,LOGINSNMPV2,v1:legacy_community
    server01,os,linux,LOGINSNMPV2,@VAULT[SNMP_COMMUNITY]

Explanation:
    - switch01: SNMPv2c with community "public" (default protocol)
    - switch02: SNMPv2c with community "monitoring_ro" (explicit v2)
    - router01: SNMPv1 with community "legacy_community" (forced v1)
    - server01: SNMPv2c with community from vault

Best Practices:
---------------
1. Never use default "public"/"private" in production
2. Use read-only communities for monitoring
3. Use @VAULT[key] for community strings
4. Restrict SNMP access with firewall/ACLs
5. Consider migrating to SNMPv3 for better security
6. Use SNMPv2c unless legacy v1 devices require it

SNMPv1 vs SNMPv2c:
------------------
Use SNMPv2c (default) unless you have legacy devices that only support v1:
    - v2c: Improved error handling, 64-bit counters, bulk operations
    - v1: Legacy protocol, 32-bit counters only

Force v1 only for:
    - Very old network devices
    - Devices with broken v2c implementations
    - Specific vendor requirements

Example with Vault:
------------------
Vault file (encrypted):
    SNMP_RO_COMMUNITY=SecureReadOnlyCommunity123
    SNMP_RW_COMMUNITY=SecureReadWriteCommunity456

CSV file:
    host_name,name,type,monitoring_type,monitoring_0
    switch01,os,network,LOGINSNMPV2,@VAULT[SNMP_RO_COMMUNITY]

Generated config (community substituted):
    check_command check_snmp!SecureReadOnlyCommunity123!2

Classes:
--------
- MonitoringDetailLoginSNMPV2: SNMP v1/v2c login credentials detail
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import coshsh
from coshsh.monitoringdetail import MonitoringDetail


def __detail_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify LOGINSNMPV2 monitoring details.

    Called by the plugin factory system to determine if a monitoring
    detail should be upgraded to a MonitoringDetailLoginSNMPV2 object.

    Args:
        params: Monitoring detail attributes dictionary

    Returns:
        MonitoringDetailLoginSNMPV2 class if monitoring_type="LOGINSNMPV2"
        None if no match

    Example:
        params = {'monitoring_type': 'LOGINSNMPV2', 'monitoring_0': 'public'}
        Returns: MonitoringDetailLoginSNMPV2 class

        params = {'monitoring_type': 'LOGIN', 'monitoring_0': 'user'}
        Returns: None
    """
    if params is None:
        params = {}

    if params.get("monitoring_type") == "LOGINSNMPV2":
        return MonitoringDetailLoginSNMPV2
    return None


class MonitoringDetailLoginSNMPV2(coshsh.monitoringdetail.MonitoringDetail):
    """SNMP v1/v2c community-based login credentials.

    Stores SNMP community strings and protocol version for monitoring
    checks that use SNMP v1 or v2c.

    Attributes:
        monitoring_type: Always "LOGINSNMPV2"
        community: SNMP community string (without version prefix)
        protocol: SNMP protocol version (1 or 2)

    Class Attributes:
        property: "loginsnmpv2" - property name on application/host
        property_type: str - stored as single object (not list)

    Community String Processing:
        Input "public" → community="public", protocol=2
        Input "v2:monitoring" → community="monitoring", protocol=2
        Input "v1:legacy" → community="legacy", protocol=1
        Input "" or None → community="_none_", protocol=2

    Security Note:
        SNMP v1/v2c community strings are sent in plain text.
        Use @VAULT[key] syntax for secure storage and consider
        migrating to SNMPv3 for encrypted authentication.

    Example:
        detail = MonitoringDetailLoginSNMPV2({
            'monitoring_type': 'LOGINSNMPV2',
            'monitoring_0': 'v2:monitoring_ro'
        })
        # detail.community = "monitoring_ro"
        # detail.protocol = 2

        # Used in template:
        if application.loginsnmpv2:
            cmd = f"check_snmp -C {application.loginsnmpv2.community} -P {application.loginsnmpv2.protocol}"
    """

    # Property name added to application/host
    property = "loginsnmpv2"

    # Property type (single object, not list)
    property_type = str

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize SNMP v1/v2c login credentials detail.

        Parses the community string and extracts the SNMP protocol version
        if a version prefix (v1: or v2:) is present.

        Args:
            params: Dictionary with SNMP parameters

        CSV Format:
            monitoring_0: community string with optional version prefix

        Version Prefix Handling:
            - "v1:community" → protocol=1, community="community"
            - "v2:community" → protocol=2, community="community"
            - "community" → protocol=2, community="community" (default v2)

        Default Values:
            - Empty/None community → "_none_" (placeholder)
            - No version prefix → SNMPv2c (protocol=2)

        Note:
            The community string is required for SNMP authentication.
            Use @VAULT[key] syntax for secure credential storage.
        """
        self.monitoring_type = params["monitoring_type"]

        # Get community string, default to "public", handle empty as "_none_"
        self.community = params.get("monitoring_0", "public") or "_none_"

        # Parse version prefix and extract actual community string
        if self.community.startswith("v1:"):
            self.protocol = 1
            self.community = self.community.split(":", 1)[1]
        elif self.community.startswith("v2:"):
            self.protocol = 2
            self.community = self.community.split(":", 1)[1]
        else:
            # Default to SNMPv2c if no version prefix
            self.protocol = 2

    def __str__(self) -> str:
        """Return string representation for debugging.

        Returns:
            String containing SNMP version and community

        Example:
            "SNMP v2/1 community: public"
            "SNMP v2/1 community: monitoring_ro"

        Note:
            Shows "v2/1" to indicate this plugin handles both versions,
            with the actual version stored in self.protocol attribute.
        """
        return f"SNMP v2/1 community: {self.community}"
