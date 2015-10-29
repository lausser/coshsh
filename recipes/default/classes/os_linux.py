import coshsh
from coshsh.application import Application
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr

def __mi_ident__(params={}):
    if coshsh.util.compare_attr("type", params, ".*red\s*hat.*|.*rhel.*|.*sles.*|.*linux.*|.*limux.*|.*debian.*|.*ubuntu.*|.*centos.*"):
        return Linux


class Linux(coshsh.application.Application):
    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None, 
            template="os_linux_default"),
        coshsh.templaterule.TemplateRule(needsattr="filesystems", 
            template="os_linux_fs"),
    ]

    def __new__(cls, params={}):
        if coshsh.util.compare_attr("version", params, ".*embedded.*"):
            cls = EmbeddedLinux
        return object.__new__(cls)


class RedHat(Linux):
    pass


class SuSE(Linux):
    pass


class EmbeddedLinux(Linux):
    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None, 
            template="os_linux_heartbeat"),
    ]

