import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "INTERFACE":
        return MonitoringDetailInterface


class MonitoringDetailInterface(coshsh.monitoringdetail.MonitoringDetail):
    """
    """
    property = "interfaces"
    property_type = list

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.name = params.get("monitoring_0", None)


