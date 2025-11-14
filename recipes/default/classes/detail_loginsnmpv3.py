"""SNMPv3 Login Credentials Monitoring Detail Plugin

This plugin handles SNMPv3 authentication credentials for monitoring checks.

Plugin Identification:
---------------------
Identifies monitoring details with monitoring_type = "LOGINSNMPV3".

Purpose:
--------
Stores SNMPv3 authentication credentials for monitoring network devices
and systems that support SNMPv3:
    - Network switches and routers
    - Servers with SNMP agents
    - Storage devices
    - UPS systems
    - Environmental sensors
    - Any SNMPv3-enabled device

SNMPv3 provides enhanced security over SNMPv1/v2 with:
    - User-based authentication (authprotocol + authkey)
    - Privacy/encryption (privprotocol + privkey)
    - Context-based access control

Security Levels:
---------------
SNMPv3 supports three security levels (automatically determined):

1. noAuthNoPriv: No authentication, no privacy
   - Only securityname required
   - Not recommended for production

2. authNoPriv: Authentication without privacy
   - Requires: securityname, authprotocol, authkey
   - Data is authenticated but not encrypted

3. authPriv: Authentication with privacy
   - Requires: securityname, authprotocol, authkey, privprotocol, privkey
   - Data is authenticated AND encrypted (recommended)

Input Format:
-------------
CSV Format (monitoring_N columns):
    monitoring_type = LOGINSNMPV3
    monitoring_0 = securityname (SNMPv3 username)
    monitoring_1 = authprotocol (MD5 or SHA)
    monitoring_2 = authkey (authentication password)
    monitoring_3 = privprotocol (DES or AES)
    monitoring_4 = privkey (privacy/encryption password)
    monitoring_5 = context (SNMP context, optional)

Parameters:
-----------
- securityname: SNMPv3 username/security name
    Examples: nagiosuser, monitoring, snmpv3user
    Required for all security levels

- authprotocol: Authentication protocol
    Options: MD5, SHA (SHA preferred for better security)
    Required for authNoPriv and authPriv
    Omit for noAuthNoPriv

- authkey: Authentication password/passphrase
    Examples: authpass123, @VAULT[SNMP_AUTH_KEY]
    Required for authNoPriv and authPriv
    Recommendation: Use @VAULT[key] for secure storage
    Must be at least 8 characters

- privprotocol: Privacy/encryption protocol
    Options: DES, AES (AES preferred for better security)
    Required for authPriv only
    Omit for noAuthNoPriv and authNoPriv

- privkey: Privacy/encryption password/passphrase
    Examples: privpass456, @VAULT[SNMP_PRIV_KEY]
    Required for authPriv only
    Recommendation: Use @VAULT[key] for secure storage
    Must be at least 8 characters

- context: SNMPv3 context name (optional)
    Examples: "", "vlan100", "router-context"
    Used for context-based access control
    Can be empty string or omitted

Template Usage:
---------------
The 'loginsnmpv3' property is set as a single object on the application/host
(not a list, since there's typically one SNMPv3 login per device).

Example template:
    {% if application.loginsnmpv3 %}
    define service {
        host_name               {{ application.host_name }}
        service_description     SNMP Interface Status
        check_command           check_snmpv3!{{ application.loginsnmpv3.securityname }}!{{ application.loginsnmpv3.securitylevel }}!{{ application.loginsnmpv3.authprotocol }}!{{ application.loginsnmpv3.authkey }}!{{ application.loginsnmpv3.privprotocol }}!{{ application.loginsnmpv3.privkey }}
    }
    {% endif %}

Configuration Examples:
----------------------
CSV datasource (applicationdetails.csv):

Example 1 - authPriv (full security, recommended):
    host_name,name,type,monitoring_type,monitoring_0,monitoring_1,monitoring_2,monitoring_3,monitoring_4,monitoring_5
    switch01,snmp,network,LOGINSNMPV3,nagiosuser,SHA,@VAULT[SNMP_AUTH],AES,@VAULT[SNMP_PRIV],

Example 2 - authNoPriv (authentication only):
    host_name,name,type,monitoring_type,monitoring_0,monitoring_1,monitoring_2,monitoring_3,monitoring_4,monitoring_5
    router01,snmp,network,LOGINSNMPV3,monitoring,MD5,@VAULT[SNMP_AUTH],,,,

Example 3 - noAuthNoPriv (no security, not recommended):
    host_name,name,type,monitoring_type,monitoring_0,monitoring_1,monitoring_2,monitoring_3,monitoring_4,monitoring_5
    testdevice,snmp,test,LOGINSNMPV3,testuser,,,,,

Explanation:
    - switch01: Full SNMPv3 with SHA auth and AES encryption (authPriv)
    - router01: SNMPv3 with MD5 auth but no encryption (authNoPriv)
    - testdevice: SNMPv3 with only username, no security (noAuthNoPriv)

Security Best Practices:
-----------------------
1. Always use authPriv (both auth and priv) in production
2. Prefer SHA over MD5 for authentication
3. Prefer AES over DES for privacy/encryption
4. Always use @VAULT[key] for passwords in production
5. Never commit plain text passwords to version control
6. Use strong passphrases (minimum 8 characters, longer is better)
7. Use dedicated monitoring accounts with minimal SNMP privileges
8. Rotate credentials regularly
9. Restrict SNMP access with firewall rules
10. Monitor SNMP access logs for unauthorized attempts

Common Authentication Protocols:
-------------------------------
- MD5: Message Digest 5 (legacy, less secure)
- SHA: Secure Hash Algorithm (preferred)
- SHA-224, SHA-256, SHA-384, SHA-512 (on newer devices)

Common Privacy Protocols:
------------------------
- DES: Data Encryption Standard (legacy, 56-bit, less secure)
- AES: Advanced Encryption Standard (preferred, 128-bit or higher)
- AES-192, AES-256 (on newer devices)

Example with Vault:
------------------
Vault file (encrypted):
    SWITCH_SNMP_AUTH=MyAuthPass12345
    SWITCH_SNMP_PRIV=MyPrivPass67890

CSV file:
    host_name,name,type,monitoring_type,monitoring_0,monitoring_1,monitoring_2,monitoring_3,monitoring_4
    switch01,snmp,network,LOGINSNMPV3,nagiosuser,SHA,@VAULT[SWITCH_SNMP_AUTH],AES,@VAULT[SWITCH_SNMP_PRIV]

Generated config (passwords substituted):
    check_command check_snmpv3!nagiosuser!authPriv!SHA!MyAuthPass12345!AES!MyPrivPass67890

Classes:
--------
- MonitoringDetailLoginSNMPV3: SNMPv3 credentials detail
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import coshsh
from coshsh.monitoringdetail import MonitoringDetail


def __detail_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify LOGINSNMPV3 monitoring details.

    Called by the plugin factory system to determine if a monitoring
    detail should be upgraded to a MonitoringDetailLoginSNMPV3 object.

    Args:
        params: Monitoring detail attributes dictionary

    Returns:
        MonitoringDetailLoginSNMPV3 class if monitoring_type="LOGINSNMPV3"
        None if no match

    Example:
        params = {'monitoring_type': 'LOGINSNMPV3', 'monitoring_0': 'nagiosuser'}
        Returns: MonitoringDetailLoginSNMPV3 class

        params = {'monitoring_type': 'LOGIN', 'monitoring_0': 'admin'}
        Returns: None
    """
    if params is None:
        params = {}

    if params.get("monitoring_type") == "LOGINSNMPV3":
        return MonitoringDetailLoginSNMPV3
    return None


