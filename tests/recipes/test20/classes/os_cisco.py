import coshsh
from coshsh.application import Application
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr, is_attr

def __mi_ident__(params={}):
    if is_attr("name", params, "os") and compare_attr("type", params, "(.*cisco.*|.*ios.*)"):
        return CiscoIOS


class CiscoIOS(Application):
    template_rules = [
        TemplateRule(needsattr=None,
            template="os_ios_default",
        ),
        TemplateRule(needsattr='interfaces',
            template="os_ios_if",
        ),
        TemplateRule(needsattr=None,
            template="exporter", suffix="json", for_tool="prometheus",
            unique_config="snmp_%s", unique_attr="host_name"
        ),
    ]


