#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import os
from util import compare_attr, is_attr
from coshsh.log import logger
from generator import Generator
from item import Item
from templaterule import TemplateRule


class ApplicationNotImplemented(Exception):
    pass


class Application(Item):

    id = 1 #0 is reserved for host (primary node for parents)
    my_type = 'application'
    app_template = "app.tpl"
    #class_factory = []

    def __new__(cls, params={}):
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
        super(Application, self).__init__(params)
        self.contact_groups = []

    def create_servicegroups(self):
        pass

    def create_contacts(self):
        pass

    def create_templates(self):
        pass

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



