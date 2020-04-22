import coshsh
from coshsh.application import Application
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr

def __mi_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "oraappindsdb"):
        return Oraappindsdb


class Oraappindsdb(coshsh.application.Application):
    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None,
            template="app_oraappindsdb_default"),
    ]

    def __init__(self, params):
        pass

