"""Contact Type Plugins for Monitoring Notifications

Provides contact type classes for different notification channels.

Plugin Identification: type = "WEBREADWRITE", "WEBREADONLY", "MAIL", "SMS", "PHONE"

Purpose:
--------
Implements contact type plugins that define how monitoring notifications
are delivered and what permissions contacts have in the monitoring interface.

Contact Types:
--------------
1. ContactWeb (WEBREADWRITE/WEBREADONLY)
   - Web interface users
   - Read-only or read-write access
   - No external notifications (web dashboard only)

2. ContactMail (MAIL)
   - Email notifications
   - Customizable notification options
   - Host and service alerts via email

3. ContactSMS (SMS)
   - SMS/text message notifications
   - Short message format
   - Critical alerts via SMS

4. ContactPhone (PHONE)
   - Phone call notifications
   - Voice alerts
   - High-priority escalation

Input Format:
-------------
CSV Format (contacts.csv):
    contact_name,userid,alias,email,pager,address,type,notification_period
    admin,admin_user,Admin User,admin@example.com,,admin@example.com,MAIL,24x7
    ops,ops_user,Operations,ops@example.com,,ops@example.com,MAIL,workhours
    webuser,webuser,Web User,,,webuser,WEBREADWRITE,24x7
    readonly,readonly,Read Only,,,readonly,WEBREADONLY,24x7
    oncall,oncall,On Call,,,+1234567890,SMS,24x7
    emergency,emergency,Emergency,,,+1234567890,PHONE,24x7

ContactWeb Configuration:
--------------------------
WEBREADWRITE:
    - Web interface access with command submission
    - Can acknowledge alerts
    - Can submit commands
    - Can schedule downtime
    - No email/SMS notifications

WEBREADONLY:
    - Web interface access without commands
    - Can view alerts
    - Cannot submit commands
    - Cannot modify configuration
    - No email/SMS notifications

Attributes Set:
    contact_name = userid
    can_submit_commands = True (WEBREADWRITE) or False (WEBREADONLY)
    service_notification_options = "n" (none)
    host_notification_options = "n" (none)
    service_notification_commands = ["notify_by_nothing"]
    host_notification_commands = ["notify_by_nothing"]

ContactMail Configuration:
--------------------------
Email notifications with customizable options.

Attributes Set:
    contact_name = "mail_{name}_{notification_period}"
    email = address field from CSV
    service_notification_options = "w,c,u,r,f" (default)
        w = Warning
        c = Critical
        u = Unknown
        r = Recovery
        f = Flapping
    host_notification_options = "d,u,r,f" (default)
        d = Down
        u = Unreachable
        r = Recovery
        f = Flapping
    service_notification_commands = ["service-notify-by-email"]
    host_notification_commands = ["host-notify-by-email"]

Override notification options in CSV:
    Set service_notification_options attribute for custom values
    Set host_notification_options attribute for custom values

ContactSMS Configuration:
-------------------------
SMS/text notifications for mobile devices.

Attributes Set:
    contact_name = "sms_{name}_{notification_period}"
    pager = address field from CSV (phone number)
    can_submit_commands = False
    service_notification_options = "w,c,u,r,f" (default)
    host_notification_options = "d,u,r,f" (default)
    service_notification_commands = ["service-notify-by-sms"]
    host_notification_commands = ["host-notify-by-sms"]

SMS Best Practices:
    - Use for critical alerts only (avoid notification fatigue)
    - Configure escalation (email first, then SMS)
    - Keep message templates short
    - Verify phone number format (+country-code-number)

ContactPhone Configuration:
---------------------------
Phone call notifications for critical escalation.

Attributes Set:
    contact_name = "phone_{name}_{notification_period}"
    pager = address field from CSV (phone number)

Phone Best Practices:
    - Reserve for highest priority alerts
    - Use in escalation chains
    - Test phone notification system regularly
    - Consider time zones for on-call rotations

Notification Periods:
---------------------
Common periods:
    24x7: 24 hours, 7 days a week
    workhours: Business hours only (e.g., Mon-Fri 9-5)
    oncall: Variable schedule (requires timeperiod definition)
    never: Disable notifications

The notification period name is used in contact_name generation
to allow the same person to have different contacts for different
time periods:
    mail_admin_24x7 → Always notify
    mail_admin_workhours → Only during work hours

Template Usage:
---------------
Contacts are typically rendered in Nagios config using templates.

Example contact template:
    define contact {
        contact_name {{ contact.contact_name }}
        {% if contact.email %}
        email {{ contact.email }}
        {% endif %}
        {% if contact.pager %}
        pager {{ contact.pager }}
        {% endif %}
        service_notification_options {{ contact.service_notification_options }}
        host_notification_options {{ contact.host_notification_options }}
        service_notification_commands {{ contact.service_notification_commands|join(',') }}
        host_notification_commands {{ contact.host_notification_commands|join(',') }}
    }

Notification Commands:
----------------------
The notification command names reference Nagios command definitions
that must exist in your monitoring configuration:

    service-notify-by-email → Email service alerts
    host-notify-by-email → Email host alerts
    service-notify-by-sms → SMS service alerts
    host-notify-by-sms → SMS host alerts
    notify_by_nothing → Suppress notifications

These commands are defined in your Nagios commands.cfg or similar file.

Multi-Channel Notifications:
----------------------------
To send notifications via multiple channels, create multiple contact
entries for the same person with different types:

    admin,admin_user,Admin,admin@example.com,,admin@example.com,MAIL,24x7
    admin,admin_user,Admin,,,+1234567890,SMS,24x7

This creates two contacts (mail_admin_24x7 and sms_admin_24x7) that
both represent the same person but use different notification methods.

Classes:
--------
- ContactWeb: Web interface access (read-write or read-only)
- ContactMail: Email notifications
- ContactSMS: SMS notifications
- ContactPhone: Phone call notifications

Related Configuration:
----------------------
Contacts are typically associated with:
    - ContactGroups: Group contacts together
    - Notification periods: Define when to send notifications
    - Notification commands: Define how to send notifications
    - Hosts/Services: Assign contact groups to monitoring objects

Implementation Notes:
--------------------
The __mi_ident__() function uses "mi" (monitoring_item) instead of
standard prefixes because contacts existed before the plugin naming
convention was standardized.

The clean_name() method is inherited from Contact base class and
normalizes the contact name (removes special characters, etc.).

The notification_period.replace("/", "_") converts periods like
"24/7" to "24_7" for valid contact names.
"""

