import re
import coshsh
from coshsh.application import Application
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr

def __mi_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "Paloalto"):
        return Unity


class Unity(coshsh.application.Application):
    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None,
            template="os_paloalto_default"),
        coshsh.templaterule.TemplateRule(needsattr='trap_events',
            template="os_paloalto_traps"),
    ]
    implements_mibs = ['PAN-TRAPS-MIB:PAN-TRAPS-7-MIB']

    def wemustrepeat(self):
        if hasattr(self, "version"):
            self.implements_mibs = ['PAN-TRAPS-MIB:PAN-TRAPS-'+str(self.version)+'-MIB']
