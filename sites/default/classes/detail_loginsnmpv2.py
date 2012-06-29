from monitoring_detail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "LOGINSNMPV2":
        return MonitoringDetailLoginSNMPV2


class MonitoringDetailLoginSNMPV2(MonitoringDetail):
    """
    """
    property = "loginsnmpv2"
    property_type = str

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.community = params.get("monitoring_0", "public")

