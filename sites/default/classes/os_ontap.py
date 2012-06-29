from operatingsystem import OperatingSystem
from templaterule import TemplateRule
from util import compare_attr

def __mi_ident__(params={}):
    if compare_attr("type", params, ".*ontap.*|.*netapp.*"):
        return ONTAP


class ONTAP(OperatingSystem):
    template_rules = [
        TemplateRule(needsattr=None, 
            template="os_ontap_default", 
        ),
        TemplateRule(needsattr='volumes', 
            template="os_ontap_fs", 
        ),
    ]

    def __new__(cls, params={}):
        return object.__new__(cls)

    def resolve_monitoring_details(self):
        super(ONTAP, self).resolve_monitoring_details()
        # build snmp login hashes
        if hasattr(self, "loginsnmpv3"):
            print "i have", self.loginsnmpv3
            x = self.loginsnmpv3.securitylevel + ":" + self.loginsnmpv3.securityname + ":" + self.loginsnmpv3.authprotocol + ":" + self.loginsnmpv3.authkey
            print x
        




