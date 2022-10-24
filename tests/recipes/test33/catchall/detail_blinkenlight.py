import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "BLINKENLIGHT":
        return MonitoringDetailBlinkenLight


class MonitoringDetailBlinkenLight(coshsh.monitoringdetail.MonitoringDetail):
    """
    """
    property = "blinkenlights"
    property_type = list

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.color = params["monitoring_0"]

    def __str__(self):
        return "%s light" % (self.color,)

