"""Storage Volume Monitoring Detail Plugin

This plugin handles storage volume monitoring configuration.

Plugin Identification:
---------------------
Identifies monitoring details with monitoring_type = "VOLUME".

Purpose:
--------
Configures storage volume monitoring including:
    - Logical volume space usage
    - Volume group monitoring
    - Storage array volumes
    - SAN/NAS volume monitoring
    - Virtual disk monitoring

Difference from FILESYSTEM:
--------------------------
- FILESYSTEM: Monitors mounted filesystems (/var, C:\, etc.)
- VOLUME: Monitors underlying storage volumes (LVM, storage arrays, etc.)

Use Cases:
----------
- LVM logical volumes (Linux)
- Storage array LUNs
- SAN volumes
- Virtual machine volumes
- NetApp/EMC volumes

Input Format:
-------------
CSV Format (monitoring_N columns):
    monitoring_type = VOLUME
    monitoring_0 = name (volume name/identifier)
    monitoring_1 = warning (default: 10)
    monitoring_2 = critical (default: 5)
    monitoring_3 = units (default: %)

Parameters:
-----------
- name: Volume name or identifier
    Examples:
        LVM: vg0/lv_data, vg_apps/lv_logs
        Storage: lun001, vol_database
        Virtual: vmdk_data, vhd_backup

- warning: Warning threshold for free space
    Default: 10 (10% free space remaining)
    With units=%: Percentage of free space
    With units=GB: Gigabytes of free space

- critical: Critical threshold for free space
    Default: 5 (5% free space remaining)
    With units=%: Percentage of free space
    With units=GB: Gigabytes of free space

- units: Measurement units
    Default: % (percentage)
    Options: %, MB, GB, TB, KB

Template Usage:
---------------
The 'volumes' property is populated as a list on the application/host.
Templates can iterate over this list to generate individual checks.

Example template:
    {% for vol in application.volumes %}
    define service {
        host_name               {{ application.host_name }}
        service_description     Volume {{ vol.name }}
        check_command           check_volume!{{ vol.name }}!{{ vol.warning }}!{{ vol.critical }}
    }
    {% endfor %}

Configuration Examples:
----------------------
CSV datasource (applicationdetails.csv):
    host_name,name,type,monitoring_type,monitoring_0,monitoring_1,monitoring_2,monitoring_3
    server01,lvm,storage,VOLUME,vg0/lv_data,10,5,%
    server01,lvm,storage,VOLUME,vg0/lv_logs,15,10,%
    san01,netapp,storage,VOLUME,vol_db_prod,100,50,GB
    vmhost01,vsphere,virtualization,VOLUME,datastore1,20,10,%

Explanation:
    - server01 vg0/lv_data: LVM volume, alert at 10%/5% free
    - server01 vg0/lv_logs: LVM volume, alert at 15%/10% free
    - san01 vol_db_prod: NetApp volume, alert at 100GB/50GB free
    - vmhost01 datastore1: VMware datastore, alert at 20%/10% free

Common Volume Types:
-------------------
LVM (Linux):
    vg_name/lv_name
    Examples: vg0/lv_root, vg_data/lv_mysql

Storage Arrays:
    lun001, lun002
    vol_prod_001, vol_test_001

Virtual Infrastructure:
    datastore1, datastore_prod
    vmdk_database, vhd_appdata

Cloud Storage:
    ebs-vol-12345678
    disk-prod-001

Classes:
--------
- MonitoringDetailVolume: Storage volume monitoring detail
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import coshsh
from coshsh.monitoringdetail import MonitoringDetail


def __detail_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify VOLUME monitoring details.

    Called by the plugin factory system to determine if a monitoring
    detail should be upgraded to a MonitoringDetailVolume object.

    Args:
        params: Monitoring detail attributes dictionary

    Returns:
        MonitoringDetailVolume class if monitoring_type="VOLUME"
        None if no match

    Example:
        params = {'monitoring_type': 'VOLUME', 'monitoring_0': 'vg0/lv_data'}
        Returns: MonitoringDetailVolume class

        params = {'monitoring_type': 'FILESYSTEM', 'monitoring_0': '/var'}
        Returns: None
    """
    if params is None:
        params = {}

    if params.get("monitoring_type") == "VOLUME":
        return MonitoringDetailVolume
    return None


class MonitoringDetailVolume(coshsh.monitoringdetail.MonitoringDetail):
    """Storage volume monitoring detail.

    Represents a storage volume to be monitored, with free space thresholds.

    Attributes:
        monitoring_type: Always "VOLUME"
        name: Volume name/identifier
        warning: Warning threshold (free space)
        critical: Critical threshold (free space)
        units: Measurement units (%, MB, GB, TB, KB)

    Class Attributes:
        property: "volumes" - property name on application/host
        property_type: list - stored as a list

    Example:
        detail = MonitoringDetailVolume({
            'monitoring_type': 'VOLUME',
            'monitoring_0': 'vg0/lv_data',
            'monitoring_1': '10',
            'monitoring_2': '5',
            'monitoring_3': '%'
        })

        # Used in template:
        for vol in application.volumes:
            print(f"Check volume {vol.name} at {vol.warning}/{vol.critical}{vol.units}")
    """

    # Property name added to application/host
    property = "volumes"

    # Property type (list allows multiple volumes)
    property_type = list

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize storage volume monitoring detail.

        Args:
            params: Dictionary with volume parameters

        CSV Format:
            monitoring_0: name (volume name/identifier) - REQUIRED
            monitoring_1: warning (default: 10)
            monitoring_2: critical (default: 5)
            monitoring_3: units (default: %)

        Note:
            Thresholds represent free space. Lower values trigger alerts.
            Example: warning=10, critical=5 means alert at 10%/5% free.
        """
        self.monitoring_type = params["monitoring_type"]
        self.name = params["monitoring_0"]
        self.warning = params.get("monitoring_1", "10")
        self.critical = params.get("monitoring_2", "5")
        self.units = params.get("monitoring_3", "%")

    def __str__(self) -> str:
        """Return string representation for debugging.

        Returns:
            String in format: "name warning:critical:0:100"

        Example:
            "vg0/lv_data 10:5:0:100"

        Note:
            Format may be used by legacy templates or debugging.
            The "0:100" represents min:max range (0-100%).
        """
        return f"{self.name} {self.warning}:{self.critical}:0:100"
