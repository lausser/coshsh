from application import Application
from templaterule import TemplateRule
from util import compare_attr

def __mi_ident__(params={}):
    print "try mysql"
    if compare_attr("type", params, "mysql"):
        return MySQL


class MySQL(Application):
    template_rules = [
        TemplateRule(
            template="app_db_mysql_default",
            unique_config="app_db_mysql_%s_default",
        )
    ]

    def __init__(self, params={}):
        super(MySQL, self).__init__(params)
        self.access = "remote"
        self.port = 3306
