"""Generic Key-Value Pairs Detail Plugin

This plugin provides flexible generic key-value storage for applications.

Plugin Identification:
---------------------
Identifies monitoring details with:
- monitoring_type = "KEYVALUES" → MonitoringDetailKeyvalues
- monitoring_type = "KEYVALUESARRAY" → MonitoringDetailKeyvaluesArray

Purpose:
--------
Provides flexible storage for custom application attributes that don't
fit into standard monitoring detail types.

Use Cases:
----------
- Custom application-specific parameters
- Dynamic attribute storage
- Configuration values for templates
- Application metadata
- Flexible extensibility without creating new plugins

KEYVALUES vs KEYVALUESARRAY:
----------------------------
KEYVALUES:
    - Stores key=value pairs
    - Each key has single value
    - Last value wins if duplicate keys

KEYVALUESARRAY:
    - Stores key=[value1, value2, ...] arrays
    - Each key can have multiple values
    - Values accumulate into lists

Input Formats:
--------------
KEYVALUES - CSV Format (monitoring_N columns):
    monitoring_type = KEYVALUES
    monitoring_0 = key1
    monitoring_1 = value1
    monitoring_2 = key2
    monitoring_3 = value2
    monitoring_4 = key3
    monitoring_5 = value3

KEYVALUESARRAY - CSV Format:
    monitoring_type = KEYVALUESARRAY
    monitoring_0 = key1
    monitoring_1 = value1
    monitoring_2 = key2
    monitoring_3 = value2
    monitoring_4 = key3
    monitoring_5 = value3

Parameters (KEYVALUES):
----------------------
Supports up to 3 key-value pairs per row:
    monitoring_0, monitoring_1 = first key-value pair
    monitoring_2, monitoring_3 = second key-value pair
    monitoring_4, monitoring_5 = third key-value pair

Parameters (KEYVALUESARRAY):
---------------------------
Supports up to 3 key-value pairs per row, accumulating values into arrays.

Template Usage:
---------------
KEYVALUES creates a dictionary: application.generic = {key: value}
KEYVALUESARRAY creates a dictionary: application.generic = {key: [values]}

Example template (KEYVALUES):
    {% if application.generic %}
    # Custom config: {{ application.generic.get('config_version', 'unknown') }}
    # Owner: {{ application.generic.get('owner', 'unassigned') }}
    {% endif %}

Example template (KEYVALUESARRAY):
    {% if application.generic and 'parents' in application.generic %}
    # Parent switches: {{ ', '.join(application.generic['parents']) }}
    {% endif %}

Configuration Examples:
----------------------
KEYVALUES example (applicationdetails.csv):
    host_name,name,type,monitoring_type,monitoring_0,monitoring_1,monitoring_2,monitoring_3
    web01,app,webserver,KEYVALUES,owner,john.doe,version,2.5
    web01,app,webserver,KEYVALUES,environment,production,criticality,high

Result: application.generic = {
    'owner': 'john.doe',
    'version': '2.5',
    'environment': 'production',
    'criticality': 'high'
}

KEYVALUESARRAY example (applicationdetails.csv):
    host_name,name,type,monitoring_type,monitoring_0,monitoring_1,monitoring_2,monitoring_3
    web01,app,webserver,KEYVALUESARRAY,role,frontend,parents,sw1
    web01,app,webserver,KEYVALUESARRAY,role,api,parents,sw2

Result: application.generic = {
    'role': ['frontend', 'api'],
    'parents': ['sw1', 'sw2']
}

Common Use Cases:
----------------
KEYVALUES:
    - Application owner/contact
    - Version numbers
    - Configuration identifiers
    - Business metadata
    - Custom thresholds

KEYVALUESARRAY:
    - Parent devices (switches, routers)
    - Multiple roles
    - Team memberships
    - Multiple contacts
    - Tag-like categorization with values

Best Practices:
---------------
1. Use standard detail types when available
2. Reserve KEYVALUES for truly custom/dynamic data
3. Document custom keys in templates
4. Use consistent naming conventions
5. Consider creating dedicated plugin for frequently-used patterns

Classes:
--------
- MonitoringDetailKeyvalues: Generic key-value pairs (single values)
- MonitoringDetailKeyvaluesArray: Generic key-value arrays (multiple values)
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List

import coshsh
from coshsh.monitoringdetail import MonitoringDetail


def __detail_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify KEYVALUES/KEYVALUESARRAY monitoring details.

    Called by the plugin factory system to determine which class to use.

    Args:
        params: Monitoring detail attributes dictionary

    Returns:
        MonitoringDetailKeyvaluesArray if monitoring_type="KEYVALUESARRAY"
        MonitoringDetailKeyvalues if monitoring_type="KEYVALUES"
        None if no match

    Example:
        params = {'monitoring_type': 'KEYVALUES', 'monitoring_0': 'owner'}
        Returns: MonitoringDetailKeyvalues class

        params = {'monitoring_type': 'KEYVALUESARRAY', 'monitoring_0': 'role'}
        Returns: MonitoringDetailKeyvaluesArray class
    """
    if params is None:
        params = {}

    if params.get("monitoring_type") == "KEYVALUESARRAY":
        return MonitoringDetailKeyvaluesArray
    elif params.get("monitoring_type") == "KEYVALUES":
        return MonitoringDetailKeyvalues
    return None


