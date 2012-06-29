from application import Application
from templaterule import TemplateRule
from util import compare_attr

def __mi_ident__(params={}):
    if compare_attr("type", params, "ldap") or compare_attr("type", params, "OPENLDAP"):
        return LDAP


class LDAP(Application):
    template_rules = [
        TemplateRule(needsattr=None,
            template="app_infra_ldap_default",
            unique_config="app_infra_ldap_%s_default",
        ),
        #TemplateRule(needsattr="False",
        #    template="app_infra_ad_perf",
        #    unique_config="app_infra_ad_%s_perf",
        #),
    ]

    def __new__(cls, params={}):
        return object.__new__(cls)



