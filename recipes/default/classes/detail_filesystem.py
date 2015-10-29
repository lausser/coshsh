import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "FILESYSTEM":
        return MonitoringDetailFilesystem


class MonitoringDetailFilesystem(coshsh.monitoringdetail.MonitoringDetail):
    """
    """
    property = "filesystems"
    property_type = list
    unique_attribute = "path"

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        if "monitoring_0" in params:
            self.path = params["monitoring_0"]
            self.warning = str(params.get("monitoring_1", "10"))
            self.critical = str(params.get("monitoring_2", "5"))
            self.units = params.get("monitoring_3", "%")
            self.optional = bool(params.get("monitoring_4", "0"))
            self.iwarning = str(params.get("monitoring_5", "0"))
            self.icritical = str(params.get("monitoring_6", "0"))
        else:
            self.path = params["path"]
            self.warning = str(params.get("warning", "10"))
            self.critical = str(params.get("critical", "5"))
            self.units = params.get("units", "%")
            self.optional = bool(params.get("optional", "0"))
        if not self.units:
            self.units = "%"

    def __str__(self):
        return "%s %s:%s:0:100" % (self.path, self.warning, self.critical)

