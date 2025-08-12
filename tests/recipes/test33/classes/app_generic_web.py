import coshsh

def __mi_ident__(params={}):
    if coshsh.util.compare_attr("type", params, ".*webapp.*"):
        return AppWeb


class AppWeb(coshsh.application.Application):
    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None, 
            template="app_generic_web"),
    ]

