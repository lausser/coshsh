#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import os
import imp
import inspect
from util import compare_attr, is_attr
from log import logger
from item import Item
from templaterule import TemplateRule


class ApplicationNotImplemented(Exception):
    pass


class Application(Item):

    id = 1 #0 is reserved for host (primary node for parents)
    my_type = 'application'
    app_template = "app.tpl"
    class_factory = []


    # try __init__ as class factory with self.__class__ = 
    def __new__(cls, **params):
        #print "Application.__new__", params, len(cls.class_factory)
        try:
            newcls = cls.get_class(params)
            if not newcls:
                newcls = GenericApplication
            #print "i was Application.__new__ a", newcls.__name__
            return newcls.__new__(newcls, params)
        except ImportError as exc:
            logger.info("found no working code for application %s (%s)" % (params.get("type", "null_type"), exc))
            raise ApplicationNotImplemented
        except ApplicationNotImplemented as exc:
            # was already logged in the lower class
            pass
        except Exception as exc:
            logger.info("found unknown application %s" % (params.get("type", "null_type"),))
            print "except is", type(exc), exc
            raise ApplicationNotImplemented

    def fingerprint(self):
        return "%s+%s+%s" % (self.host_name, self.name, self.type)

    def __init__(self, params={}):
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
        for p in [p for p in reversed(classpath) if os.path.exists(p) and os.path.isdir(p)]:
            for module, path in [(item, p) for item in os.listdir(p) if item[-3:] == ".py" and (item.startswith('app_') or item.startswith('os_'))]:
                try:
                    path = os.path.abspath(path)
                    fp, filename, data = imp.find_module(module.replace('.py', ''), [path])
                    toplevel = imp.load_module('', fp, '', ('py', 'r', imp.PY_SOURCE))
                    for cl in inspect.getmembers(toplevel, inspect.isfunction):
                        if cl[0] ==  "__mi_ident__":
                            cls.class_factory.append([path, module, cl[1]])
                except Exception, e:
                    print e
                finally:
                    if fp:
                        fp.close()


    @classmethod
    def get_class(cls, params={}):
        for class_func in cls.class_factory:
            try:
                newcls = class_func(params)
                if newcls:
                    return newcls
            except Exception:
                pass
        logger.debug("found no matching class for this monitoring item %s" % params)


class GenericApplication(Application):
    template_rules = [
        TemplateRule(needsattr=None, 
            template="app_generic_default",
            unique_attr='name', unique_config="app_%s_default"),
    ]

    def __new__(cls, params={}):
        return object.__new__(cls)

    def __init__(self, params={}):
        self.name = params["name"]
        super(GenericApplication, self).__init__(params)

    def render(self):
        # Maybe we find some processes, ports, filesystems in the
        # monitoring_details so we can output generic services
        if (hasattr(self, "processes") and self.processes) or (hasattr(self, "filesystems") and self.filesystems) or (hasattr(self, "ports") and self.ports):
            super(GenericApplication, self).render()
        else:
            return ()


