import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "RICHINTERFACE":
        return MonitoringDetailRichInterface


class MonitoringDetailRichInterface(coshsh.monitoringdetail.MonitoringDetail):
    """
    """
    property = "interfaces"
    property_type = list

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.name = params.get("monitoring_0", None)
        self.type = params.get("monitoring_1", None)
        self.addresses = params.get("monitoring_2", [])

    def __repr__(self):
        return "%s %s %s %s" % (self.monitoring_type, self.name, self.type, ",".join(self.addresses))