class MonitoringDetailKeyvalues(coshsh.monitoringdetail.MonitoringDetail):
    """Generic key-value pairs monitoring detail.

    Stores up to 3 key-value pairs per CSV row in a dictionary.
    Last value wins if duplicate keys appear.

    Attributes:
        monitoring_type: Always "KEYVALUES"
        dictionary: Dict[str, str] containing key-value pairs

    Class Attributes:
        property: "generic" - property name on application/host
        property_type: dict - stored as dictionary

    Example:
        detail = MonitoringDetailKeyvalues({
            'monitoring_type': 'KEYVALUES',
            'monitoring_0': 'owner',
            'monitoring_1': 'john.doe',
            'monitoring_2': 'version',
            'monitoring_3': '2.5'
        })

        # Result: application.generic = {'owner': 'john.doe', 'version': '2.5'}

        # Used in template:
        owner = application.generic.get('owner', 'unknown')
        version = application.generic.get('version', '1.0')
    """

    # Property name added to application/host
    property = "generic"

    # Property type (dictionary of key-value pairs)
    property_type = dict

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize generic key-value detail.

        Extracts up to 3 key-value pairs from monitoring_0 through
        monitoring_5.

        Args:
            params: Dictionary with keyvalue parameters

        CSV Format:
            monitoring_0, monitoring_1: First key-value pair
            monitoring_2, monitoring_3: Second key-value pair
            monitoring_4, monitoring_5: Third key-value pair

        Note:
            Missing or invalid pairs are silently skipped using
            try-except blocks for backward compatibility.
        """
        self.monitoring_type = params["monitoring_type"]
        self.dictionary: Dict[str, str] = {}

        # First key-value pair
        try:
            self.dictionary[params["monitoring_0"]] = params["monitoring_1"]
        except Exception:
            pass

        # Second key-value pair
        try:
            self.dictionary[params["monitoring_2"]] = params["monitoring_3"]
        except Exception:
            pass

        # Third key-value pair
        try:
            self.dictionary[params["monitoring_4"]] = params["monitoring_5"]
        except Exception:
            pass


class MonitoringDetailKeyvaluesArray(coshsh.monitoringdetail.MonitoringDetail):
    """Generic key-value array monitoring detail.

    Stores up to 3 key-value pairs per CSV row, accumulating values
    into arrays/lists.

    Attributes:
        monitoring_type: Always "KEYVALUESARRAY"
        dictionary: Dict[str, List[str]] containing key-array pairs

    Class Attributes:
        property: "generic" - property name on application/host
        property_type: list - stored as list (though actually dict of lists)

    Example CSV data:
        KEYVALUESARRAY, role, frontend, parents, sw1
        KEYVALUESARRAY, role, api, parents, sw2
        KEYVALUESARRAY, role, backend, team, alpha

    Result:
        application.generic = {
            'role': ['frontend', 'api', 'backend'],
            'parents': ['sw1', 'sw2'],
            'team': ['alpha']
        }

    Template usage:
        {% for role in application.generic.get('role', []) %}
        # Role: {{ role }}
        {% endfor %}

        {% if 'parents' in application.generic %}
        # Parent switches: {{ ', '.join(application.generic['parents']) }}
        {% endif %}
    """

    # Property name added to application/host
    property = "generic"

    # Property type (list, though contains dict of lists)
    property_type = list

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize generic key-value array detail.

        Extracts up to 3 key-value pairs from monitoring_0 through
        monitoring_5, appending values to arrays.

        Args:
            params: Dictionary with keyvalue array parameters

        CSV Format:
            monitoring_0, monitoring_1: First key-value to append
            monitoring_2, monitoring_3: Second key-value to append
            monitoring_4, monitoring_5: Third key-value to append

        Note:
            Values are appended to arrays. If key doesn't exist,
            a new array is created. Missing pairs are silently
            skipped for backward compatibility.
        """
        self.monitoring_type = params["monitoring_type"]
        self.dictionary: Dict[str, List[str]] = {}

        # First key-value pair
        try:
            self.dictionary[params["monitoring_0"]].append(params["monitoring_1"])
        except Exception:
            # Key doesn't exist yet, create new array
            self.dictionary[params["monitoring_0"]] = [params["monitoring_1"]]

        # Second key-value pair
        try:
            self.dictionary[params["monitoring_2"]].append(params["monitoring_3"])
        except Exception:
            try:
                # Key doesn't exist yet, create new array
                self.dictionary[params["monitoring_2"]] = [params["monitoring_3"]]
            except Exception:
                # Missing parameters, skip
                pass

        # Third key-value pair
        try:
            self.dictionary[params["monitoring_4"]].append(params["monitoring_5"])
        except Exception:
            try:
                # Key doesn't exist yet, create new array
                self.dictionary[params["monitoring_4"]] = [params["monitoring_5"]]
            except Exception:
                # Missing parameters, skip
                pass
