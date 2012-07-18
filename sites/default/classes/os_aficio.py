from application import Application
from templaterule import TemplateRule
from util import compare_attr

def __mi_ident__(params={}):
    if compare_attr("type", params, ".*aficio.*"):
        return Aficio

class Aficio(Application):
    template_rules = [
        TemplateRule(needsattr=None, 
            template="os_aficio_default"),
    ]

    def __new__(cls, params={}):
        return object.__new__(cls)


