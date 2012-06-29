from operatingsystem import OperatingSystem
from templaterule import TemplateRule
from util import compare_attr

def __mi_ident__(params={}):
    if compare_attr("type", params, ".*aix.*"):
        return AIX

class AIX(OperatingSystem):
    template_rules = [
        TemplateRule(needsattr=None, 
            template="os_aix_default"),
        TemplateRule(needsattr=None, 
            template="os_aix_logs"),
        TemplateRule(needsattr="filesystems", 
            template="os_aix_fs"),
    ]

    def __new__(cls, params={}):
        return object.__new__(cls)


