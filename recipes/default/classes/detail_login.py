import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "LOGIN":
        return MonitoringDetailLogin


class MonitoringDetailLogin(coshsh.monitoringdetail.MonitoringDetail):
    """
    """
    property = "login"
    property_type = str

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.username = params["monitoring_0"]
        self.password = params["monitoring_1"]



