import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "TAG":
        return MonitoringDetailTag


class MonitoringDetailTag(coshsh.monitoringdetail.MonitoringDetail):
    """
    """
    property = "tags"
    property_type = list
    property_flat = True
    property_attr = "tag" # application.tags will be a list of property.tag

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.tag = params["monitoring_0"]

