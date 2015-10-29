import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "PORT":
        return MonitoringDetailPort


class MonitoringDetailPort(coshsh.monitoringdetail.MonitoringDetail):
    """
    """
    property = "ports"
    property_type = list

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.port = params["monitoring_0"]
        # Thresholds are shown only as an example. In this case they
        # indicate response times
        self.warning = params.get("monitoring_1", "1")
        self.critical = params.get("monitoring_2", "10")

    def __str__(self):
        return "%s" % (self.port,)


