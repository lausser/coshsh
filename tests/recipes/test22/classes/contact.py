import os
import coshsh
from coshsh.contact import Contact
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr, is_attr

def __mi_ident__(params={}):
    if coshsh.util.is_attr("type", params, "MYTICKETTOOL"):
        return ContactMyTicketTool
    elif coshsh.util.is_attr("type", params, "EXISTINGTEMPLATE"):
        return ContactExistingTemplate
    elif coshsh.util.is_attr("type", params, "EXISTINGTEMPLATE2"):
        return ContactExistingTemplate2


class ContactMyTicketTool(coshsh.contact.Contact):

    def __init__(self, params):
        self.clean_name()
        self.contact_name = self.userid
        self.queue_id = self.address
        self.service_notification_options = "w,c"
        self.host_notification_options = "w,c"
        self.service_notification_commands = ["service-notify-by-msend"]
        self.host_notification_commands = ["host-notify-by-msend"]


class ContactExistingTemplate(coshsh.contact.Contact):

    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None, 
            template="contact_using_a_known_template",
            self_name="contact",
            unique_attr="contact_name", unique_config="contact_%s",
        )
    ]

    def __init__(self, params):
        self.clean_name()
        self.contact_name = self.userid


class ContactExistingTemplate2(coshsh.contact.Contact):

    def __init__(self, params):
        self.clean_name()
        self.contact_name = self.userid

