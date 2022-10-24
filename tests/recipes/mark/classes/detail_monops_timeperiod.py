import json
import coshsh
from coshsh.monitoringdetail import MonitoringDetail
from pprint import pprint
 
def __detail_ident__(params={}):
    print("DETAIL {}".format(params))
    if params["monitoring_type"] == "MONOPS_DETAIL_TIMEPERIOD":
        return MonitoringDetailMonopsTimeperiod
 
 
class MonitoringDetailMonopsTimeperiod(coshsh.monitoringdetail.MonitoringDetail):
    property = "timeperiods"
    property_type = list
 
    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.name = params["monitoring_0"]
        self.alias = params["monitoring_1"]
        self.day = params["monitoring_2"]
        self.from_1 = params["monitoring_3"]
        self.to_1 = params["monitoring_4"]
        self.from_2 = params["monitoring_5"]
        self.to_2 = params["monitoring_6"]
        self.from_3 = params["monitoring_7"]
        self.to_3 = params["monitoring_8"]
        self.from_4 = params["monitoring_9"]
        self.to_4 = params["monitoring_10"]
        self.exclude = params["monitoring_11"]
 
    def __str__(self):
        return "%s %s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s" % (self.name, self.alias, self.day, self.from_1, self.to_1, self.from_2, self.to_2, self.from_2, self.to_2, self.from_3, self.to_3, self.from_4, self.to_4, self.exclude)

