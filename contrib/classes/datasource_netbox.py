#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).
import logging
import coshsh
from coshsh.datasource import Datasource, DatasourceCorrupt, DatasourceNotAvailable
from coshsh.host import Host
from coshsh.monitoringdetail import MonitoringDetail
from pynetbox import api
from collections import defaultdict
import requests
from requests.adapters import HTTPAdapter
import urllib.parse
import urllib3
urllib3.disable_warnings()


logger = logging.getLogger('coshsh')

def __ds_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "netboxlabsnetbox"):
        return NetboxLabsNetbox


class TimeoutBaseURLAdapter(HTTPAdapter):
    """Adapter für pynetbox, der Timeouts setzt und relative URLs mit einer Basis-URL kombiniert."""
    def __init__(self, base_url, timeout=60, *args, **kwargs):
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        # Timeout setzen, falls nicht explizit angegeben
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = self.timeout

        # Relative URLs mit base_url kombinieren
        if not urllib.parse.urlparse(request.url).netloc:
            request.url = urllib.parse.urljoin(self.base_url, request.url.lstrip("/"))
        elif urllib.parse.urlparse(request.url).netloc != urllib.parse.urlparse(self.base_url).netloc:
            request.url = request.url.replace(urllib.parse.urlparse(request.url).netloc, urllib.parse.urlparse(self.base_url).netloc)

        return super().send(request, **kwargs)



