from application import Application
from templaterule import TemplateRule
from util import compare_attr

def __mi_ident__(params={}):
    if compare_attr("type", params, "dns") or compare_attr("type", params, "named"):
        return DNS


class DNS(Application):
    template_rules = [
        TemplateRule(needsattr=None,
            template="app_infra_dns_default",
            unique_config="app_infra_dns_%s_default",
        ),
    ]

    def __new__(cls, params={}):
        return object.__new__(cls)

