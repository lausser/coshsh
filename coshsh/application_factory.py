#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import os
import inspect
from util import compare_attr, is_attr
from coshsh.log import logger
from generator import Generator
from item import Item
from templaterule import TemplateRule


class ApplicationNotImplemented(Exception):
    pass


class ApplicationFactory(Item):

    id = 1 #0 is reserved for host (primary node for parents)
    my_type = 'application'
    app_template = "app.tpl"


    # try __init__ as class factory with self.__class__ = 
    def x__new__(cls, params={}):
        #print "Application.__new__", params, len(cls.class_factory)
        try:
            if compare_attr("name", params, "os"):
                from operatingsystem import OperatingSystem
                newcls = OperatingSystem
            else:
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
        if not params or 'classpath' in params:
            try:
                classpath = params['classpath']
            except Exception:
                classpath = [os.path.join(os.path.dirname(__file__), '..', 'sites', 'default', 'classes')]
            self.class_cache = []
            self.init_classes(classpath)
        else:
            newcls = cls.get_class(params)
            if not newcls:
                self.__class__ = newcls
            super(ApplicationFactory, self).__init__(params)
            self.contact_groups = []

    def create_servicegroups(self):
        pass

    def create_contacts(self):
        pass

    def create_templates(self):
        pass

    def init_classes(self, classpath):
        print "init", classpath
        for module in  [item for sublist in [os.listdir(p) for p in classpath if os.path.exists(p) and os.path.isdir(p)] for item in sublist if item[-3:] == ".py"]:
            print "inspect", module
            toplevel = __import__(module[:-3], locals(), globals())
            for cl in inspect.getmembers(toplevel, inspect.isfunction):
                if cl[0] ==  "__mi_ident__":
                    self.class_cache.append(cl[1])
                    print "cache", cl[1]


    @classmethod
    def get_class(cls, params={}):
        print Generator.class_factory
        for class_func in cls.class_factory:
            print "it is class", class_func
            try:
                newcls = class_func(params)
                if newcls:
                    return newcls
            except Exception:
                pass
        logger.debug("found no matching class for this monitoring item %s" % params)



