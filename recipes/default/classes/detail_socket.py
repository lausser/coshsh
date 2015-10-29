import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "SOCKET":
        return MonitoringDetailSocket


class MonitoringDetailSocket(coshsh.monitoringdetail.MonitoringDetail):
    """
    """
    property = "socket"
    property_type = str

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.socket = params["monitoring_0"]
        # Thresholds are shown only as an example. In this case they
        # indicate response times
        self.warning = params.get("monitoring_1", "1")
        self.critical = params.get("monitoring_2", "10")

    def __str__(self):
        return "%s" % (self.socket,)

