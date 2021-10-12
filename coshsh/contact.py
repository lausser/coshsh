#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import sys
import os
import imp
import inspect
import logging
import coshsh
from coshsh.item import Item
from coshsh.templaterule import TemplateRule
from coshsh.util import clean_umlauts

logger = logging.getLogger('coshsh')


class Contact(coshsh.item.Item):

    class_factory = []
    lower_columns = []

    template_rules = [
        coshsh.templaterule.TemplateRule(
            template="contact",
            self_name="contact",
            unique_attr="contact_name", unique_config="contact_%s",
        )
    ]

    def __init__(self, params):
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
        self.name = clean_umlauts(self.name)


    @classmethod
    def fingerprint(self, params):
        return "+".join([str(params.get(a, "")) for a in ["name", "type", "address", "userid"]])

    def __str__(self):
        fipri = " ".join([str(getattr(self, a, "")) for a in ["name", "type", "address", "userid"]])
        grps = ",".join(self.contactgroups)
        return str("contact %s groups (%s)" % (fipri, grps))

    @classmethod
    def init_classes(cls, classpath):
        sys.dont_write_bytecode = True
        for p in [p for p in reversed(classpath) if os.path.exists(p) and os.path.isdir(p)]:
            for module, path in [(item, p) for item in sorted(os.listdir(p), reverse=True) if item[-3:] == ".py" and (item.startswith('contact_') or item == 'contact.py')]:
                try:
                    path = os.path.abspath(path)
                    fp, filename, data = imp.find_module(module.replace('.py', ''), [path])
                    toplevel = imp.load_source(module.replace(".py", ""), filename)
                    for cl in inspect.getmembers(toplevel, inspect.isfunction):
                        if cl[0] ==  "__mi_ident__":
                            cls.class_factory.append([path, module, cl[1]])
                except Exception as e:
                    print(e)
                finally:
                    if fp:
                        fp.close()
        #print ".............fill %s / %s woth %s" % (cls, cls.__name__, cls.class_factory)


    @classmethod
    def get_class(cls, params={}):
        #print "getclass from cache", cls, cls.__name__,  cls.class_factory
        for path, module, class_func in reversed(cls.class_factory):
            try:
                #print "get_class trys", path, module, class_func
                newcls = class_func(params)
                #print "get_class says", newcls.__module__, sys.modules[newcls.__module__].__file__
                if newcls:
                    return newcls
            except Exception:
                pass
        logger.debug("found no matching class for this monitoring item %s" % params)
        return None


class GenericContact(Contact):

    def __init__(self, params={}):
        super(GenericContact, self).__init__(params)
        self.clean_name()
        self.contact_name = "unknown_" + self.type + "_" + self.name + "_" + self.notification_period.replace("/", "_")

    def render(self, template_cache, jinja2, recipe):
        # Maybe we find some useful attributes in the future which can
        # be used like in GenericApplication
        super(GenericContact, self).render(template_cache, jinja2, recipe)

