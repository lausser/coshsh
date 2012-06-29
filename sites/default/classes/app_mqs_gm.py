from monitoring_detail import MonitoringDetail
from application import Application
from templaterule import TemplateRule
from util import compare_attr, is_attr

def __mi_ident__(params={}):
    if compare_attr("type", params, "gearman\-worker") or is_attr("type", params, "gmw"):
        return GearmanWorker
    elif compare_attr("type", params, "gearman\-server") or is_attr("type", params, "gms"):
        return GearmanServer


class GearmanWorker(Application):
    template_rules = [
        TemplateRule(needsattr=None, 
            template="app_mqs_gmw_default",
            unique_config="app_mqs_gmw_%s_default")
    ]

    def __new__(cls, params={}):
        return object.__new__(cls)

    def __init__(self, params={}):
        super(GearmanWorker, self).__init__(params)

        self.monitoring_details.append(MonitoringDetail({
            "monitoring_type" : "PROCESS",
            "monitoring_0" : "mod_gearman_worker",
            "monitoring_1" : "50",
            "monitoring_2" : "1:",
            "monitoring_3" : "worker" }))

    def resolve_monitoring_details(self):
        super(GearmanWorker, self).resolve_monitoring_details()
        if hasattr(self, "ports"):
            self.port = self.ports[0].port
        if len(self.processes) > 1:
            # processes were found in the database
            # delete the default
            del self.processes[0]


class GearmanServer(Application):
    template_rules = [
        TemplateRule(needsattr=None, 
            template="app_mqs_gms_default",
            unique_config="app_mqs_gms_%s_default")
    ]

    def __new__(cls, params={}):
        return object.__new__(cls)

    def __init__(self, params={}):
        super(GearmanServer, self).__init__(params)
        self.port = "4730"
        self.process_name = "gearmand"
        self.monitoring_details.append(MonitoringDetail({
            "monitoring_type" : "PROCESS",
            "monitoring_0" : "gearmand",
            "monitoring_1" : "1",
            "monitoring_2" : "1:",
            "monitoring_3" : "server" }))

    def resolve_monitoring_details(self):
        super(GearmanServer, self).resolve_monitoring_details()
        if hasattr(self, "ports"):
            self.port = self.ports[0].port
        if len(self.processes) > 1:
            # processes were found in the database
            # delete the default
            del self.processes[0]


