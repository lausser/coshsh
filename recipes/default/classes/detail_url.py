"""URL Monitoring Detail Plugin

This plugin handles HTTP/HTTPS URL monitoring configuration.

Plugin Identification:
---------------------
Identifies monitoring details with monitoring_type = "URL".

Purpose:
--------
Configures web URL monitoring including:
    - HTTP/HTTPS endpoint checking
    - Response time thresholds
    - Content verification (expected strings)
    - URL component extraction

Input Format:
-------------
CSV Format (monitoring_N columns):
    monitoring_type = URL
    monitoring_0 = url (full URL, e.g., https://example.com/api/health)
    monitoring_1 = warning (response time in seconds, default: 5)
    monitoring_2 = critical (response time in seconds, default: 10)
    monitoring_3 = url_expect (optional expected content string)

Parameters:
-----------
- url: Full URL to monitor
    Examples:
        http://example.com → Simple HTTP check
        https://example.com/api/health → HTTPS API endpoint
        https://example.com:8443/status → Custom port
        http://user:pass@example.com/admin → With authentication

- warning: Warning threshold for response time (seconds)
    Default: 5 seconds
    Example: warning=2 → Warn if response takes > 2 seconds

- critical: Critical threshold for response time (seconds)
    Default: 10 seconds
    Example: critical=5 → Alert if response takes > 5 seconds

- url_expect: Expected content in response (optional)
    String that should appear in the response body
    Example: url_expect="OK" → Response must contain "OK"

URL Parsing:
------------
The URL is automatically parsed into components for template use:
    - scheme: Protocol (http, https)
    - hostname: Server hostname
    - port: Port number (or None for default)
    - path: URL path
    - query: Query string
    - fragment: URL fragment (#section)
    - username: HTTP auth username (if present)
    - password: HTTP auth password (if present)
    - netloc: Network location (hostname:port)

Template Usage:
---------------
The 'urls' property is populated as a list on the application/host.
Templates can iterate over this list to generate individual checks.

Example template:
    {% for url in application.urls %}
    define service {
        host_name               {{ application.host_name }}
        service_description     URL {{ url.path or '/' }}
        check_command           check_http!{{ url.hostname }}!{{ url.path }}!{{ url.warning }}!{{ url.critical }}
        {% if url.url_expect %}
        # Expecting: "{{ url.url_expect }}"
        {% endif %}
    }
    {% endfor %}

Configuration Examples:
----------------------
CSV datasource (applicationdetails.csv):
    host_name,name,type,monitoring_type,monitoring_0,monitoring_1,monitoring_2,monitoring_3
    web01,apache,webserver,URL,https://web01.example.com/,2,5,
    web01,apache,webserver,URL,https://web01.example.com/api/health,3,10,OK
    api01,nodejs,api,URL,https://api.example.com/status,5,15,healthy
    app01,tomcat,appserver,URL,http://app01:8080/manager/status,10,30,

Explanation:
    - web01 homepage: Check homepage with 2s/5s thresholds
    - web01 API health: Check /api/health, expect "OK", 3s/10s thresholds
    - api01 status: Check status endpoint, expect "healthy", 5s/15s thresholds
    - app01 manager: Check Tomcat manager on port 8080, 10s/30s thresholds

URL Components Example:
-----------------------
For URL: https://user:pass@example.com:8443/api/v1/status?debug=1#results

Parsed components:
    scheme: "https"
    hostname: "example.com"
    port: 8443
    path: "/api/v1/status"
    query: "debug=1"
    fragment: "results"
    username: "user"
    password: "pass"
    netloc: "example.com:8443"
    url: "https://user:pass@example.com:8443/api/v1/status?debug=1#results"

Classes:
--------
- MonitoringDetailUrl: URL monitoring detail
"""

from __future__ import annotations

from urllib.parse import urlparse
from typing import Optional, Dict, Any

import coshsh
from coshsh.monitoringdetail import MonitoringDetail


