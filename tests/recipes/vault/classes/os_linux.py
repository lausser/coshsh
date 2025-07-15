import coshsh

def __mi_ident__(params={}):
    if coshsh.util.compare_attr("type", params, r".*red\s*hat.*|.*sles.*|.*linux.*|.*limux.*|.*debian.*|.*ubuntu.*|.*centos.*"):
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

    def __init__(self, params):
        self.test4_linux = True


class RedHat(Linux):
    pass


class SuSE(Linux):
    pass


class EmbeddedLinux(Linux):
    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None, 
            template="os_linux_heartbeat"),
    ]

