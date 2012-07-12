#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import os
import sys
import imp
import inspect
import time
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

    def init_classes(self, classpath):
        for p in [p for p in reversed(classpath) if os.path.exists(p) and os.path.isdir(p)]:
            for module, path in [(item, p) for item in os.listdir(p) if item[-3:] == ".py" and item.startswith('datasource_')]:
                try:
                    path = os.path.abspath(path)
                    fp, filename, data = imp.find_module(module.replace('.py', ''), [path])

                    toplevel = imp.load_module('', fp, '', ('py', 'r', imp.PY_SOURCE))
                except Exception, e:
                    print e
                finally:
                    if fp:
                        fp.close()

                for cl in inspect.getmembers(toplevel, inspect.isfunction):
                    if cl[0] ==  "__ds_ident__":
                        self.class_cache.append([path, module, cl[1]])
                        print "i cache", path, cl
            
    def get_class(self, params={}):
        goodclasses = []
        for path, module, class_func in self.class_cache:
            try:
                newcls = class_func(params)
                if newcls:
                    return newcls
            except Exception, e:
                print "reload exp", e
                pass
        logger.debug("found no matching class for this datasource %s" % params)

    def get_datasource(self, **params):
        try:
            newcls = self.get_class(params)
            if newcls:
                newobj = newcls.__new__(newcls, params)
                newobj.__init__(**params)
                return newobj
            else:
                print "i force a raise"
                raise DatasourceNotImplemented
        except ImportError as exc:
            logger.info("found no working code for application %s (%s)" % (params.get("type", "null_type"), exc))
            raise ApplicationNotImplemented
        except Exception as exc:
            logger.info("found unknown datasource %s" % (params.get("type", "null_type"),))
            print "exception is", exc
            print "__new__ got", params
            raise DatasourceNotImplemented




