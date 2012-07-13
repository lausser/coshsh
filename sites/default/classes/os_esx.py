from application import OperatingSystem
from templaterule import TemplateRule
from util import compare_attr

def __mi_ident__(params={}):
    if compare_attr("type", params, ".*esx.*"):
        return ESX

class ESX(OperatingSystem):
    template_rules = [
        TemplateRule( template="os_esx_default", ),
        TemplateRule(needsattr='datastores', template="os_esx_fs", ),
        TemplateRule(needsattr='vms', template="os_esx_vm", ),
    ]

    def __new__(cls, params={}):
        if params["version"] == "ESX4.1":
            newcls = ESX4
        else:
            newcls = cls
        return object.__new__(newcls)

    def resolve_monitoring_details(self):
        super(ESX, self).resolve_monitoring_details()
        self.vms = []


class ESX4(ESX):

    def __new__(cls, params={}):
        return object.__new__(cls)


