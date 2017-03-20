import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "CUSTOMMACRO":
        return MonitoringDetailCustomMacro


class MonitoringDetailCustomMacro(coshsh.monitoringdetail.MonitoringDetail):
    """
    """
    property = "custom_macros"
    property_type = dict

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.key = params["monitoring_0"]
        self.value = params["monitoring_1"]

    def __str__(self):
        return "%s: %s" % (self.key, self.value)

