"""Role Assignment Detail Plugin

This plugin assigns functional roles to applications.

Plugin Identification:
---------------------
Identifies monitoring details with monitoring_type = "ROLE".

Purpose:
--------
Assigns a functional role describing the application's purpose:
    - Server roles (webserver, database, cache, loadbalancer)
    - Application roles (backend, frontend, api, worker)
    - Infrastructure roles (monitoring, logging, backup)

Difference from TAG:
-------------------
- ROLE: Primary functional purpose (typically one per application)
- TAG: Multiple categorization labels (many tags possible)

Example:
    role = "database"  (what it IS)
    tags = ["production", "critical", "team-alpha"]  (how it's categorized)

Use Cases:
----------
- Role-based template selection
- Generate role-specific checks
- Documentation and inventory
- Access control and permissions

Input Format:
-------------
CSV Format (monitoring_N columns):
    monitoring_type = ROLE
    monitoring_0 = role_name

Parameters:
-----------
- role_name: Functional role of the application
    Examples:
        webserver, database, cache, queue
        loadbalancer, firewall, proxy
        application, api, backend, frontend
        monitoring, logging, backup

Template Usage:
---------------
The 'role' property is set as a string value on the application/host.
Templates use this to generate role-specific configurations.

Example template:
    {% if application.role == 'database' %}
    define service {
        host_name               {{ application.host_name }}
        service_description     Database Connections
        check_command           check_db_connections
    }
    define service {
        host_name               {{ application.host_name }}
        service_description     Database Replication
        check_command           check_db_replication
    }
    {% elif application.role == 'webserver' %}
    define service {
        host_name               {{ application.host_name }}
        service_description     HTTP Response Time
        check_command           check_http_time
    }
    define service {
        host_name               {{ application.host_name }}
        service_description     Apache Status
        check_command           check_apache_status
    }
    {% endif %}

Configuration Examples:
----------------------
CSV datasource (applicationdetails.csv):
    host_name,name,type,monitoring_type,monitoring_0
    web01,apache,webserver,ROLE,webserver
    db01,mysql,database,ROLE,database
    cache01,redis,cache,ROLE,cache
    lb01,haproxy,loadbalancer,ROLE,loadbalancer
    app01,api,application,ROLE,api

Explanation:
    - web01: Role is webserver
    - db01: Role is database
    - cache01: Role is cache
    - lb01: Role is loadbalancer
    - app01: Role is api

Common Roles:
-------------
Server Roles:
    webserver, database, cache, queue
    loadbalancer, proxy, firewall
    dns, dhcp, ntp, smtp

Application Roles:
    api, backend, frontend, worker
    scheduler, processor, collector
    gateway, aggregator

Infrastructure Roles:
    monitoring, logging, metrics
    backup, storage, archive
    build, ci-cd, deployment

Best Practices:
---------------
1. Use standardized role names across organization
2. Keep roles focused and specific
3. One primary role per application
4. Use tags for additional categorization
5. Document role definitions and responsibilities

Classes:
--------
- MonitoringDetailRole: Role assignment detail
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import coshsh
from coshsh.monitoringdetail import MonitoringDetail


def __detail_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify ROLE monitoring details.

    Called by the plugin factory system to determine if a monitoring
    detail should be upgraded to a MonitoringDetailRole object.

    Args:
        params: Monitoring detail attributes dictionary

    Returns:
        MonitoringDetailRole class if monitoring_type="ROLE"
        None if no match

    Example:
        params = {'monitoring_type': 'ROLE', 'monitoring_0': 'webserver'}
        Returns: MonitoringDetailRole class

        params = {'monitoring_type': 'TAG', 'monitoring_0': 'production'}
        Returns: None
    """
    if params is None:
        params = {}

    if params.get("monitoring_type") == "ROLE":
        return MonitoringDetailRole
    return None


class MonitoringDetailRole(coshsh.monitoringdetail.MonitoringDetail):
    """Role assignment monitoring detail.

    Assigns a functional role describing the application's purpose.

    Attributes:
        monitoring_type: Always "ROLE"
        role: Role name (string)

    Class Attributes:
        property: "role" - property name on application/host
        property_type: str - stored as string value
        property_flat: True - value stored directly (not nested object)

    Example:
        detail = MonitoringDetailRole({
            'monitoring_type': 'ROLE',
            'monitoring_0': 'database'
        })

        # Used in template:
        if application.role == 'database':
            # Database-specific monitoring
            pass
    """

    # Property name added to application/host
    property = "role"

    # Property type (string value)
    property_type = str

    # Flat property (role value stored directly, not as object)
    property_flat = True

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize role detail.

        Args:
            params: Dictionary with role parameters

        CSV Format:
            monitoring_0: role (role name) - REQUIRED

        Note:
            Typically only one ROLE per application. If multiple
            ROLE entries exist, the last one wins.
        """
        self.monitoring_type = params["monitoring_type"]
        self.role = params["monitoring_0"]

    def __str__(self) -> str:
        """Return string representation for debugging.

        Returns:
            String containing the role name

        Example:
            "webserver"
            "database"
            "cache"

        Note:
            Returns the role for logging/debugging.
        """
        return f"{self.role}"
