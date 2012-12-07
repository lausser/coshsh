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
        TemplateRule(needsattr=None,
            template="os_windows_kaas"),
    ]

    def __new__(cls, params={}):
        return object.__new__(cls)

    def __init__(self, params):
        self.test4_windows = True



class Windows2008(Windows):
    pass


class Windows2003(Windows):
    pass


class WindowsXP(Windows):
    pass


class WindowsXPSP1(Windows):
    pass


class WindowsVista(Windows):
    pass


class Windows7(Windows):
    pass


