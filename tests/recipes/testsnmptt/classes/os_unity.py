import coshsh

def __mi_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "Unity"):
        return Unity


class Unity(coshsh.application.Application):
    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None,
            template="os_unity_default"),
        coshsh.templaterule.TemplateRule(needsattr='trap_events',
            template="os_unity_traps"),
    ]
    implements_mibs = ['Unity-MIB']

