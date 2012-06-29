from operatingsystem import OperatingSystem
from templaterule import TemplateRule
from util import compare_attr

def __mi_ident__(params={}):
    if compare_attr("type", params, ".*hp\-ux.*|.*hpux.*"):
        return HPUX


class HPUX(OperatingSystem):
    template_rules = [
        TemplateRule(needsattr=None, 
            template="os_hpux_default"),
        TemplateRule(needsattr="filesystems", 
            template="os_hpux_fs"),
    ]

    def __new__(cls, params={}):
        return object.__new__(cls)


