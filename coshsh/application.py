#!/usr/bin/env python
#-*- encoding: utf-8 -*-
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
from coshsh.util import compare_attr, is_attr
from coshsh.item import Item
from coshsh.templaterule import TemplateRule

logger = logging.getLogger('coshsh')

class ApplicationNotImplemented(Exception):
    pass


class Application(coshsh.item.Item):

    id = 1 #0 is reserved for host (primary node for parents)
    my_type = 'application'
    app_template = "app.tpl"
    class_factory = []
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
                #raise ApplicationNotImplemented
                self.fingerprint = lambda s=self:s.__class__.fingerprint(params)
        else:
            pass

    @classmethod
    def fingerprint(self, params={}):
        return "%s+%s+%s" % (params["host_name"], params["name"], params["type"])

    def _i_init__(self, params={}):
        super(Application, self).__init__(params)
        self.contact_groups = []

    def create_servicegroups(self):
        pass

    def create_contacts(self):
        pass

    def create_templates(self):
        pass

    @classmethod
    def init_classes(cls, classpath):
        sys.dont_write_bytecode = True
        for p in [p for p in reversed(classpath) if os.path.exists(p) and os.path.isdir(p)]:
            for module, path in [(item, p) for item in os.listdir(p) if item[-3:] == ".py" and (item.startswith('app_') or item.startswith('os_'))]:
                try:
                    path = os.path.abspath(path)
                    fp, filename, data = imp.find_module(module.replace('.py', ''), [path])
                    toplevel = imp.load_source(module.replace(".py", ""), filename)
                    for cl in inspect.getmembers(toplevel, inspect.isfunction):
                        if cl[0] ==  "__mi_ident__":
                            cls.class_factory.append([path, module, cl[1]])
                except Exception, e:
                    print e
                finally:
                    if fp:
                        fp.close()
        #print ".............fill %s / %s woth %s" % (cls, cls.__name__, cls.class_factory)


    @classmethod
    def get_class(cls, params={}):
        #print "getclass from cache", cls, cls.__name__,  cls.class_factory
        for path, module, class_func in cls.class_factory:
            try:
                #print "get_class trys", path, module, class_func
                newcls = class_func(params)
                #print "get_class says", newcls
                if newcls:
                    return newcls
            except Exception:
                pass
        logger.debug("found no matching class for this monitoring item %s" % params)
        return None


class GenericApplication(Application):
    template_rules = [
        TemplateRule(needsattr=None, 
            template="app_generic_default",
            unique_attr=['type', 'name'], unique_config="app_%s_%s_default"),
    ]

    def x__new__(cls, params={}):
        return object.__new__(cls)

    def __init__(self, params={}):
        self.name = params["name"]
        super(GenericApplication, self).__init__(params)

    def render(self, template_cache, jinja2):
        # Maybe we find some processes, ports, filesystems in the
        # monitoring_details so we can output generic services
        if (hasattr(self, "processes") and self.processes) or (hasattr(self, "filesystems") and self.filesystems) or (hasattr(self, "cfgfiles") and self.cfgfiles) or (hasattr(self, "files") and self.files) or (hasattr(self, "ports") and self.ports) or (hasattr(self, "urls") and self.urls):
            super(GenericApplication, self).render(template_cache, jinja2)
        else:
            return ()


