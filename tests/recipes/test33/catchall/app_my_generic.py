import coshsh
from coshsh.application import Application
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr

def __mi_ident__(params={}):
    if coshsh.util.compare_attr("type", params, ".*"):
        return MyGenericApplication


class MyGenericApplication(coshsh.application.Application):
    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr='filesystems',
            template="app_my_generic_fs"),
        coshsh.templaterule.TemplateRule(needsattr='services',
            template="app_my_generic_services"),
        coshsh.templaterule.TemplateRule(needsattr='ports',
            template="app_my_generic_ports"),
        coshsh.templaterule.TemplateRule(needsattr='blinkenlights',
            template="app_my_generic_blinkenlights"),
    ]

