"""Default contact implementations for various notification types.

Provides contact classes for different notification channels:
- Web contacts (read-only and read-write)
- Email contacts
- SMS contacts
- Phone contacts
"""

from __future__ import annotations

import os
from typing import Dict, Any, Optional, Type
import coshsh
from coshsh.contact import Contact
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr, is_attr


def __mi_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[Type[Contact]]:
    """Identify the appropriate contact class based on parameters.

    Args:
        params: Dictionary of contact parameters, must include 'type'

    Returns:
        Contact class for the specified type, or None if not recognized
    """
    if params is None:
        params = {}

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
    return None


class ContactWeb(coshsh.contact.Contact):
    """Web interface contact.

    Contacts that access monitoring via web interface. Can be read-only
    or read-write (with command submission capabilities).
    """

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize web contact.

        Args:
            params: Contact parameters including userid and type
        """
        self.clean_name()
        self.contact_name = self.userid
        self.can_submit_commands = (self.type == "WEBREADWRITE")
        self.service_notification_options = "n"
        self.host_notification_options = "n"
        self.service_notification_commands = ["notify_by_nothing"]
        self.host_notification_commands = ["notify_by_nothing"]


class ContactMail(coshsh.contact.Contact):
    """Email notification contact.

    Sends notifications via email using configured email address.
    """

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize email contact.

        Args:
            params: Contact parameters including name, address, and notification_period
        """
        self.clean_name()
        self.contact_name = f"mail_{self.name}_{self.notification_period.replace('/', '_')}"
        self.email = self.address
        if not hasattr(self, "service_notification_options"):
            self.service_notification_options = "w,c,u,r,f"
        if not hasattr(self, "host_notification_options"):
            self.host_notification_options = "d,u,r,f"
        self.service_notification_commands = ["service-notify-by-email"]
        self.host_notification_commands = ["host-notify-by-email"]


class ContactSMS(coshsh.contact.Contact):
    """SMS notification contact.

    Sends notifications via SMS using configured phone number.
    """

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize SMS contact.

        Args:
            params: Contact parameters including name, address, and notification_period
        """
        self.clean_name()
        self.contact_name = f"sms_{self.name}_{self.notification_period.replace('/', '_')}"
        self.pager = self.address
        self.can_submit_commands = False
        if not hasattr(self, "service_notification_options"):
            self.service_notification_options = "w,c,u,r,f"
        if not hasattr(self, "host_notification_options"):
            self.host_notification_options = "d,u,r,f"
        self.service_notification_commands = ["service-notify-by-sms"]
        self.host_notification_commands = ["host-notify-by-sms"]


class ContactPhone(coshsh.contact.Contact):
    """Phone notification contact.

    Sends notifications via phone call using configured phone number.
    """

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize phone contact.

        Args:
            params: Contact parameters including name, address, and notification_period
        """
        self.clean_name()
        self.contact_name = f"phone_{self.name}_{self.notification_period.replace('/', '_')}"
        self.pager = self.address


