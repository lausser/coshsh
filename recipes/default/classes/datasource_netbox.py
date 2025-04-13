#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).
import logging
import coshsh
from coshsh.host import Host
from coshsh.datasource import Datasource
from pynetbox import api
from collections import defaultdict
import requests


logger = logging.getLogger('coshsh')

def __ds_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "netboxlabsnetbox"):
        return NetboxLabsNetbox


class NetboxLabsNetbox(Datasource):
    """
    If you don't have an api token yet, but username and password.
    $ curl -L -X POST \
    -H "Content-Type: application/json" \
    -H "Accept: application/json; indent=4" \
    https://the-netbox-url/api/users/tokens/provision/ \
    --data '{
        "username": "your-user",
        "password": "your-password"
    }'
    It returns a json structure where the attribute "key" is what we want.
    Note down key's value, this will be the token for the api requests.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = kwargs.get("name", "netbox")
        self.netbox_url = kwargs.get("netbox_url", "http://your-netbox-url:8000")
        self.api_token = kwargs.get("api_token", "your-api-token")
        self.nb = None  # Will be initialized in open()

    def open(self):
        try:
            # Validate token with a lightweight GET request
            headers = {
                "Authorization": f"Token {self.api_token}",
                "Accept": "application/json"
            }
            # Use /api/status/ for lightweight check (NetBox 3.4+)
            status_url = self.netbox_url.rstrip("/") + "/api/status/"
            response = requests.get(status_url, headers=headers, timeout=5)

            # Fall back to /api/ if /status/ fails (e.g., older NetBox versions)
            if response.status_code == 404:
                status_url = self.netbox_url.rstrip("/") + "/api/"
                response = requests.get(status_url, headers=headers, timeout=5)

            # Check response
            if response.status_code != 200:
                raise Exception(f"Token validation failed: HTTP {response.status_code} - {response.text}")

            # Initialize NetBox client
            self.nb = api(
                url=self.netbox_url,
                token=self.api_token
            )
            logger.info("NetBox connection established.")

        except requests.RequestException as e:
            raise Exception(f"Failed to connect to NetBox: {str(e)}")
        except Exception as e:
            raise Exception(f"Error validating NetBox token: {str(e)}")

    def read(self, filter=None, objects=None, details=None, **kwargs):
        self.objects = objects
        # Data structure to hold device info
        devices_data = defaultdict(lambda: {
            "name": "",
            "management_ip": "None",
            "interfaces": [],
            "configured_ips": [],
            "manufacturer_os": "Unknown"
        })

        # Step 1: Fetch all devices
        logger.debug("Fetching devices...")
        devices = list(self.nb.dcim.devices.all())
        device_ids = [d.id for d in devices]

        # Step 2: Fetch all interfaces for these devices
        logger.debug("Fetching interfaces...")
        interfaces = self.nb.dcim.interfaces.filter(device_id=device_ids)

        # Step 3: Fetch all IP addresses assigned to interfaces
        logger.debug("Fetching IP addresses...")
        ip_addresses = self.nb.ipam.ip_addresses.filter(device_id=device_ids)

        # Step 4: Organize interfaces and IPs by device
        logger.debug("Merge data")
        interface_map = defaultdict(list)
        for iface in interfaces:
            interface_map[iface.device.id].append({
                "name": iface.name,
                "type": iface.type.label if iface.type else "Unknown",
                "id": iface.id
            })

        ip_map = defaultdict(list)
        for ip in ip_addresses:
            if ip.assigned_object_type == "dcim.interface" and ip.assigned_object:
                ip_map[ip.assigned_object.device.id].append({
                    "address": ip.address.split("/")[0],
                    "interface": ip.assigned_object.name
                })

        # Step 5: Build device objects
        for device in devices:
            device_id = device.id
            devices_data[device_id]["name"] = device.name or device.display
            devices_data[device_id]["management_ip"] = (
                device.primary_ip4.address.split("/")[0]
                if device.primary_ip4
                else device.primary_ip6.address.split("/")[0]
                if device.primary_ip6
                else "None"
            )
            devices_data[device_id]["interfaces"] = interface_map.get(device_id, [])
            devices_data[device_id]["configured_ips"] = ip_map.get(device_id, [])
            devices_data[device_id]["manufacturer_os"] = (
                device.platform.name
                if device.platform and device.platform.name
                else device.device_type.manufacturer.name
                if device.device_type and device.device_type.manufacturer
                else "Unknown"
            )

        # Step 6: Add devices to coshsh DataRecipient
        for device in devices_data.values():
            host_data = {
                "host_name": device["name"],
                "address": device["management_ip"],
                "type": "network_device",
                "os": device["manufacturer_os"],
                #"interfaces": device["interfaces"],  # List of {"name": ..., "type": ...}
                #"ip_addresses": device["configured_ips"]  # List of {"address": ..., "interface": ...}
            }
            self.add("hosts", Host(host_data))

        logger.debug(f"Added {len(devices_data)} devices to coshsh.")


    def close(self):
        self.nb = None
        logger.info("NetBox connection closed.")
