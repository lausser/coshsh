from application import Application
from templaterule import TemplateRule
from util import compare_attr

def __mi_ident__(params={}):
    if compare_attr("type", params, ".*windows.*"):
        return Windows


class Windows(Application):
    template_rules = [
        TemplateRule(needsattr=None, 
            template="os_windows_default"),
        TemplateRule(needsattr="filesystems",
            template="os_windows_fs"),
        TemplateRule(needsattr="filesystems",
            template="nrpe_os_windows_fs", suffix="conf"),
    ]


