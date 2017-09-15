import os
import coshsh
from coshsh.contact import Contact
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr, is_attr

def __mi_ident__(params={}):
    if coshsh.util.is_attr("type", params, "MYTICKETTOOL"):
        return ContactMyTicketTool


class ContactMyTicketTool(coshsh.contact.Contact):

    def __init__(self, params):
        self.clean_name()
        self.contact_name = self.userid
        self.queue_id = self.address
        self.service_notification_options = "w,c"
        self.host_notification_options = "w,c"
        self.service_notification_commands = ["service-notify-by-msend"]
        self.host_notification_commands = ["host-notify-by-msend"]



