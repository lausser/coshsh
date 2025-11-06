"""Tag Categorization Detail Plugin

This plugin adds tags/labels to applications for categorization and filtering.

Plugin Identification:
---------------------
Identifies monitoring details with monitoring_type = "TAG".

Purpose:
--------
Provides flexible tagging/labeling for applications:
    - Environment tags (production, staging, development)
    - Business unit tags (sales, marketing, engineering)
    - Technology tags (java, python, nodejs)
    - Compliance tags (pci-dss, hipaa, sox)
    - Custom categorization

Use Cases:
----------
- Filter hosts by tag in monitoring UI
- Conditional template generation based on tags
- Group/categorize services
- Apply different monitoring policies per tag
- Reporting and analytics

Input Format:
-------------
CSV Format (monitoring_N columns):
    monitoring_type = TAG
    monitoring_0 = tag_value

Parameters:
-----------
- tag_value: Tag/label to apply to the application
    Examples:
        production, staging, development
        critical, important, low-priority
        database, webserver, cache
        pci-compliant, hipaa-compliant
        team-alpha, team-beta

Template Usage:
---------------
The 'tags' property is populated as a list of tag strings on the
application/host. Templates can check for specific tags or iterate.

Example template:
    {% if 'production' in application.tags %}
    define service {
        host_name               {{ application.host_name }}
        service_description     Production Health Check
        check_interval          1
        notification_interval   5
    }
    {% elif 'development' in application.tags %}
    define service {
        host_name               {{ application.host_name }}
        service_description     Dev Health Check
        check_interval          5
        notification_interval   30
    }
    {% endif %}

    {% for tag in application.tags %}
    # Tag: {{ tag }}
    {% endfor %}

Configuration Examples:
----------------------
CSV datasource (applicationdetails.csv):
    host_name,name,type,monitoring_type,monitoring_0
    web01,app,webserver,TAG,production
    web01,app,webserver,TAG,critical
    web01,app,webserver,TAG,pci-compliant
    web02,app,webserver,TAG,staging
    web02,app,webserver,TAG,development
    db01,mysql,database,TAG,production
    db01,mysql,database,TAG,critical
    db01,mysql,database,TAG,team-alpha

Explanation:
    - web01: Tagged with production, critical, pci-compliant
    - web02: Tagged with staging, development
    - db01: Tagged with production, critical, team-alpha

Common Tag Categories:
---------------------
Environment:
    production, staging, development, test, qa

Priority:
    critical, important, normal, low-priority

Compliance:
    pci-dss, hipaa, sox, gdpr, iso27001

Technology Stack:
    java, python, nodejs, ruby, php
    mysql, postgres, mongodb, redis
    apache, nginx, tomcat

Business Unit:
    sales, marketing, engineering, finance, hr

Team Ownership:
    team-alpha, team-beta, team-infrastructure

Best Practices:
---------------
1. Use consistent tag naming (lowercase, hyphen-separated)
2. Define standard tag taxonomy across organization
3. Don't overuse tags - keep it simple
4. Use tags for filtering, not as primary identifier
5. Document tag meanings and usage

Classes:
--------
- MonitoringDetailTag: Tag categorization detail
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import coshsh
from coshsh.monitoringdetail import MonitoringDetail


def __detail_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify TAG monitoring details.

    Called by the plugin factory system to determine if a monitoring
    detail should be upgraded to a MonitoringDetailTag object.

    Args:
        params: Monitoring detail attributes dictionary

    Returns:
        MonitoringDetailTag class if monitoring_type="TAG"
        None if no match

    Example:
        params = {'monitoring_type': 'TAG', 'monitoring_0': 'production'}
        Returns: MonitoringDetailTag class

        params = {'monitoring_type': 'ROLE', 'monitoring_0': 'webserver'}
        Returns: None
    """
    if params is None:
        params = {}

    if params.get("monitoring_type") == "TAG":
        return MonitoringDetailTag
    return None


class MonitoringDetailTag(coshsh.monitoringdetail.MonitoringDetail):
    """Tag categorization monitoring detail.

    Adds tags/labels to applications for flexible categorization.

    Attributes:
        monitoring_type: Always "TAG"
        tag: Tag value (string)

    Class Attributes:
        property: "tags" - property name on application/host
        property_type: list - stored as a list of tags
        property_flat: True - values stored directly (not nested objects)
        property_attr: "tag" - attribute name containing tag value

    Example:
        detail = MonitoringDetailTag({
            'monitoring_type': 'TAG',
            'monitoring_0': 'production'
        })

        # Multiple tags create list:
        # application.tags = ['production', 'critical', 'pci-compliant']

        # Used in template:
        if 'production' in application.tags:
            # Production-specific configuration
            pass
    """

    # Property name added to application/host
    property = "tags"

    # Property type (list of tag values)
    property_type = list

    # Flat property (tag values stored directly, not as objects)
    property_flat = True

    # Attribute containing the tag value
    property_attr = "tag"

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize tag detail.

        Args:
            params: Dictionary with tag parameters

        CSV Format:
            monitoring_0: tag (tag value) - REQUIRED

        Note:
            Multiple TAG entries for the same application create a
            list: application.tags = [tag1, tag2, tag3]
        """
        self.monitoring_type = params["monitoring_type"]
        self.tag = params["monitoring_0"]
