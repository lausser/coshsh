from application import Application
from templaterule import TemplateRule
from util import compare_attr

def __mi_ident__(params={}):
    if compare_attr("type", params, "apache"):
        return Apache


class Apache(Application):
    template_rules = [
        TemplateRule(needsattr=None,
            template="app_web_apache_default",
            unique_config="app_web_apache_%s_default",
        ),
        TemplateRule(needsattr="False",
            template="app_web_apache_perf",
            unique_config="app_web_apache_%s_perf",
        ),
    ]

    def __new__(cls, params={}):
        if params["version"] and params["version"].startswith("1"):
            newcls = Apache
        else:
            newcls = cls
        return object.__new__(newcls)



