from operatingsystem import OperatingSystem
from templaterule import TemplateRule
from util import compare_attr

def __mi_ident__(params={}):
    if compare_attr("type", params, ".*solaris.*"):
        return Solaris


class Solaris(OperatingSystem):
    template_rules = [
        TemplateRule(needsattr=None, 
            template="os_solaris_default"),
        TemplateRule(needsattr=None, 
            template="os_solaris_logs"),
        TemplateRule(needsattr=None,
            template="os_solaris_fs"),
    ]

    def __new__(cls, params={}):
        return object.__new__(cls)


class Solaris10(Solaris):
    pass


