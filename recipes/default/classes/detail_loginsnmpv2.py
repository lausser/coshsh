import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "LOGINSNMPV2":
        return MonitoringDetailLoginSNMPV2


class MonitoringDetailLoginSNMPV2(coshsh.monitoringdetail.MonitoringDetail):
    """
    """
    property = "loginsnmpv2"
    property_type = str

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.community = params.get("monitoring_0", "public") or "_none_"
        if self.community.startswith("v1:"):
            self.protocol = 1
            self.community = self.community.split(":", 1)[1]
        elif self.community.startswith("v2:"):
            self.protocol = 2
            self.community = self.community.split(":", 1)[1]
        else:
            self.protocol = 2

    def __str__(self):
        return "SNMP v2/1 community: %s" % (self.community)
