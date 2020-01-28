import re
import coshsh
from coshsh.application import Application
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr

def __mi_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "ds3500"):
        return IBMDS3500


class IBMDS3500(coshsh.application.Application):
    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr='trap_events',
            template="os_ds3500_traps"),
    ]
    implements_mibs = ['SM10-R2-MIB']

