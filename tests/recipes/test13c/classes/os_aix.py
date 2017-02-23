import coshsh
from coshsh.application import Application
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr

def __mi_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "aix"):
        return AIX


class AIX(coshsh.application.Application):
    marker = "corporate"
    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None, 
            template="os_aix_default"),
    ]

