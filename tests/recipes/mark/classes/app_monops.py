from builtins import super
import coshsh
from coshsh.application import Application
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr
 
def __mi_ident__(params={}):
    print("cCCCCCCCheck this {}".format(params))
    if coshsh.util.compare_attr("type", params, "monops_timeperiods_dummy_application"):
        return MonopsTimeperiodsApplication
 
class MonopsTimeperiodsApplication(Application):
    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None,
            template="timeperiods_monops",
        ),
    ]
    #timeperiod_class = MonopsTimeperiod
 
    def __init__(self, params={}):
        super().__init__(params)
        self.timeperiods = []

