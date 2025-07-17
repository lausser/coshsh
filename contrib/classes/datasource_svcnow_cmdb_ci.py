import logging
import requests
import socket
import os
import json
import coshsh
from coshsh.datasource import Datasource
from coshsh.host import Host
from coshsh.contact import Contact
from coshsh.contactgroup import ContactGroup
from coshsh.monitoringdetail import MonitoringDetail
import urllib3
urllib3.disable_warnings()


logger = logging.getLogger('coshsh')

def __ds_ident__(params={}):
    if params.get("type") == "svcnow_cmdb_ci":
        return ServiceNowDatasource

class ServiceNowDatasource(Datasource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instance_url = kwargs["instance_url"]
        self.cmdb_url = kwargs["cmdb_url"]
        self.incident_url = kwargs["incident_url"]
        self.username = kwargs["username"]
        self.password = kwargs["password"]
        insecure_skip_verify = kwargs.get("insecure_skip_verify", "no")
        self.verify = False if insecure_skip_verify == "yes" else True
        if not self.cmdb_url and self.instance_url:
            self.cmdb_url = self.instance_url
        if not self.incident_url and self.instance_url:
            self.incident_url = self.instance_url
        self.page_size = 100
        self.servicenow_tables = {}

    def get_cmn_item(self, table, sys_id):
        # {
        #   "link": "https://.../api/now/table/cmn_department/5228mae283328",
        #   "value": "5228mae283328"
        if isinstance(sys_id, dict):
            sys_id = sys_id["value"]
        for item in self.servicenow_tables.get(table, []):
            if sys_id == item.get("sys_id", "non-existing-sys-id"):
                return item.get("name")
        return None
        
    def fetch_table(self, table):
        self.servicenow_tables[table] = []
        offset = 0
        while True:
            url = f"{self.cmdb_url}/api/now/table/{table}"
            params = {
                "sysparm_limit": self.page_size,
                "sysparm_offset": offset,
                #"sysparm_query": "sys_class_name=cmdb_ci^operational_status=1"
            }
            try:
                response = requests.get(
                    url,
                    auth=(self.username, self.password),
                    headers={"Accept": "application/json"},
                    params=params,
                    verify=self.verify
                )
                response.raise_for_status()
                data = response.json().get("result", [])
                
                self.servicenow_tables[table].extend(data)
                
                if len(data) < self.page_size:
                    break
                offset += self.page_size
                
            except requests.exceptions.RequestException as e:
                logger.error(f"ServiceNow API error: {e}, table {table}")
                break
        with open(os.environ["OMD_ROOT"]+"/tmp/table_"+table+".json", "w") as f:
            json.dump(self.servicenow_tables[table], f, indent=2)


    def read(self, filter=None, objects={}, **kwargs):
        self.objects = objects
        logger.info("Fetching CMDB CI data from ServiceNow")
        self.fetch_table("cmn_department")
        self.fetch_table("cmn_location")
        self.fetch_table("cmdb_ci")
        
        servicenow = Contact({
            "name": "servicenow", "userid": "servicenow", "type": "SERVICENOW",
            "notification_period": "24x7",
        })
        servicenow.custom_macros = {
            "_SERVICENOW_USERNAME": self.username,
            "_SERVICENOW_PASSWORD": self.password,
            "_SERVICENOW_INCIDENT_URL": self.incident_url+"/api/now/table/incident",
        }
        self.add("contacts", servicenow)
        self.add("contactgroups", ContactGroup({"contactgroup_name": "servicenow"}))
        servicenow.contactgroups.append("servicenow")

        logger.info("Processing CMDB CI data")
        for item in self.servicenow_tables["cmdb_ci"]:
            host_name = item["name"]
            sys_class_name = item["sys_class_name"]
            if item["sys_class_name"] not in [
                "cmdb_ci_aix_server",
                "cmdb_ci_cluster",
                "cmdb_ci_cluster_node",
                "cmdb_ci_computer",
                "cmdb_ci_database",
                "cmdb_ci_esx_server",
                "cmdb_ci_firewall_network",
                "cmdb_ci_ip_network",
                "cmdb_ci_ip_router",
                "cmdb_ci_ip_switch",
                "cmdb_ci_kubernetes_cluster",
                "cmdb_ci_kubernetes_node",
                "cmdb_ci_linux_server",
                "cmdb_ci_netgear",
                "cmdb_ci_printer",
                "cmdb_ci_server",
                "cmdb_ci_storage_switch",
                "cmdb_ci_unix_server",
                "cmdb_ci_vcenter_dvs",
                "cmdb_ci_vmware_instance",
                "cmdb_ci_web_server",
                "cmdb_ci_win_cluster",
                "cmdb_ci_win_cluster_node",
                "cmdb_ci_win_server",
            ]:
                logger.debug(f"{host_name} is an unsupported {sys_class_name}")
                continue
            try:
                address = item.get("ip_address", None)
                if not address:
                    address = socket.gethostbyname(host_name)
                    logger.debug(f"{host_name} has dns address {address}")
                else:
                    address = address.rstrip(".")
                    logger.debug(f"{host_name} has cmdb address {address}")
            except Exception as e:
                logger.critical(f"{host_name} ({sys_class_name}) has no ip address")
                continue
            existing_host = self.get("hosts", host_name)
            if existing_host:
                logger.debug(f"{host_name} already exists, update from svcnow")
                host = existing_host
            else:
                host = Host({
                    "host_name": host_name,
                    "address": address,
                    "os": item.get("os"),
                })
            host.templates = ["generic-host"]
            host.hostgroups.append("sys_class_"+sys_class_name)
            location = self.get_cmn_item("cmn_location", item["location"])
            department = self.get_cmn_item("cmn_department", item["department"])
            if location:
                host.hostgroups.append("loc_"+location)
            if department:
                host.hostgroups.append("dpt_"+department)
            host.contact_groups.append("servicenow")
            self.add('hosts', host)
            self.add("details", MonitoringDetail({"host_name": host_name, "monitoring_type": "CUSTOMMACRO", "monitoring_0": "SYS_CLASS_NAME", "monitoring_1": sys_class_name}))
            self.add("details", MonitoringDetail({"host_name": host_name, "monitoring_type": "CUSTOMMACRO", "monitoring_0": "SYS_ID", "monitoring_1": item.get("sys_id")}))
            self.add("details", MonitoringDetail({"host_name": host_name, "monitoring_type": "CUSTOMMACRO", "monitoring_0": "SERIAL", "monitoring_1": item.get("serial_number")}))


