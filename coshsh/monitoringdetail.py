#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import os
import imp
import inspect
import logging
from urlparse import urlparse
import coshsh
from coshsh.item import Item
from coshsh.application import Application

logger = logging.getLogger('coshsh')

class MonitoringDetailNotImplemented(Exception):
    pass


class MonitoringDetail(coshsh.item.Item):
    class_factory = []
    lower_columns = ['application_name', 'application_type']

    def __init__(self, params):
        #print "Detail init", self.__class__, self.__class__.__name__, len(self.__class__.class_factory)
        if self.__class__.__name__ == "MonitoringDetail":
            for c in self.__class__.lower_columns:
                try:
                    params[c] = params[c].lower()
                except Exception:
                    if c in params:
                        params[c] = None
            newcls = self.__class__.get_class(params)
            if newcls:
                self.__class__ = newcls
                self.__init__(params)
            else:
                logger.info("monitoring detail of type %s for host %s / appl %s had a problem" % (params["monitoring_type"], params["host_name"], params["application_name"]))
                raise MonitoringDetailNotImplemented
        else:
            pass

    @classmethod
    def init_classes(cls, classpath):
        for p in [p for p in reversed(classpath) if os.path.exists(p) and os.path.isdir(p)]:
            for module, path in [(item, p) for item in os.listdir(p) if item[-3:] == ".py" and item.startswith('detail_')]:
                try:
                    path = os.path.abspath(path)
                    fp, filename, data = imp.find_module(module.replace('.py', ''), [path])
                    toplevel = imp.load_module('', fp, '', ('py', 'r', imp.PY_SOURCE))
                    for cl in inspect.getmembers(toplevel, inspect.isfunction):
                        if cl[0] ==  "__detail_ident__":
                            cls.class_factory.append([path, module, cl[1]])
                except Exception, e:
                    print e
                finally:
                    if fp:
                        fp.close()


    @classmethod
    def get_class(cls, params={}):
        #print "getclass from cache", cls, cls.__name__, len(cls.class_factory)
        for path, module, class_func in cls.class_factory:
            try:
                #print "get_class trys", path, module, class_func
                newcls = class_func(params)
                #print "get_class says", newcls
                if newcls:
                    return newcls
            except Exception:
                pass
        logger.debug("found no matching class for this monitoring detail %s" % params)
        return None


