"""Unix Socket Monitoring Detail Plugin

This plugin handles Unix domain socket monitoring configuration.

Plugin Identification:
---------------------
Identifies monitoring details with monitoring_type = "SOCKET".

Purpose:
--------
Configures Unix socket monitoring including:
    - Socket connectivity checks
    - Socket response time monitoring
    - Application socket availability

Unix Sockets vs TCP Ports:
--------------------------
- TCP PORT: Network sockets (IP:port, e.g., localhost:3306)
- UNIX SOCKET: Local IPC sockets (file paths, e.g., /var/run/mysql.sock)

Common Use Cases:
----------------
- Database local connections (MySQL, PostgreSQL)
- Web server sockets (PHP-FPM, uWSGI)
- Application IPC (Docker daemon, Redis)
- System services (systemd sockets)

Input Format:
-------------
CSV Format (monitoring_N columns):
    monitoring_type = SOCKET
    monitoring_0 = socket (socket file path)
    monitoring_1 = warning (response time in seconds, default: 1)
    monitoring_2 = critical (response time in seconds, default: 10)

Parameters:
-----------
- socket: Unix socket file path
    Examples:
        /var/run/mysqld/mysqld.sock (MySQL)
        /var/run/postgresql/.s.PGSQL.5432 (PostgreSQL)
        /var/run/php-fpm.sock (PHP-FPM)
        /var/run/docker.sock (Docker daemon)
        /run/redis/redis.sock (Redis)

- warning: Warning threshold for response time (seconds)
    Default: 1 second
    Example: warning=2 → Warn if socket takes > 2 seconds to respond

- critical: Critical threshold for response time (seconds)
    Default: 10 seconds
    Example: critical=5 → Alert if socket takes > 5 seconds to respond

Template Usage:
---------------
The 'socket' property is set as a single object on the application/host
(not a list, since there's typically one main socket per application).

Example template:
    {% if application.socket %}
    define service {
        host_name               {{ application.host_name }}
        service_description     Socket {{ application.socket.socket }}
        check_command           check_unix_socket!{{ application.socket.socket }}
    }
    {% endif %}

Configuration Examples:
----------------------
CSV datasource (applicationdetails.csv):
    host_name,name,type,monitoring_type,monitoring_0,monitoring_1,monitoring_2
    db01,mysql,database,SOCKET,/var/run/mysqld/mysqld.sock,1,5
    db02,postgres,database,SOCKET,/var/run/postgresql/.s.PGSQL.5432,1,5
    web01,php-fpm,webserver,SOCKET,/var/run/php-fpm.sock,2,10
    app01,docker,container,SOCKET,/var/run/docker.sock,1,5

Explanation:
    - db01: MySQL socket with 1s/5s thresholds
    - db02: PostgreSQL socket with 1s/5s thresholds
    - web01: PHP-FPM socket with 2s/10s thresholds
    - app01: Docker daemon socket with 1s/5s thresholds

Common Socket Paths:
-------------------
Databases:
    /var/run/mysqld/mysqld.sock (MySQL)
    /var/lib/mysql/mysql.sock (MySQL alternative)
    /tmp/mysql.sock (MySQL macOS)
    /var/run/postgresql/.s.PGSQL.5432 (PostgreSQL)
    /tmp/.s.PGSQL.5432 (PostgreSQL alternative)

Web/Application:
    /var/run/php-fpm.sock (PHP-FPM)
    /run/uwsgi.sock (uWSGI)
    /var/run/gunicorn.sock (Gunicorn)

Services:
    /var/run/docker.sock (Docker)
    /run/redis/redis.sock (Redis)
    /var/run/memcached.sock (Memcached)

Classes:
--------
- MonitoringDetailSocket: Unix socket monitoring detail
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import coshsh
from coshsh.monitoringdetail import MonitoringDetail


def __detail_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify SOCKET monitoring details.

    Called by the plugin factory system to determine if a monitoring
    detail should be upgraded to a MonitoringDetailSocket object.

    Args:
        params: Monitoring detail attributes dictionary

    Returns:
        MonitoringDetailSocket class if monitoring_type="SOCKET"
        None if no match

    Example:
        params = {'monitoring_type': 'SOCKET', 'monitoring_0': '/var/run/mysqld/mysqld.sock'}
        Returns: MonitoringDetailSocket class

        params = {'monitoring_type': 'PORT', 'monitoring_0': '3306'}
        Returns: None
    """
    if params is None:
        params = {}

    if params.get("monitoring_type") == "SOCKET":
        return MonitoringDetailSocket
    return None


class MonitoringDetailSocket(coshsh.monitoringdetail.MonitoringDetail):
    """Unix socket monitoring detail.

    Represents a Unix domain socket to be monitored, with response
    time thresholds.

    Attributes:
        monitoring_type: Always "SOCKET"
        socket: Unix socket file path
        warning: Warning threshold for response time (seconds)
        critical: Critical threshold for response time (seconds)

    Class Attributes:
        property: "socket" - property name on application/host
        property_type: str - stored as single object (not list)

    Example:
        detail = MonitoringDetailSocket({
            'monitoring_type': 'SOCKET',
            'monitoring_0': '/var/run/mysqld/mysqld.sock',
            'monitoring_1': '1',
            'monitoring_2': '5'
        })

        # Used in template:
        if application.socket:
            print(f"Check socket {application.socket.socket}")
    """

    # Property name added to application/host
    property = "socket"

    # Property type (single object, not list)
    property_type = str

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize Unix socket monitoring detail.

        Args:
            params: Dictionary with socket parameters

        CSV Format:
            monitoring_0: socket (socket file path) - REQUIRED
            monitoring_1: warning (response time in seconds, default: 1)
            monitoring_2: critical (response time in seconds, default: 10)

        Note:
            Thresholds indicate response times in seconds. If the socket
            connection takes longer than these thresholds, an alert
            is generated.
        """
        self.monitoring_type = params["monitoring_type"]
        self.socket = params["monitoring_0"]

        # Response time thresholds (in seconds)
        # These are shown as examples - actual usage depends on check command
        self.warning = params.get("monitoring_1", "1")
        self.critical = params.get("monitoring_2", "10")

    def __str__(self) -> str:
        """Return string representation for debugging.

        Returns:
            String containing the socket path

        Example:
            "/var/run/mysqld/mysqld.sock"
            "/var/run/docker.sock"

        Note:
            Simple format for quick identification in logs.
        """
        return f"{self.socket}"
