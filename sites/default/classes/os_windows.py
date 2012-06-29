from operatingsystem import OperatingSystem
from templaterule import TemplateRule
from util import compare_attr

def __mi_ident__(params={}):
    if compare_attr("type", params, ".*windows.*"):
        return Windows


class Windows(OperatingSystem):
    template_rules = [
        TemplateRule(needsattr=None, 
            template="os_windows_default"),
        TemplateRule(needsattr="filesystems", 
            template="os_windows_fs"),
    ]

    def __new__(cls, params={}):
        return object.__new__(cls)


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


