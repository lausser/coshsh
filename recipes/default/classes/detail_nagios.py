import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "NAGIOS":
        return MonitoringDetailNagios


class MonitoringDetailNagios(coshsh.monitoringdetail.MonitoringDetail):
    property = "generic"
    property_type = str

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.attribute = params.get("monitoring_0", None)
        self.value = params.get("monitoring_1", None)


