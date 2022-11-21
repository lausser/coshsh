import coshsh
from coshsh.application import Application
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr

def __mi_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "mysql"):
        return MySQL


class MySQL(coshsh.application.Application):
    template_rules = [
        coshsh.templaterule.TemplateRule(
            template="app_db_mysql_default",
            unique_config="app_db_mysql_%s_default",
        )
    ]

    def __init__(self, params={}):
        super(MySQL, self).__init__(params)
        self.access = "remote"
        self.port = 3306

    def wemustrepeat(self):
        if "cluster" in self.host_name:
            self.host.hostgroups.append("mysql-clusters")
