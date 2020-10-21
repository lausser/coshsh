import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "KEYVALUES":
        return MonitoringDetailKeyvalues
    elif params["monitoring_type"] == "KEYVALUESARRAY":
        return MonitoringDetailKeyvaluesArray


class MonitoringDetailKeyvalues(coshsh.monitoringdetail.MonitoringDetail):
    """
    """
    property = "generic"
    property_type = dict

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.dictionary = { }
        try:
            self.dictionary[params["monitoring_0"]] = params["monitoring_1"]
        except Exception:
            pass
        try:
            self.dictionary[params["monitoring_2"]] = params["monitoring_3"]
        except Exception:
            pass
        try:
            self.dictionary[params["monitoring_4"]] = params["monitoring_5"]
        except Exception:
            pass


class MonitoringDetailKeyvaluesArray(coshsh.monitoringdetail.MonitoringDetail):
    """
    KEYVALUESARRAY, role, dach
    KEYVALUESARRAY, role, master, parents, "sw1"
    KEYVALUESARRAY, role, dmz, role, prod, parents, "sw2"
    -> application.role = [dach, master, dmz, prod]
    -> application.parents = [sw1, sw2]
    """
    property = "generic"
    property_type = list

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.dictionary = { }
        try:
            self.dictionary[params["monitoring_0"]].append(params["monitoring_1"])
        except Exception:
            self.dictionary[params["monitoring_0"]] = [params["monitoring_1"]]
        try:
            self.dictionary[params["monitoring_2"]].append(params["monitoring_3"])
        except Exception:
            try:
                self.dictionary[params["monitoring_2"]] = [params["monitoring_3"]]
            except Exception:
                pass
        try:
            self.dictionary[params["monitoring_4"]].append(params["monitoring_5"])
        except Exception:
            try:
                self.dictionary[params["monitoring_4"]] = [params["monitoring_5"]]
            except Exception:
                pass