class MonitoringDetailLoginSNMPV3(coshsh.monitoringdetail.MonitoringDetail):
    """SNMPv3 authentication credentials monitoring detail.

    Stores SNMPv3 credentials for monitoring network devices and systems.
    Automatically determines security level based on provided credentials.

    Attributes:
        monitoring_type: Always "LOGINSNMPV3"
        securityname: SNMPv3 username/security name
        authprotocol: Authentication protocol (MD5, SHA, etc.)
        authkey: Authentication password/passphrase
        privprotocol: Privacy/encryption protocol (DES, AES, etc.)
        privkey: Privacy/encryption password/passphrase
        context: SNMPv3 context name (optional)
        securitylevel: Auto-determined security level (noAuthNoPriv, authNoPriv, authPriv)

    Class Attributes:
        property: "loginsnmpv3" - property name on application/host
        property_type: str - stored as single object (not list)

    Security Levels (auto-determined):
        noAuthNoPriv: No authkey, no privkey (not recommended)
        authNoPriv: Has authkey, no privkey
        authPriv: Has both authkey and privkey (recommended)

    Security Warning:
        Credentials are stored in plain text in the generated monitoring
        configuration unless using @VAULT[key] syntax. For production use:
            - Always use @VAULT[key] for passwords
            - Restrict file permissions on generated configs
            - Use authPriv security level
            - Prefer SHA and AES over MD5 and DES

    Example:
        detail = MonitoringDetailLoginSNMPV3({
            'monitoring_type': 'LOGINSNMPV3',
            'monitoring_0': 'nagiosuser',
            'monitoring_1': 'SHA',
            'monitoring_2': '@VAULT[SNMP_AUTH]',
            'monitoring_3': 'AES',
            'monitoring_4': '@VAULT[SNMP_PRIV]',
            'monitoring_5': ''
        })
        # detail.securitylevel will be 'authPriv'

        # Used in template:
        if application.loginsnmpv3:
            cmd = f"check_snmpv3 -u {application.loginsnmpv3.securityname} -l {application.loginsnmpv3.securitylevel}"
    """

    # Property name added to application/host
    property = "loginsnmpv3"

    # Property type (single object, not list)
    property_type = str

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize SNMPv3 credentials detail.

        Args:
            params: Dictionary with SNMPv3 parameters

        CSV Format:
            monitoring_0: securityname - REQUIRED (SNMPv3 username)
            monitoring_1: authprotocol - OPTIONAL (MD5, SHA, etc.)
            monitoring_2: authkey - OPTIONAL (authentication password)
            monitoring_3: privprotocol - OPTIONAL (DES, AES, etc.)
            monitoring_4: privkey - OPTIONAL (privacy/encryption password)
            monitoring_5: context - OPTIONAL (SNMP context)

        Security Level Determination:
            If authkey and privkey both present: authPriv
            If authkey present but not privkey: authNoPriv
            If neither authkey nor privkey: noAuthNoPriv

        Note:
            - securityname is required
            - For authPriv: provide authprotocol, authkey, privprotocol, privkey
            - For authNoPriv: provide authprotocol, authkey only
            - For noAuthNoPriv: provide only securityname
            - context is optional for all security levels
        """
        self.monitoring_type = params["monitoring_type"]
        self.securityname = params.get("monitoring_0", None)
        self.authprotocol = params.get("monitoring_1", None)
        self.authkey = params.get("monitoring_2", None)
        self.privprotocol = params.get("monitoring_3", None)
        self.privkey = params.get("monitoring_4", None)
        self.context = params.get("monitoring_5", None)

        # Determine security level based on credentials
        # noAuthNoPriv|authNoPriv|authPriv
        if not self.authkey and not self.privkey:
            self.securitylevel = "noAuthNoPriv"
        elif self.authkey and not self.privkey:
            self.securitylevel = "authNoPriv"
        elif self.authkey and self.privkey:
            self.securitylevel = "authPriv"

