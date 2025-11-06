"""Login Credentials Monitoring Detail Plugin

This plugin handles authentication credentials for monitoring checks.

Plugin Identification:
---------------------
Identifies monitoring details with monitoring_type = "LOGIN".

Purpose:
--------
Stores authentication credentials for monitoring applications that
require login:
    - Database monitoring (username/password)
    - Application monitoring with authentication
    - API monitoring with credentials
    - Any service requiring authentication

Security Warning:
----------------
Credentials are stored in plain text in the generated monitoring
configuration. For production use, consider:
    - Using vault integration: @VAULT[password_key]
    - Restricting file permissions on generated configs
    - Using key-based authentication where possible
    - Rotating credentials regularly

Input Format:
-------------
CSV Format (monitoring_N columns):
    monitoring_type = LOGIN
    monitoring_0 = username
    monitoring_1 = password

Parameters:
-----------
- username: Authentication username
    Examples: nagios, monitoring, admin, dbuser

- password: Authentication password
    Examples: password123, @VAULT[DB_PASSWORD]
    Recommendation: Use @VAULT[key] for secure storage

Template Usage:
---------------
The 'login' property is set as a single object on the application/host
(not a list, since there's typically one login per application).

Example template:
    {% if application.login %}
    define service {
        host_name               {{ application.host_name }}
        service_description     Database Status
        check_command           check_mysql!{{ application.login.username }}!{{ application.login.password }}
    }
    {% endif %}

Configuration Examples:
----------------------
CSV datasource (applicationdetails.csv):
    host_name,name,type,monitoring_type,monitoring_0,monitoring_1
    db01,mysql,database,LOGIN,nagios,@VAULT[MYSQL_PASSWORD]
    db02,postgres,database,LOGIN,monitoring,@VAULT[POSTGRES_PASSWORD]
    app01,tomcat,appserver,LOGIN,admin,@VAULT[TOMCAT_PASSWORD]

Explanation:
    - db01: MySQL monitoring with username 'nagios', password from vault
    - db02: PostgreSQL with username 'monitoring', password from vault
    - app01: Tomcat with username 'admin', password from vault

Best Practices:
---------------
1. Always use @VAULT[key] for passwords in production
2. Never commit plain text passwords to version control
3. Use dedicated monitoring accounts with minimal privileges
4. Rotate credentials regularly
5. Audit credential usage in monitoring configs

Example with Vault:
------------------
Vault file (encrypted):
    MYSQL_PASSWORD=SuperSecret123
    POSTGRES_PASSWORD=PgSecret456

CSV file:
    host_name,name,type,monitoring_type,monitoring_0,monitoring_1
    db01,mysql,database,LOGIN,nagios,@VAULT[MYSQL_PASSWORD]

Generated config (password substituted):
    check_command check_mysql!nagios!SuperSecret123

Classes:
--------
- MonitoringDetailLogin: Login credentials detail
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import coshsh
from coshsh.monitoringdetail import MonitoringDetail


def __detail_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify LOGIN monitoring details.

    Called by the plugin factory system to determine if a monitoring
    detail should be upgraded to a MonitoringDetailLogin object.

    Args:
        params: Monitoring detail attributes dictionary

    Returns:
        MonitoringDetailLogin class if monitoring_type="LOGIN"
        None if no match

    Example:
        params = {'monitoring_type': 'LOGIN', 'monitoring_0': 'nagios'}
        Returns: MonitoringDetailLogin class

        params = {'monitoring_type': 'PORT', 'monitoring_0': '3306'}
        Returns: None
    """
    if params is None:
        params = {}

    if params.get("monitoring_type") == "LOGIN":
        return MonitoringDetailLogin
    return None


class MonitoringDetailLogin(coshsh.monitoringdetail.MonitoringDetail):
    """Login credentials monitoring detail.

    Stores authentication credentials for monitoring checks.

    Attributes:
        monitoring_type: Always "LOGIN"
        username: Authentication username
        password: Authentication password (plain text or @VAULT reference)

    Class Attributes:
        property: "login" - property name on application/host
        property_type: str - stored as single object (not list)

    Security Note:
        Passwords are stored in plain text unless using @VAULT[key]
        syntax. Always use vault integration for production.

    Example:
        detail = MonitoringDetailLogin({
            'monitoring_type': 'LOGIN',
            'monitoring_0': 'nagios',
            'monitoring_1': '@VAULT[MYSQL_PASSWORD]'
        })

        # Used in template:
        if application.login:
            cmd = f"check_mysql -u {application.login.username} -p {application.login.password}"
    """

    # Property name added to application/host
    property = "login"

    # Property type (single object, not list)
    property_type = str

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize login credentials detail.

        Args:
            params: Dictionary with login parameters

        CSV Format:
            monitoring_0: username - REQUIRED
            monitoring_1: password - REQUIRED

        Note:
            Both username and password are required fields.
            Use @VAULT[key] syntax for secure password storage.
        """
        self.monitoring_type = params["monitoring_type"]
        self.username = params["monitoring_0"]
        self.password = params["monitoring_1"]
