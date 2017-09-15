import os
import coshsh
from coshsh.contact import Contact
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr, is_attr

def __mi_ident__(params={}):
    if coshsh.util.is_attr("type", params, "WEBREADWRITE"):
        return ContactWeb
    elif coshsh.util.is_attr("type", params, "WEBREADONLY"):
        return ContactWeb
    elif coshsh.util.is_attr("type", params, "MAIL"):
        return ContactMail
    elif coshsh.util.is_attr("type", params, "SMS"):
        return ContactSMS
    elif coshsh.util.is_attr("type", params, "PHONE"):
        return ContactPhone


class ContactWeb(coshsh.contact.Contact):

    def __init__(self, params):
        self.clean_name()
        self.contact_name = self.userid
        if self.type == "WEBREADWRITE":
            self.can_submit_commands = True
        else:
            self.can_submit_commands = False
        self.service_notification_options = "n"
        self.host_notification_options = "n"
        self.service_notification_commands = ["notify_by_nothing"]
        self.host_notification_commands = ["notify_by_nothing"]


class ContactMail(coshsh.contact.Contact):

    def __init__(self, params):
        self.clean_name()
        self.contact_name = "mail_" + self.name + "_" + self.notification_period.replace("/", "_")
        self.email = self.address
        if not hasattr(self, "service_notification_options"):
            setattr(self, "service_notification_options", "w,c,u,r,f")
        if not hasattr(self, "host_notification_options"):
            setattr(self, "host_notification_options", "d,u,r,f")
        self.service_notification_commands = ["service-notify-by-email"]
        self.host_notification_commands = ["host-notify-by-email"]


class ContactSMS(coshsh.contact.Contact):

    def __init__(self, params):
        self.clean_name()
        self.contact_name = "sms_" + self.name + "_" + self.notification_period.replace("/", "_")
        self.pager = self.address
        self.can_submit_commands = False
        if not hasattr(self, "service_notification_options"):
            setattr(self, "service_notification_options", "w,c,u,r,f")
        if not hasattr(self, "host_notification_options"):
            setattr(self, "host_notification_options", "d,u,r,f")
        self.service_notification_commands = ["service-notify-by-sms"]
        self.host_notification_commands = ["host-notify-by-sms"]


class ContactPhone(coshsh.contact.Contact):

    def __init__(self, params):
        self.clean_name()
        self.contact_name = "phone_" + self.name + "_" + self.notification_period.replace("/", "_")
        self.pager = self.address


