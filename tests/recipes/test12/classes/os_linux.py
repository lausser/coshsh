import coshsh
from coshsh.application import Application
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr

def __mi_ident__(params={}):
    if coshsh.util.compare_attr("type", params, r".*red\s*hat.*|.*sles.*|.*linux.*|.*limux.*|.*debian.*|.*ubuntu.*|.*centos.*"):
        return Linux


class Linux(Application):
    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None, 
            template="os_linux_default"),
        coshsh.templaterule.TemplateRule(needsattr="filesystems", 
            template="os_linux_fs"),
    ]

