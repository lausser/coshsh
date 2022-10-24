import coshsh
from coshsh.application import Application
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr

def __mi_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "appwithblanksbool"):
        return AppWithBlanksBool
    elif coshsh.util.compare_attr("type", params, "appwithblankslist"):
        return AppWithBlanksList
    elif coshsh.util.compare_attr("type", params, "appwithblanks"):
        return AppWithBlanks


class AppWithBlanks(coshsh.application.Application):
    pass


class AppWithBlanksBool(coshsh.application.Application):
    dont_strip_attributes = True


class AppWithBlanksList(coshsh.application.Application):
    dont_strip_attributes = ["prefix", "suffix"]

