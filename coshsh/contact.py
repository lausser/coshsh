#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Contact class for notification contacts.

This module defines the Contact class which represents a person or entity
that receives monitoring notifications. Contacts support plugin-based
specialization through the "reblessing" pattern.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List, Callable

import coshsh

logger = logging.getLogger('coshsh')


class Contact(coshsh.item.Item):
    """Represents a contact for monitoring notifications.

    A Contact is a person or system that receives notifications when
    monitoring events occur. Contacts support plugin-based specialization
    - the base Contact class can transform into specific contact types
    (e.g., EmailContact, SmsContact) based on the contact's attributes.

    Plugin Discovery ("Reblessing" Pattern):
        When a Contact is initialized, it searches for plugin classes
        that match the contact's attributes. If found, the object
        dynamically changes its class (self.__class__ = newcls) to
        become the specialized type. This allows custom contact types
        to be added without modifying core code.

    Attributes:
        contact_name: Unique identifier (auto-generated for generic contacts)
        name: Person's name
        email: Email address for notifications
        pager: Pager number or SMS address
        address1-6: Up to 6 additional contact addresses
        notification_period: Time period for notifications (e.g., "24x7")
        host_notification_period: Host-specific period (defaults to notification_period)
        service_notification_period: Service-specific period (defaults to notification_period)
        can_submit_commands: Whether contact can execute commands (default: False)
        contactgroups: List of contact group names
        custom_macros: Dictionary of custom Nagios macros
        templates: List of template names to inherit from

    Example Configuration:
        Contact({
            'name': 'John Doe',
            'type': 'email',
            'email': 'john.doe@example.com',
            'notification_period': '24x7',
            'address': 'john.doe@example.com'
        })

    Plugin Files:
        Plugin files should be named "contact_*.py" or "contact.py"
        and contain a __mi_ident__ function that returns True/False
        to indicate if the plugin handles the contact.

    Template Rendering:
        Renders to Nagios/Icinga contact configuration using the
        'contact' template.
    """

    # Plugin discovery configuration
    class_factory: List[tuple] = []
    class_file_prefixes = ["contact_", "contact.py"]
    class_file_ident_function = "__mi_ident__"
    my_type = "application"

    # Columns that should be lowercased (can be extended by subclasses)
    lower_columns: List[str] = []

    template_rules = [
        coshsh.templaterule.TemplateRule(
            template="contact",
            self_name="contact",
            unique_attr="contact_name",
            unique_config="contact_%s"
        )
    ]

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """Initialize a Contact with plugin-based specialization.

        This method implements the "reblessing" pattern:
        1. Normalizes lowercase columns
        2. Initializes default attributes
        3. Searches for matching plugin class via get_class()
        4. If found, changes self.__class__ to the plugin class
        5. Re-initializes as the specialized class

        Args:
            params: Dictionary of contact attributes including:
                - name: Required - person's name
                - type: Contact type (used by plugins)
                - email, pager: Contact methods
                - notification_period: When to notify
                - address, userid: Additional identifiers

        Note:
            The reblessing pattern allows this generic Contact to
            transform into specialized types (e.g., EmailContact)
            without requiring explicit factory methods.
        """
        params = params or {}

        # Only do initialization if we're the base Contact class
        # (prevents re-initialization during reblessing)
        if self.__class__.__name__ == "Contact":
            # Normalize lowercase columns
            for column in self.__class__.lower_columns:
                try:
                    if column in params and params[column] is not None:
                        params[column] = params[column].lower()
                except (AttributeError, TypeError):
                    if column in params:
                        params[column] = None

            # Initialize contact attributes
            self.email: Optional[str] = None
            self.pager: Optional[str] = None
            self.address1: Optional[str] = None
            self.address2: Optional[str] = None
            self.address3: Optional[str] = None
            self.address4: Optional[str] = None
            self.address5: Optional[str] = None
            self.address6: Optional[str] = None
            self.can_submit_commands: bool = False
            self.contactgroups: List[str] = []
            self.custom_macros: Dict[str, Any] = {}
            self.templates: List[str] = []

            # Search for specialized plugin class
            newcls = self.__class__.get_class(params)
            if newcls:
                # Rebless to specialized class
                self.__class__ = newcls
                super(Contact, self).__init__(params)
                self.__init__(params)
                self.fingerprint: Callable = lambda s=self: s.__class__.fingerprint(params)
            else:
                # No plugin found - use GenericContact
                logger.debug(f'this will be Generic {params}')
                self.__class__ = GenericContact
                self.contactgroups = []
                super(Contact, self).__init__(params)
                self.__init__(params)
                self.fingerprint = lambda s=self: s.__class__.fingerprint(params)

            # Set default notification periods if not specified
            if not hasattr(self, 'host_notification_period') or not self.host_notification_period:
                self.host_notification_period = self.notification_period
                logger.debug('no column host_notification_period found use notification_period instead')

            if not hasattr(self, 'service_notification_period') or not self.service_notification_period:
                self.service_notification_period = self.notification_period
                logger.debug('no column service_notification_period found use notification_period instead')
        else:
            # We've already been reblessed - subclass handles init
            pass

    def clean_name(self) -> None:
        """Clean special characters (umlauts) from contact name.

        Converts German umlauts and other special characters to ASCII
        equivalents for compatibility with monitoring systems that don't
        support Unicode.
        """
        self.name = coshsh.util.clean_umlauts(self.name)

    @classmethod
    def fingerprint(cls, params: Dict[str, Any]) -> str:
        """Return unique identifier for this contact.

        Args:
            params: Dictionary containing contact attributes

        Returns:
            Fingerprint string combining name, type, address, and userid

        Note:
            Used for deduplication. Multiple contact entries with the
            same fingerprint are considered the same contact.
        """
        return "+".join([str(params.get(a, "")) for a in ["name", "type", "address", "userid"]])

    def __str__(self) -> str:
        """Return human-readable string representation.

        Returns:
            String showing contact identifier and group memberships
        """
        fipri = " ".join([str(getattr(self, a, "")) for a in ["name", "type", "address", "userid"]])
        grps = ",".join(self.contactgroups)
        return f"contact {fipri} groups ({grps})"


class GenericContact(Contact):
    """Fallback contact class when no specialized plugin matches.

    This class is used when no plugin claims the contact via its
    __mi_ident__ function. It generates a synthetic contact_name
    from the contact's attributes.

    The contact_name format is:
        unknown_<type>_<name>_<notification_period>

    Example:
        unknown_email_john.doe_24x7
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """Initialize a GenericContact with auto-generated name.

        Args:
            params: Dictionary of contact attributes
        """
        params = params or {}
        super().__init__(params)

        # Clean special characters from name
        self.clean_name()

        # Generate synthetic contact_name
        # Replace "/" in notification_period to avoid path issues
        period = self.notification_period.replace("/", "_")
        self.contact_name = f"unknown_{self.type}_{self.name}_{period}"

    def render(
        self,
        template_cache: Any,
        jinja2: Any,
        recipe: Any
    ) -> str:
        """Render contact configuration.

        Args:
            template_cache: Template cache object
            jinja2: Jinja2 environment
            recipe: Recipe object containing configuration

        Returns:
            Rendered configuration string

        Note:
            Currently delegates to parent class. Future enhancements
            could add generic attribute handling similar to GenericApplication.
        """
        return super().render(template_cache, jinja2, recipe)