def __detail_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify URL monitoring details.

    Called by the plugin factory system to determine if a monitoring
    detail should be upgraded to a MonitoringDetailUrl object.

    Args:
        params: Monitoring detail attributes dictionary

    Returns:
        MonitoringDetailUrl class if monitoring_type="URL"
        None if no match

    Example:
        params = {'monitoring_type': 'URL', 'monitoring_0': 'https://example.com'}
        Returns: MonitoringDetailUrl class

        params = {'monitoring_type': 'PORT', 'monitoring_0': '80'}
        Returns: None
    """
    if params is None:
        params = {}

    if params.get("monitoring_type") == "URL":
        return MonitoringDetailUrl
    return None


class MonitoringDetailUrl(coshsh.monitoringdetail.MonitoringDetail):
    """URL monitoring detail.

    Represents a web URL to be monitored, with response time thresholds
    and optional content verification.

    The URL is automatically parsed into components for easy access in
    templates (scheme, hostname, port, path, query, etc.).

    Attributes:
        monitoring_type: Always "URL"
        url: Full URL to monitor
        warning: Warning threshold for response time (seconds)
        critical: Critical threshold for response time (seconds)
        url_expect: Expected content string (optional)
        scheme: URL scheme (http, https)
        hostname: Server hostname
        port: Port number (or None)
        path: URL path
        query: Query string
        fragment: URL fragment
        username: HTTP auth username (if present)
        password: HTTP auth password (if present)
        netloc: Network location (hostname:port)
        params: URL parameters

    Class Attributes:
        property: "urls" - property name on application/host
        property_type: list - stored as a list

    Example:
        detail = MonitoringDetailUrl({
            'monitoring_type': 'URL',
            'monitoring_0': 'https://example.com/api/health',
            'monitoring_1': '5',
            'monitoring_2': '10',
            'monitoring_3': 'OK'
        })

        # Parsed components available:
        print(detail.hostname)  # "example.com"
        print(detail.path)      # "/api/health"
        print(detail.url_expect)  # "OK"

        # Used in template:
        for url in application.urls:
            print(f"Check {url.hostname}{url.path} expecting '{url.url_expect}'")
    """

    # Property name added to application/host
    property = "urls"

    # Property type (list allows multiple URLs)
    property_type = list

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize URL monitoring detail.

        Parses the URL into components for easy template access.

        Args:
            params: Dictionary with URL parameters

        CSV Format:
            monitoring_0: url (full URL) - REQUIRED
            monitoring_1: warning (response time in seconds, default: 5)
            monitoring_2: critical (response time in seconds, default: 10)
            monitoring_3: url_expect (expected content, optional)

        Note:
            The URL is parsed using urllib.parse.urlparse to extract
            all components (scheme, hostname, port, path, etc.).
            This makes templates more flexible.
        """
        self.monitoring_type = params["monitoring_type"]
        self.url = params.get("monitoring_0", None)

        # Response time thresholds (in seconds)
        # Using 'or' to handle empty strings as None
        self.warning = params.get("monitoring_1", "5") or "5"
        self.critical = params.get("monitoring_2", "10") or "10"

        # Optional expected content
        self.url_expect = params.get("monitoring_3", None)

        # Parse URL into components
        # Split scheme first to handle non-standard schemes
        scheme, rest = self.url.split(":", 1)

        # Parse the rest using urlparse (prepend http: for correct parsing)
        o = urlparse("http:" + rest)

        # Extract all URL components
        for attr in ["scheme", "netloc", "path", "params", "query", "fragment",
                     "username", "password", "hostname", "port"]:
            setattr(self, attr, getattr(o, attr))

        # Override scheme with the actual scheme from URL
        setattr(self, "scheme", scheme)

    def __str__(self) -> str:
        """Return string representation for debugging.

        Returns:
            String in format: "url warning:critical"

        Example:
            "https://example.com/api/health 5:10"

        Note:
            Includes thresholds for debugging and log identification.
        """
        return f"{self.url} {self.warning}:{self.critical}"
