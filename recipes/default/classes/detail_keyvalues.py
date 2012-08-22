from monitoring_detail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "KEYVALUES":
        return MonitoringDetailKeyvalues


class MonitoringDetailKeyvalues(MonitoringDetail):
    """
    """
    property = "generic"
    property_type = dict

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.dictionary = {
            params["monitoring_0"]: params["monitoring_1"],
            params["monitoring_2"]: params["monitoring_3"],
            params["monitoring_4"]: params["monitoring_5"],
        }

