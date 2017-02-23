import os
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

    def wemustrepeat(self):
        self.SSHPORT = getattr(self, 'SSHPORT', 22)
        self.SSHUSER = getattr(self, 'SSHUSER', os.environ.get('OMD_ROLLOUT_USER_LINUX', 'mon'))
        self.SSHPATHPREFIX = getattr(self, 'SSHPATHPREFIX', os.environ.get('OMD_ROLLOUT_PATH_PREFIX', '.'))
        if not hasattr(self, 'custom_macros'):
            self.custom_macros = {}
        self.custom_macros['_SSHPORT'] = self.SSHPORT
        self.custom_macros['_SSHUSER'] = self.SSHUSER
        self.custom_macros['_SSHPATHPREFIX'] = self.SSHPATHPREFIX


class EmbeddedLinux(Linux):
    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None, 
            template="os_linux_heartbeat"),
    ]

