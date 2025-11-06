"""Custom Nagios Macro Detail Plugin

This plugin adds custom Nagios/Naemon macros to applications.

Plugin Identification:
---------------------
Identifies monitoring details with monitoring_type = "CUSTOMMACRO".

Purpose:
--------
Defines custom macros that can be used in Nagios/Naemon check commands
and service definitions:
    - Application-specific parameters
    - Custom thresholds
    - Connection strings
    - API keys/tokens
    - Any dynamic values needed in checks

Nagios Custom Macros:
--------------------
Custom macros in Nagios/Naemon start with underscore:
    - Host macros: $_HOSTMACRONAME$
    - Service macros: $_SERVICEMACRONAME$

These can be referenced in check commands and other configurations.

Input Format:
-------------
CSV Format (monitoring_N columns):
    monitoring_type = CUSTOMMACRO
    monitoring_0 = macro_name (without leading underscore)
    monitoring_1 = macro_value

Parameters:
-----------
- macro_name: Name of the custom macro
    Examples:
        DBNAME, APIKEY, THRESHOLD_WARN, THRESHOLD_CRIT
        PORT, USERNAME, INSTANCE

- macro_value: Value of the custom macro
    Examples:
        production_db, abc123xyz, 80, 95
        Can use @VAULT[key] for secure values

Template Usage:
---------------
The 'custom_macros' property is populated as a dictionary on the
application/host. Templates can iterate or access specific macros.

Example template:
    {% if application.custom_macros %}
    define host {
        host_name               {{ application.host_name }}
        {% for macro, value in application.custom_macros.items() %}
        _{{ macro }}            {{ value }}
        {% endfor %}
    }
    {% endif %}

    define service {
        host_name               {{ application.host_name }}
        service_description     Database Check
        check_command           check_db!$_HOSTDBNAME$!$_HOSTDBUSER$
    }

Configuration Examples:
----------------------
CSV datasource (applicationdetails.csv):
    host_name,name,type,monitoring_type,monitoring_0,monitoring_1
    db01,mysql,database,CUSTOMMACRO,DBNAME,production_db
    db01,mysql,database,CUSTOMMACRO,DBPORT,3306
    db01,mysql,database,CUSTOMMACRO,DBUSER,monitoring
    api01,rest,api,CUSTOMMACRO,APIKEY,@VAULT[API_KEY]
    api01,rest,api,CUSTOMMACRO,APIURL,https://api.example.com

Result: application.custom_macros = {
    'DBNAME': 'production_db',
    'DBPORT': '3306',
    'DBUSER': 'monitoring',
    'APIKEY': '@VAULT[API_KEY]',
    'APIURL': 'https://api.example.com'
}

Generated Nagios config:
    define host {
        host_name               db01
        _DBNAME                 production_db
        _DBPORT                 3306
        _DBUSER                 monitoring
    }

    define service {
        host_name               db01
        service_description     MySQL Check
        check_command           check_mysql!$_HOSTDBNAME$!$_HOSTDBPORT$!$_HOSTDBUSER$
    }

Common Use Cases:
----------------
Database Monitoring:
    DBNAME, DBPORT, DBUSER, DBSID (Oracle)
    INSTANCE (SQL Server), DATABASE (PostgreSQL)

API Monitoring:
    APIKEY, APIURL, APIVERSION
    APITOKEN, ENDPOINT

Application Monitoring:
    APPPORT, APPPATH, APPUSER
    JMXPORT (Java), CONTEXTROOT

Thresholds:
    THRESHOLD_WARN, THRESHOLD_CRIT
    MAX_CONNECTIONS, MAX_SESSIONS

Best Practices:
---------------
1. Use descriptive, uppercase macro names
2. Use @VAULT[key] for sensitive values
3. Document macros in templates
4. Keep macro names consistent across similar applications
5. Avoid spaces in macro names

Security Note:
--------------
Custom macro values are written to Nagios config files. For sensitive
data like passwords or API keys, always use @VAULT[key] syntax to
reference vault-stored secrets.

Classes:
--------
- MonitoringDetailCustomMacro: Custom Nagios macro definition
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import coshsh
from coshsh.monitoringdetail import MonitoringDetail


def __detail_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify CUSTOMMACRO monitoring details.

    Called by the plugin factory system to determine if a monitoring
    detail should be upgraded to a MonitoringDetailCustomMacro object.

    Args:
        params: Monitoring detail attributes dictionary

    Returns:
        MonitoringDetailCustomMacro class if monitoring_type="CUSTOMMACRO"
        None if no match

    Example:
        params = {'monitoring_type': 'CUSTOMMACRO', 'monitoring_0': 'DBNAME'}
        Returns: MonitoringDetailCustomMacro class

        params = {'monitoring_type': 'TAG', 'monitoring_0': 'production'}
        Returns: None
    """
    if params is None:
        params = {}

    if params.get("monitoring_type") == "CUSTOMMACRO":
        return MonitoringDetailCustomMacro
    return None


class MonitoringDetailCustomMacro(coshsh.monitoringdetail.MonitoringDetail):
    """Custom Nagios macro monitoring detail.

    Adds custom macros to hosts/applications for use in check commands.

    Attributes:
        monitoring_type: Always "CUSTOMMACRO"
        key: Macro name (without leading underscore)
        value: Macro value

    Class Attributes:
        property: "custom_macros" - property name on application/host
        property_type: dict - stored as dictionary

    Example:
        detail = MonitoringDetailCustomMacro({
            'monitoring_type': 'CUSTOMMACRO',
            'monitoring_0': 'DBNAME',
            'monitoring_1': 'production_db'
        })

        # Multiple macros accumulate:
        # application.custom_macros = {'DBNAME': 'production_db', 'DBPORT': '3306'}

        # Used in template:
        _{{ key }}  {{ value }}  # Generates: _DBNAME  production_db

        # Used in check command:
        check_db!$_HOSTDBNAME$!$_HOSTDBPORT$
    """

    # Property name added to application/host
    property = "custom_macros"

    # Property type (dictionary of macro name-value pairs)
    property_type = dict

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize custom macro detail.

        Args:
            params: Dictionary with macro parameters

        CSV Format:
            monitoring_0: key (macro name without _) - REQUIRED
            monitoring_1: value (macro value) - REQUIRED

        Note:
            Multiple CUSTOMMACRO entries accumulate into the
            custom_macros dictionary. Macro names should be
            uppercase by convention.
        """
        self.monitoring_type = params["monitoring_type"]
        self.key = params["monitoring_0"]
        self.value = params["monitoring_1"]

    def __str__(self) -> str:
        """Return string representation for debugging.

        Returns:
            String in format: "key: value"

        Example:
            "DBNAME: production_db"
            "APIKEY: @VAULT[API_KEY]"
            "PORT: 8080"

        Note:
            Shows the macro definition for logging/debugging.
        """
        return f"{self.key}: {self.value}"
