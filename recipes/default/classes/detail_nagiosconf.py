import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "NAGIOSCONF":
        return MonitoringDetailNagiosConf


class MonitoringDetailNagiosConf(coshsh.monitoringdetail.MonitoringDetail):
    property = "nagios_config_attributes"
    property_type = list

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        # modify an attribute of service "name"
        self.name = params.get("monitoring_0", None)
        self.attribute = params.get("monitoring_1", None)
        if self.attribute.endswith('groups'):
            self.value = [params.get("monitoring_2", None)]
        else:
            self.value = params.get("monitoring_2", None)


