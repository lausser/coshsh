import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "ROLE":
        return MonitoringDetailRole


class MonitoringDetailRole(coshsh.monitoringdetail.MonitoringDetail):
    """
    """
    property = "role"
    property_type = str
    property_flat = True

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.role = params["monitoring_0"]

    def __str__(self):
        return "%s" % (self.role,)

