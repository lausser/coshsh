"""Generic Nagios Attribute Detail Plugin

This plugin allows setting arbitrary Nagios object attributes.

Plugin Identification:
---------------------
Identifies monitoring details with monitoring_type = "NAGIOS".

Purpose:
--------
Provides flexible way to set any Nagios/Naemon attribute on hosts/services:
    - max_check_attempts
    - check_interval
    - retry_interval
    - notification_options
    - Any Nagios directive

Use Cases:
----------
- Override default check intervals
- Set custom notification options
- Configure check attempts
- Any Nagios attribute not covered by other plugins

Input Format:
-------------
CSV Format (monitoring_N columns):
    monitoring_type = NAGIOS
    monitoring_0 = attribute_name
    monitoring_1 = attribute_value

Parameters:
-----------
- attribute_name: Nagios attribute name
    Examples: max_check_attempts, check_interval, retry_interval

- attribute_value: Attribute value
    Examples: 5, 10, 1, w,u,c,r

Template Usage:
---------------
The 'generic' property stores attribute-value pairs.

Example:
    {% if application.generic %}
    # Nagios attributes set via NAGIOS monitoring detail
    {% endif %}

Configuration Examples:
----------------------
CSV datasource:
    host_name,name,type,monitoring_type,monitoring_0,monitoring_1
    web01,apache,webserver,NAGIOS,max_check_attempts,5
    web01,apache,webserver,NAGIOS,check_interval,1

Classes:
--------
- MonitoringDetailNagios: Generic Nagios attribute
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import coshsh
from coshsh.monitoringdetail import MonitoringDetail


def __detail_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    if params is None:
        params = {}
    if params.get("monitoring_type") == "NAGIOS":
        return MonitoringDetailNagios
    return None


class MonitoringDetailNagios(coshsh.monitoringdetail.MonitoringDetail):
    """Generic Nagios attribute monitoring detail."""

    property = "generic"
    property_type = str

    def __init__(self, params: Dict[str, Any]) -> None:
        self.monitoring_type = params["monitoring_type"]
        self.attribute = params.get("monitoring_0", None)
        self.value = params.get("monitoring_1", None)
