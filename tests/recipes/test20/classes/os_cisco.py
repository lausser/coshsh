import coshsh

def __mi_ident__(params={}):
    if coshsh.util.is_attr("name", params, "os") and coshsh.util.compare_attr("type", params, "(.*cisco.*|.*ios.*)"):
        return CiscoIOS


class CiscoIOS(coshsh.application.Application):
    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None,
            template="os_ios_default",
        ),
        coshsh.templaterule.TemplateRule(needsattr='interfaces',
            template="os_ios_if",
        ),
        coshsh.templaterule.TemplateRule(needsattr=None,
            template="exporter", suffix="json", for_tool="prometheus",
            unique_config="snmp_%s", unique_attr="host_name"
        ),
    ]


