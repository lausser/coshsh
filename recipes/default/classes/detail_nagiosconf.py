"""Nagios Service Configuration Attribute Plugin

This plugin modifies Nagios service configuration attributes.

Plugin Identification:
---------------------
Identifies monitoring details with monitoring_type = "NAGIOSCONF".

Purpose:
--------
Modifies attributes of specific Nagios services by name:
    - Change service check_interval
    - Modify servicegroups
    - Update notification_interval
    - Any service-specific attribute

Difference from NAGIOS:
----------------------
- NAGIOS: Sets general host/application attributes
- NAGIOSCONF: Modifies specific service attributes by name

Input Format:
-------------
CSV Format (monitoring_N columns):
    monitoring_type = NAGIOSCONF
    monitoring_0 = service_name
    monitoring_1 = attribute_name
    monitoring_2 = attribute_value

Parameters:
-----------
- service_name: Name of the service to modify
    Examples: HTTP, MySQL, Disk /var

- attribute_name: Attribute to modify
    Examples: check_interval, servicegroups, notification_interval

- attribute_value: New value for attribute
    Special handling for '*groups' attributes (stored as list)

Template Usage:
---------------
The 'nagios_config_attributes' property is a list of modifications.

Example:
    {% for conf in application.nagios_config_attributes %}
    # Modify service {{ conf.name }}: {{ conf.attribute }} = {{ conf.value }}
    {% endfor %}

Configuration Examples:
----------------------
CSV datasource:
    host_name,name,type,monitoring_type,monitoring_0,monitoring_1,monitoring_2
    web01,apache,webserver,NAGIOSCONF,HTTP,check_interval,5
    web01,apache,webserver,NAGIOSCONF,HTTP,servicegroups,web-services
    db01,mysql,database,NAGIOSCONF,MySQL,notification_interval,30

Classes:
--------
- MonitoringDetailNagiosConf: Service configuration modifier
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List, Union

import coshsh
from coshsh.monitoringdetail import MonitoringDetail


def __detail_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    if params is None:
        params = {}
    if params.get("monitoring_type") == "NAGIOSCONF":
        return MonitoringDetailNagiosConf
    return None


class MonitoringDetailNagiosConf(coshsh.monitoringdetail.MonitoringDetail):
    """Nagios service configuration attribute detail."""

    property = "nagios_config_attributes"
    property_type = list

    def __init__(self, params: Dict[str, Any]) -> None:
        self.monitoring_type = params["monitoring_type"]
        # Modify an attribute of service "name"
        self.name = params.get("monitoring_0", None)
        self.attribute = params.get("monitoring_1", None)
        # Special handling for *groups attributes (stored as list)
        if self.attribute and self.attribute.endswith('groups'):
            self.value: Union[str, List[str]] = [params.get("monitoring_2", None)]
        else:
            self.value = params.get("monitoring_2", None)
