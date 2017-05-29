import coshsh
from coshsh.application import Application
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr, is_attr

def __mi_ident__(params={}):
    if coshsh.util.is_attr("name", params, "os") and coshsh.util.compare_attr("type", params, ".*windows.*"):
        return Windows


class Windows(Application):
    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None, 
            template="os_windows_default"),
        coshsh.templaterule.TemplateRule(needsattr="filesystems", 
            template="os_windows_fs"),
    ]

    def wemustrepeat(self):
        self.NSCPORT = getattr(self, 'NSCPORT', 18443)
        self.NSCPASSWORD = getattr(self, 'NSCPASSWORD', 'secret')
        if not hasattr(self, 'custom_macros'):
            self.custom_macros = {}
        self.custom_macros['_NSCPORT'] = self.NSCPORT
        self.custom_macros['_NSCPASSWORD'] = self.NSCPASSWORD
        if not hasattr(self.host, 'custom_macros'):
            self.host.custom_macros = {}
        self.host.custom_macros['_NSCPORT'] = self.NSCPORT
        self.host.custom_macros['_NSCPASSWORD'] = self.NSCPASSWORD

