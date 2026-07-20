#!/usr/bin/env python
# coshsh Application class skeleton.
# File name MUST be app_<something>.py.
# Place in a directory listed in the recipe's classes_dir.
#
# app_*.py files represent software running on a host (databases,
# middleware, custom services). os_*.py is the same mechanism but
# conventionally for the OS itself.

from coshsh.application import Application
from coshsh.templaterule import TemplateRule


def __mi_ident__(params={}):
    """Return the class for this app, or None to pass."""
    if params["type"].lower() == "oracle":
        return Oracle
    return None


class Oracle(Application):
    """Oracle DB server."""

    template_rules = Application.template_rules + [
        TemplateRule(
            template="app_db_oracle_default",
            unique_attr="name",
            unique_config="%s_%s_oracle",   # filename pattern: host_app_oracle
        ),
        TemplateRule(
            needsattr="tablespaces",
            template="app_db_oracle_tablespace",
        ),
        TemplateRule(
            needsattr="login",
            template="app_db_oracle_login",
            for_tool="check_oracle_health",  # routes via datarecipient for_tool
        ),
    ]

    # def __init__(self, params={}):
    #     super().__init__(params)
    #     # derive things from params if needed

    # def wemustrepeat(self):
    #     # called after all details attached; access self.tablespaces, etc.
    #     pass
