from monitoring_detail import MonitoringDetail
from application import Application
from templaterule import TemplateRule
from util import compare_attr

def __mi_ident__(params={}):
    if compare_attr("type", params, "oracle"):
        return Oracle


class Oracle(Application):
    template_rules = [
        TemplateRule(needsattr=None,
            template="app_db_oracle_default",
            unique_attr='sid', unique_config="app_db_oracle_default_%s",
        ),
        #TemplateRule(needsattr='tablespaces',
        #    template="app_db_oracle_tbs",
        #    unique_attr='sid', unique_config="app_db_oracle_tbs_%s", 
        #),
        TemplateRule(needsattr='tags', isattr='mon_tbs',
            template="app_db_oracle_tbs",
            unique_attr='sid', unique_config="app_db_oracle_tbs_%s", 
        ),
        TemplateRule(needsattr='tags', isattr='mon_quality',
            template="app_db_oracle_quality",
            unique_attr='sid', unique_config="app_db_oracle_quality_%s", 
        ),
        TemplateRule(needsattr='tags', isattr='mon_perf',
            template="app_db_oracle_perf",
            unique_attr='sid', unique_config="app_db_oracle_perf_%s", 
        ),
        TemplateRule(needsattr='tags', isattr='mon_usage',
            template="app_db_oracle_usage",
            unique_attr='sid', unique_config="app_db_oracle_usage_%s", 
        ),
    ]

    def __new__(cls, params={}):
        if params["version"] == "8.1.7":
            newcls = Oracle8
        else:
            newcls = cls
        return object.__new__(newcls)

    def __init__(self, params={}):
        super(Oracle, self).__init__(params)
        # better use sid in the template
        self.sid = self.name
        self.unique_name = '_' + self.sid
        self.access = "remote"
        #self.login = { "username" : None, "password" : None }
        #self.monitoring_details.append(MonitoringDetail({ 'monitoring_type': 'LOGIN' }))
        self.tags = []

    def wemustrepeat(self):
        if not hasattr(self, 'login') or not self.login.username:
            print "has no login yet"
            if hasattr(self, 'urls') and self.urls[0].username:
                print "has url instead"
                self.monitoring_details.append(MonitoringDetail({ 'monitoring_type': 'LOGIN', 'monitoring_0': self.urls[0].username, 'monitoring_1': self.urls[0].password }))
        self.resolve_monitoring_details()


class Oracle8(Oracle):
    pass




