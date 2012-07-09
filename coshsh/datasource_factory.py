#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import os
import sys
import inspect
from util import compare_attr, is_attr
from coshsh.log import logger
from item import Item
from templaterule import TemplateRule


class DatasourceNotImplemented(Exception):
    pass

class DatasourceNotReady(Exception):
    # datasource is currently being updated
    pass

class DatasourceNotAvailable(Exception):
    pass


class DatasourceFactory(object):

    my_type = 'datasource'

    def __init__(self, **params):
        print "init is params", params
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

    def init_classes(self, classpath):
        print "init", classpath
        #self.set_site_sys_path()
        for p in [p for p in classpath if os.path.exists(p) and os.path.isdir(p)]:
            sys.path.insert(0, p)
            print "prepend", p
            for module, path in [(item, p) for item in os.listdir(p) if item[-3:] == ".py" and item.startswith('datasource_')]:
                toplevel = __import__(module[:-3], locals(), globals())
                for cl in inspect.getmembers(toplevel, inspect.isfunction):
                    if cl[0] ==  "__ds_ident__":
                        self.class_cache.append([path, cl[1]])
                        print "cache", path, module, cl[1]
            
        for p in [p for p in classpath if os.path.exists(p) and os.path.isdir(p)]:
            del sys.path[-1]

        for module, path in  [(item, p) for sublist in [os.listdir(p) for p in classpath if os.path.exists(p) and os.path.isdir(p)] for item in sublist if item[-3:] == ".py" and item.startswith('datasource_')]:
            print "inspect", module
        if cplen == 1:
            del sys.path[-1]
        elif cplen == 2:
            del sys.path[-1]
            del sys.path[-1]



    def get_datasource(self, **params):
        print "new datasource", params
        try:
            newcls = self.get_class(params)
            if newcls:
                return newcls.__new__(newcls, params)
            else:
                print "i force a raise"
                raise DatasourceNotImplemented
        except ImportError as exc:
            logger.info("found no working code for application %s (%s)" % (params.get("type", "null_type"), exc))
            raise ApplicationNotImplemented
        except Exception as exc:
            logger.info("found unknown datasource %s" % (params.get("type", "null_type"),))
            print exc
            print "__new__ got", params
            raise DatasourceNotImplemented

    def get_class(self, params={}):
        goodclasses = []
        for class_func in self.class_cache:
            print "i try from cache", class_func, params
            try:
                newcls = class_func(params)
                if newcls:
                    print "news clas", newcls
                    return newcls
            except Exception:
                pass
        logger.debug("found no matching class for this datasource %s" % params)



