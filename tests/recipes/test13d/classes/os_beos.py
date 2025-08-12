import coshsh

def __mi_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "beos"):
        return BeOS


class BeOS(coshsh.application.Application):
    marker = "department"
    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None, 
            template="os_beos_default"),
    ]

