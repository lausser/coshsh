#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import logging
from typing import Dict, Any
import coshsh

logger = logging.getLogger('coshsh')


class Contact(coshsh.item.Item):

    class_factory = []
    class_file_prefixes = ["contact_", "contact.py"]
    class_file_ident_function = "__mi_ident__"
    my_type = "application"

    lower_columns = []

    template_rules = [
        coshsh.templaterule.TemplateRule(
            template="contact",
            self_name="contact",
            unique_attr="contact_name", unique_config="contact_%s",
        )
    ]

    def __init__(self, params: Dict[str, Any]) -> None:
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
                super().__init__(params)
                self.__init__(params)
                self.fingerprint = lambda s=self:s.__class__.fingerprint(params)
            else:
                logger.debug(f'this will be Generic {params}')
                self.__class__ = GenericContact
                self.contactgroups = []
                super().__init__(params)
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

    def clean_name(self) -> None:
        self.name = coshsh.util.clean_umlauts(self.name)

    @classmethod
    def fingerprint(cls, params: Dict[str, Any]) -> str:
        return "+".join([str(params.get(a, "")) for a in ["name", "type", "address", "userid"]])

    def __str__(self) -> str:
        fipri = " ".join([str(getattr(self, a, "")) for a in ["name", "type", "address", "userid"]])
        grps = ",".join(self.contactgroups)
        return f"contact {fipri} groups ({grps})"


class GenericContact(Contact):

    def __init__(self, params={}):
        super(GenericContact, self).__init__(params)
        self.clean_name()
        self.contact_name = "unknown_" + self.type + "_" + self.name + "_" + self.notification_period.replace("/", "_")

    def render(self, template_cache, jinja2, recipe):
        # Maybe we find some useful attributes in the future which can
        # be used like in GenericApplication
        return super(GenericContact, self).render(template_cache, jinja2, recipe)

