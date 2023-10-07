#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import sys
import os
import logging
import coshsh

logger = logging.getLogger('coshsh')


class Application(coshsh.item.Item):

    class_factory = []
    class_file_prefixes = ["app_", "os_"]
    class_file_ident_function = "__mi_ident__"
    my_type = "application"
    lower_columns = ['name', 'type', 'component', 'version', 'patchlevel']

    def __init__(self, params):
        #print "Application init", self.__class__, self.__class__.__name__, len(self.__class__.class_factory)
        if self.__class__.__name__ == "Application":
            for c in self.__class__.lower_columns:
                try:
                    params[c] = params[c].lower()
                except Exception:
                    if c in params:
                        params[c] = None
            newcls = self.__class__.get_class(params)
            if newcls:
                self.__class__ = newcls
                self.contact_groups = []
                super(Application, self).__init__(params)
                self.__init__(params)
                self.fingerprint = lambda s=self:s.__class__.fingerprint(params)
            else:
                logger.debug('this will be Generic %s' % params)
                self.__class__ = GenericApplication
                self.contact_groups = []
                super(Application, self).__init__(params)
                self.__init__(params)
                self.fingerprint = lambda s=self:s.__class__.fingerprint(params)
        else:
            pass

    @classmethod
    def fingerprint(self, params={}):
        return "%s+%s+%s" % (params["host_name"], params["name"], params["type"])

    def create_servicegroups(self):
        pass

    def create_contacts(self):
        pass

    def create_templates(self):
        pass


class GenericApplication(Application):

    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None, 
            template="app_generic_default",
            unique_attr=['type', 'name'], unique_config="app_%s_%s_default"),
    ]

    def __init__(self, params={}):
        super(GenericApplication, self).__init__(params)

    def render(self, template_cache, jinja2, recipe):
        # Maybe we find some processes, ports, filesystems in the
        # monitoring_details so we can output generic services
        if (hasattr(self, "processes") and self.processes) or (hasattr(self, "filesystems") and self.filesystems) or (hasattr(self, "cfgfiles") and self.cfgfiles) or (hasattr(self, "files") and self.files) or (hasattr(self, "ports") and self.ports) or (hasattr(self, "urls") and self.urls) or (hasattr(self, "services") and self.services):
            return super(GenericApplication, self).render(template_cache, jinja2, recipe)
        else:
            return 0

