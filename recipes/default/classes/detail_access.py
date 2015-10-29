import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "ACCESS":
        return MonitoringDetailAccess


class MonitoringDetailAccess(coshsh.monitoringdetail.MonitoringDetail):
    """
    """
    property = "access"
    property_type = str
    property_flat = True

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.access = params["monitoring_0"]

    def __str__(self):
        return "%s" % (self.access,)


