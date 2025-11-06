"""VMware Datastore Monitoring Detail Plugin

This plugin handles VMware datastore (VMFS) monitoring configuration.

Plugin Identification:
---------------------
Identifies monitoring details with monitoring_type = "DATASTORE".

Purpose:
--------
Configures VMware datastore monitoring including:
    - Datastore space usage
    - VMFS volume monitoring
    - Free space thresholds
    - ESXi datastore capacity

VMware Datastores:
-----------------
Datastores in VMware are storage volumes where virtual machines,
templates, and ISO images are stored. They can be:
    - VMFS (VMware File System) on local/SAN storage
    - NFS network shares
    - vSAN (VMware vSAN)

Input Format:
-------------
CSV Format (monitoring_N columns):
    monitoring_type = DATASTORE
    monitoring_0 = name (datastore name)
    monitoring_1 = warning (default: 10)
    monitoring_2 = critical (default: 5)
    monitoring_3 = units (default: %)

Parameters:
-----------
- name: Datastore name
    Examples: datastore1, prod-ssd-01, backup-nfs

- warning/critical: Free space thresholds (default %)
- units: Measurement units (%, GB, TB)

The plugin automatically generates the VMFS path:
    /vmfs/volumes/{datastore_name}

Template Usage:
---------------
Example:
    {% for ds in application.datastores %}
    define service {
        host_name               {{ application.host_name }}
        service_description     Datastore {{ ds.name }}
        check_command           check_datastore!{{ ds.name }}!{{ ds.warning }}!{{ ds.critical }}
    }
    {% endfor %}

Configuration Examples:
----------------------
CSV datasource (applicationdetails.csv):
    host_name,name,type,monitoring_type,monitoring_0,monitoring_1,monitoring_2,monitoring_3
    esxi01,vsphere,virtualization,DATASTORE,datastore1,10,5,%
    esxi01,vsphere,virtualization,DATASTORE,prod-ssd-01,15,10,%

Classes:
--------
- MonitoringDetailDatastore: VMware datastore monitoring detail
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import coshsh
from coshsh.monitoringdetail import MonitoringDetail


def __detail_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    if params is None:
        params = {}
    if params.get("monitoring_type") == "DATASTORE":
        return MonitoringDetailDatastore
    return None


class MonitoringDetailDatastore(coshsh.monitoringdetail.MonitoringDetail):
    """VMware datastore monitoring detail."""

    property = "datastores"
    property_type = list

    def __init__(self, params: Dict[str, Any]) -> None:
        self.monitoring_type = params["monitoring_type"]
        self.name = params["monitoring_0"]
        self.path = f"/vmfs/volumes/{self.name}"
        self.warning = params.get("monitoring_1", "10")
        self.critical = params.get("monitoring_2", "5")
        self.units = params.get("monitoring_3", "%")

    def __str__(self) -> str:
        return f"{self.name} {self.warning}:{self.critical}:0:100"
