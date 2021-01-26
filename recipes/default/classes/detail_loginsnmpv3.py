import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "LOGINSNMPV3":
        return MonitoringDetailLoginSNMPV3


class MonitoringDetailLoginSNMPV3(coshsh.monitoringdetail.MonitoringDetail):
    """
    """
    property = "loginsnmpv3"
    property_type = str

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.securityname = params.get("monitoring_0", None)
        self.authprotocol = params.get("monitoring_1", None)
        self.authkey = params.get("monitoring_2", None)
        self.privprotocol = params.get("monitoring_3", None)
        self.privkey = params.get("monitoring_4", None)
        self.context = params.get("monitoring_5", None)
        # noAuthNoPriv|authNoPriv|authPriv
        if not self.authkey and not self.privkey:
            self.securitylevel = "noAuthNoPriv"
        elif self.authkey and not self.privkey:
            self.securitylevel = "authNoPriv"
        elif self.authkey and self.privkey:
            self.securitylevel = "authPriv"

