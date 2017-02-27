import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}): 
    if params["monitoring_type"] == "PROCESS":
        return MonitoringDetailProcess


class MonitoringDetailProcess(coshsh.monitoringdetail.MonitoringDetail):
    """
    """
    property = "processes"
    property_type = list
    mandatory_fields = ["monitoring_0"]

    def __init__(self, params):
        try:
            self.monitoring_type = params["monitoring_type"]
            if "monitoring_0" not in params:
                logger.info("mandatory parameter monitoring_0 missing %s:%s:%s" % (params["host_name"], params["name"], params["type"]))
            self.name = params["monitoring_0"]
            self.warning = params.get("monitoring_1", "1:1")
            self.critical = params.get("monitoring_2", "1:")
            self.alias = params.get("monitoring_3", self.name)
        except Exception:
            pass

    def __str__(self):
        return "%s %s:%s:0:100" % (self.name, self.warning, self.critical)


