import coshsh
from coshsh.application import Application
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr

def __mi_ident__(params={}):
    if coshsh.util.compare_attr("type", params, ".*windows.*"):
        return Windows


class Windows(coshsh.application.Application):
    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None, 
            template="os_windows_default"),
        coshsh.templaterule.TemplateRule(needsattr="filesystems",
            template="os_windows_fs"),
        coshsh.templaterule.TemplateRule(needsattr="filesystems",
            template="nrpe_os_windows_fs", suffix="conf"),
    ]


