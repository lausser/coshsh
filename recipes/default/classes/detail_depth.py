import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "DEPTH":
        return MonitoringDetailDepth


class MonitoringDetailDepth(coshsh.monitoringdetail.MonitoringDetail):
    """
    Describes hwo deep the monitoring of an application should go.
    Levels are 0 (ignore), 1 (minimum) ... n (expert level, debugging)
    """
    property = "monitoring_depth"
    property_type = int
    property_flat = True

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.monitoring_depth = int(params.get("monitoring_0", 1))

    def __str__(self):
        return "%s" % (self.monitoring_depth,)