from __future__ import annotations
from typing import Optional, Dict, Any
import os
import coshsh
from coshsh.contact import Contact
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr, is_attr


def __mi_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify contact type from parameters.

    Args:
        params: Dictionary containing type and other parameters

    Returns:
        Appropriate Contact class based on type, or None
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
    """Web interface contact with read-write or read-only access.

    WEBREADWRITE: Can view and submit commands
    WEBREADONLY: Can only view, no commands
    """

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize web contact from parameters.

        Args:
            params: Dictionary with contact attributes including:
                - userid: Username for web login
                - type: WEBREADWRITE or WEBREADONLY

        Attributes Set:
            contact_name: Set to userid
            can_submit_commands: True for WEBREADWRITE, False for WEBREADONLY
            service_notification_options: "n" (no notifications)
            host_notification_options: "n" (no notifications)
            service_notification_commands: ["notify_by_nothing"]
            host_notification_commands: ["notify_by_nothing"]
        """
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
    """Email notification contact.

    Sends host and service alerts via email.
    """

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize mail contact from parameters.

        Args:
            params: Dictionary with contact attributes including:
                - name: Contact name
                - address: Email address
                - notification_period: When to send notifications

        Attributes Set:
            contact_name: "mail_{name}_{notification_period}"
            email: Email address from address field
            service_notification_options: "w,c,u,r,f" (default)
            host_notification_options: "d,u,r,f" (default)
            service_notification_commands: ["service-notify-by-email"]
            host_notification_commands: ["host-notify-by-email"]
        """
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
    """SMS notification contact.

    Sends host and service alerts via SMS/text message.
    """

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize SMS contact from parameters.

        Args:
            params: Dictionary with contact attributes including:
                - name: Contact name
                - address: Phone number
                - notification_period: When to send notifications

        Attributes Set:
            contact_name: "sms_{name}_{notification_period}"
            pager: Phone number from address field
            can_submit_commands: False
            service_notification_options: "w,c,u,r,f" (default)
            host_notification_options: "d,u,r,f" (default)
            service_notification_commands: ["service-notify-by-sms"]
            host_notification_commands: ["host-notify-by-sms"]
        """
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
    """Phone notification contact.

    Sends host and service alerts via phone call.
    """

    def __init__(self, params: Dict[str, Any]) -> None:
        """Initialize phone contact from parameters.

        Args:
            params: Dictionary with contact attributes including:
                - name: Contact name
                - address: Phone number
                - notification_period: When to send notifications

        Attributes Set:
            contact_name: "phone_{name}_{notification_period}"
            pager: Phone number from address field
        """
        self.clean_name()
        self.contact_name = "phone_" + self.name + "_" + self.notification_period.replace("/", "_")
        self.pager = self.address
