print "--->os_aix"
from application import Application
from templaterule import TemplateRule
from util import compare_attr
print "<---os_aix"

def __mi_ident__(params={}):
    if compare_attr("type", params, ".*aix.*"):
        return AIX

class AIX(Application):
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


