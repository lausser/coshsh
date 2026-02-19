#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Notification contact model for coshsh-generated monitoring configuration.

Sole responsibility: represent a single notification recipient (a person or
system that receives alerts) and produce the corresponding monitoring
configuration via Jinja2 templates.

Does NOT: send notifications, manage notification routing, or define
escalation policies.  Those concerns belong to the monitoring engine and
its runtime configuration.

Key classes:
    Contact        -- Base class using the class-factory pattern: when
                      instantiated it inspects *params* and re-classes itself
                      to a recipe-provided subclass (or GenericContact).
    GenericContact -- Fallback subclass used when no recipe-specific contact
                      class matches the input parameters.

AI agent note: Contact uses the same class-factory mechanism as Application.
The factory lookup happens inside ``__init__`` by calling ``get_class(params)``
(inherited from CoshshDatainterface).  After re-classing, ``__init__`` is
called a second time on the new class.
"""

import logging
import coshsh

logger = logging.getLogger('coshsh')


class Contact(coshsh.item.Item):

    # WHY: class_factory is populated at runtime by CoshshDatainterface when
    # recipe class directories are scanned for files matching
    # class_file_prefixes.  Each discovered module's __mi_ident__ function
    # decides whether it handles a given set of contact params.
    class_factory = []
    class_file_prefixes = ["contact_", "contact.py"]
    class_file_ident_function = "__mi_ident__"
    # WHY: my_type is set to "application" (not "contact") because the
    # class-factory discovery reuses the same mechanism that Application
    # uses; the value is only relevant for the factory lookup path.
    my_type = "application"

    lower_columns = []

    template_rules = [
        coshsh.templaterule.TemplateRule(
            template="contact",
            self_name="contact",
            unique_attr="contact_name", unique_config="contact_%s",
        )
    ]

    def __init__(self, params):
        """Create a Contact, re-classing to a recipe-specific subclass if one matches.

        When called on the base Contact class, this method:
        1. Lower-cases columns listed in ``lower_columns``.
        2. Sets safe defaults for all address/pager/email fields.
        3. Looks up a matching subclass via the class factory.
        4. Falls back to GenericContact if no subclass matches.
        5. Fills in host/service notification periods from the generic
           ``notification_period`` if the specific columns are absent.

        When called on an already-resolved subclass (i.e. ``self.__class__``
        is not Contact), this is a no-op so that the subclass ``__init__``
        can run without re-triggering the factory.

        Args:
            params: dict of datasource columns (must include at least
                    ``name``, ``type``, ``userid``, ``notification_period``).
        """
        #print "Contact init", self.__class__, self.__class__.__name__, len(self.__class__.class_factory)
        if self.__class__.__name__ == "Contact":
            for c in self.__class__.lower_columns:
                try:
                    params[c] = params[c].lower()
                except Exception:
                    if c in params:
                        params[c] = None
            self.email = None
            self.pager = None
            self.address1 = None
            self.address2 = None
            self.address3 = None
            self.address4 = None
            self.address5 = None
            self.address6 = None
            self.can_submit_commands = False
            self.contactgroups = []
            self.custom_macros = {}
            self.templates = []
            newcls = self.__class__.get_class(params)
            if newcls:
                self.__class__ = newcls
                super(Contact, self).__init__(params)
                self.__init__(params)
                self.fingerprint = lambda s=self:s.__class__.fingerprint(params)
            else:
                logger.debug('this will be Generic %s' % params)
                self.__class__ = GenericContact
                self.contactgroups = []
                super(Contact, self).__init__(params)
                self.__init__(params)
                self.fingerprint = lambda s=self:s.__class__.fingerprint(params)
            if not hasattr(self, 'host_notification_period') or not self.host_notification_period:
                self.host_notification_period = self.notification_period
                logger.debug('no column host_notification_period found use notification_period instead')
            if not hasattr(self, 'service_notification_period') or not self.service_notification_period:
                self.service_notification_period = self.notification_period
                logger.debug('no column service_notification_period found use notification_period instead')
        else:
            pass

    def clean_name(self):
        """Replace German umlauts and sharp-s in ``self.name`` with ASCII equivalents.

        # WHY: Nagios/Icinga contact_name fields must be plain ASCII.
        # German datasources frequently contain names like "Müller" or
        # "Größe".  Stripping umlauts here (ü->ue, ß->ss, etc.) keeps
        # the generated contact_name valid for the monitoring engine
        # while remaining human-readable.
        """
        self.name = coshsh.util.clean_umlauts(self.name)

    @classmethod
    def fingerprint(self, params):
        """Return a unique identity string for de-duplication in the recipe's object store.

        The fingerprint is composed as ``name+type+address+userid``, joined
        by ``+``.  For example: ``lausser+WEBREADONLY+me@example.com+lausser``.

        # WHY: All four fields are needed because the same person (name)
        # may have multiple notification types (e.g. email vs. SMS), each
        # with a different address, and potentially different userids.
        # Using only name would collapse those into one contact.
        """
        return "+".join([str(params.get(a, "")) for a in ["name", "type", "address", "userid"]])

    def __str__(self):
        """Return a human-readable summary including the fingerprint fields and group memberships."""
        fipri = " ".join([str(getattr(self, a, "")) for a in ["name", "type", "address", "userid"]])
        grps = ",".join(self.contactgroups)
        return str("contact %s groups (%s)" % (fipri, grps))


class GenericContact(Contact):
    """Fallback contact subclass used when no recipe-specific class matches."""

    def __init__(self, params={}):
        super(GenericContact, self).__init__(params)
        self.clean_name()
        self.contact_name = "unknown_" + self.type + "_" + self.name + "_" + self.notification_period.replace("/", "_")

    def render(self, template_cache, jinja2, recipe):
        """Render the contact configuration using the default ``contact`` template.

        Currently delegates directly to the parent render(). The override
        exists as a hook for future attribute enrichment, mirroring the
        pattern in GenericApplication.
        """
        # Maybe we find some useful attributes in the future which can
        # be used like in GenericApplication
        return super(GenericContact, self).render(template_cache, jinja2, recipe)