class TimeoutHTTPAdapter(HTTPAdapter):
    """ Adapter for setting pynetbox timeouts """
    def __init__(self, *args, **kwargs):
        self.timeout = 60
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        if kwargs["timeout"] is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)



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
        self.netbox_host = kwargs.get("netbox_host")
        self.api_token = kwargs.get("api_token", "your-api-token")
        self.insecure_skip_verify = kwargs.get("insecure_skip_verify", "no")
        self.nb = None  # Will be initialized in open()
        self.no_ip_devices = (
            ("Dell", "FS25")
        )

    def open(self):
        try:
            # Setup the header for special requirements
            headers = {
                "Authorization": f"Token {self.api_token}",
                "Accept": "application/json"
            }
            if self.netbox_host:
                # In case you tunnel the connection through ssh and the
                # url starts with https://127.0.0.1, you have to add the
                # real hostname in the request header.
                headers["Host"] = self.netbox_host
            # Initialize NetBox client
            self.nb = api(
                url=self.netbox_url,
                token=self.api_token,
                threading=True
            )
            if self.netbox_host:
                # enforce the netloc of a query url is always netbox_url
                adapter = TimeoutBaseURLAdapter(base_url=self.netbox_url, timeout=120)
            else:
                adapter = TimeoutHTTPAdapter(timeout=120)
            session = requests.Session()
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            session.verify = False if self.insecure_skip_verify == "yes" else True
            session.headers = headers
            self.nb.http_session = session
            version = self.nb.version
            status = self.nb.status()
            logger.info("NetBox connection established.")

        except requests.RequestException as e:
            logger.critical(f"Failed to connect to NetBox: {str(e)}")
            raise DatasourceNotAvailable
        except Exception as e:
            logger.critical(f"Error validating NetBox token: {str(e)}")
            raise DatasourceNotAvailable

    def read(self, filter=None, objects=None, details=None, **kwargs):
        self.objects = objects
        # Data structure to hold device info
        devices_data = defaultdict(lambda: {
            "status": "Planned",
            "name": "",
            "management_ip": "None",
            "interfaces": [],
            "configured_ips": [],
            "manufacturer_os": "Unknown",
            "platform": "Unknown",
            "model": "Unknown",
            "rack": "Unknown",
            "tenant": "Unknown",
            "site": "Unknown",
            "role": "Unknown",
        })

        try:
            # Step 1: Fetch devices (pynetbox handles pagination internally)
            logger.info("Fetching devices...")
            devices = list(self.nb.dcim.devices.all())
            logger.info(f"Fetched {len(devices)} devices.")

            # Step 2: Fetch interfaces
            logger.info("Fetching interfaces...")
            interfaces = list(self.nb.dcim.interfaces.all())
            logger.info(f"Fetched {len(interfaces)} interfaces.")

            # Step 3: Fetch IP addresses
            logger.info("Fetching IP addresses...")
            ip_addresses = list(self.nb.ipam.ip_addresses.all())
            logger.info(f"Fetched {len(ip_addresses)} IP addresses.")
    
            # Step 4: Organize interfaces and IPs by device
            interface_map = defaultdict(list)
            for iface in interfaces:
                if iface.device:  # Ensure interface is tied to a device
                    interface_map[iface.device.id].append({
                        "name": iface.name,
                        "type": iface.type.label if iface.type else "Unknown",
                        "id": iface.id
                    })

            ip_map = defaultdict(list)
            for ip in ip_addresses:
                if (ip.assigned_object_type == "dcim.interface" and 
                    ip.assigned_object and 
                    ip.assigned_object.device):
                    ip_map[ip.assigned_object.device.id].append({
                        "address": ip.address.split("/")[0],
                        "interface": ip.assigned_object.name
                    })

            # Step 5: Build device objects
            for device in devices:
                print(device.__dict__)
                device_id = device.id
                devices_data[device_id]["name"] = device.name or device.display
                devices_data[device_id]["management_ip"] = (
                    device.primary_ip4.address.split("/")[0]
                    if device.primary_ip4
                    else device.primary_ip6.address.split("/")[0]
                    if device.primary_ip6
                    else None
                )
                devices_data[device_id]["oob_ip"] = (
                    device.oob_ip.address.split("/")[0]
                    if device.oob_ip
                    else None
                )
                devices_data[device_id]["interfaces"] = interface_map.get(device_id, [])
                devices_data[device_id]["configured_ips"] = ip_map.get(device_id, [])
                devices_data[device_id]["manufacturer"] = (
                    device.device_type.manufacturer.name
                    if device.device_type and device.device_type.manufacturer
                    else "Unknown"
                )
                devices_data[device_id]["model"] = (
                    device.device_type.model
                    if device.device_type and device.device_type.model
                    else "Unknown"
                )
                devices_data[device_id]["platform"] = (
                    device.platform.name
                    if device.platform
                    else "Unknown"
                )
                devices_data[device_id]["rack"] = (
                    device.rack.name
                    if device.rack
                    else "Unknown"
                )
                devices_data[device_id]["site"] = (
                    device.site.name
                    if device.site
                    else "Unknown"
                )
                devices_data[device_id]["location"] = (
                    device.location.name
                    if device.location
                    else "Unknown"
                )
                devices_data[device_id]["tenant"] = (
                    device.tenant.name
                    if device.tenant
                    else "Unknown"
                )
                devices_data[device_id]["role"] = (
                    device.role.name
                    if device.role
                    else "Unknown"
                )
                devices_data[device_id]["status"] = (
                    device.status
                    if device.status
                    else "Unknown"
                )

            # Step 6: Add devices to coshsh DataRecipient
            for device in devices_data.values():
                address = device["oob_ip"] if device["oob_ip"] else device["management_ip"] if device["management_ip"] else None
                if not address:
                    if (device["manufacturer"], device["model"]) not in self.no_ip_devices:
                        logger.warning(device["name"]+" has no usable ip address")
                host_data = {
                    "host_name": device["name"],
                    "address": address,
                    "type": "network_device",
                    "os": device["manufacturer"]+" "+device["model"],
                }
                host = Host(host_data)
                self.add("hosts", host)
                host.templates = ["generic-host"]
                host.hostgroups.append("role_"+device["role"].replace(" ", "_"))
                host.hostgroups.append("location_"+device["location"].replace(" ", "_"))
                host.hostgroups.append("rack_"+device["rack"].replace(" ", "_"))
                host.hostgroups.append("platform_"+device["platform"].replace(" ", "_"))
                host.hostgroups.append("model_"+device["manufacturer"].replace(" ", "_")+"_"+device["model"].replace(" ", "_"))

                # List of {"name": ..., "type": ...}
                interfaces = device.get("interfaces", [])
                # List of {"address": ..., "interface": ...}
                ip_addrs = device.get("configured_ips", [])
                for interface in interfaces:
                    configured_addresses = []
                    for ip_addr in ip_addrs:
                        if ip_addr["interface"] == interface["name"]:
                            configured_addresses.append(ip_addr["address"])
                    if configured_addresses:
                        self.add("details", MonitoringDetail({"host_name": host.host_name, "monitoring_type": "RICHINTERFACE", "monitoring_0": interface["name"], "monitoring_1": interface["type"], "monitoring_2": configured_addresses}))
                    else:
                        #self.add("details", MonitoringDetail({"host_name": host.host_name, "monitoring_type": "RICHINTERFACE", "monitoring_0": interface["name"], "monitoring_1": interface["type"], "monitoring_2": configured_addresses}))
                        self.add("details", MonitoringDetail({"host_name": host.host_name, "monitoring_type": "INTERFACE", "monitoring_0": interface["name"]}))

            logger.info(f"Added {len(devices_data)} devices to coshsh.")

        except Exception as e:
            print(f"Error reading from NetBox: {str(e)}")
            raise DatasourceCorrupt


    def close(self):
        self.nb = None
        logger.info("NetBox connection closed.")
