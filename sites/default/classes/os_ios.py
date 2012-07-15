from application import Application
from templaterule import TemplateRule
from util import compare_attr, is_attr

def __mi_ident__(params={}):
    if is_attr("name", params, "os") and compare_attr("type", params, ".*ios.*"):
        return CiscoIOS


class CiscoIOS(Application):
     template_rules = [
         TemplateRule(needsattr=None,
             template="os_ios_default",
         ),
         TemplateRule(needsattr='interfaces',
             template="os_ios_if",
         ),
     ]

     def __new__(cls, params={}):
         return object.__new__(cls)



