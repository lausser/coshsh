#from application import Application
#from templaterule import TemplateRule
#from util import compare_attr
import coshsh
from coshsh.application import Application

def __mi_ident__(params={}):
    if compare_attr("type", params, ".*red\s*hat.*|.*sles.*|.*linux.*|.*limux.*|.*debian.*|.*ubuntu.*|.*centos.*"):
        return Linux


class Linux(Application):
    template_rules = [
        TemplateRule(needsattr=None, 
            template="os_linux_default"),
        TemplateRule(needsattr="filesystems", 
            template="os_linux_fs"),
    ]

    def __new__(cls, params={}):
        if compare_attr("version", params, ".*embedded.*"):
            cls = EmbeddedLinux
        return object.__new__(cls)

    def __init__(self, params):
        self.mycorp_linux = True


class RedHat(Linux):
    pass


class SuSE(Linux):
    pass


class EmbeddedLinux(Linux):
    template_rules = [
        TemplateRule(needsattr=None, 
            template="os_linux_heartbeat"),
    ]

