import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "RAM":
        return MonitoringDetailRam


class MonitoringDetailRam(coshsh.monitoringdetail.MonitoringDetail):
    """
    """
    property = "ram"
    property_type = str

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.warning = params["monitoring_0"]
        self.critical = params["monitoring_1"]

    def __str__(self):
        return "w:%s,c:%s" % (self.warning, self.critical)

