#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import os
import imp
import inspect
from urlparse import urlparse
from log import logger
from application import Application


class MonitoringDetailNotImplemented(Exception):
    pass


class MonitoringDetail(object):
    class_factory = []

    def __init__(self, params):
        newcls = self.__class__.get_detail(params)
        if not newcls:
            logger.info("monitoring detail of type %s for host %s / appl %s had a problem" % (params["monitoring_type"], params["host_name"], params["application_name"]))
            raise MonitoringDetailNotImplemented
        self.__class__ = newcls
        newcls.__init__(self, params)

    def x__new__(cls, params):
        if params == None:
            params = {}
        newcls = cls.get_detail(params)
        if not newcls:
            logger.info("monitoring detail of type %s for host %s / appl %s had a problem" % (params["monitoring_type"], params["host_name"], params["application_name"]))
            raise MonitoringDetailNotImplemented
        print "newcls", newcls
        return newcls(params)
        return newcls.__new__(newcls, params)

    def fingerprint(self):
        return "%s+%s+%s" % (self.host_name, self.name, self.type)

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
        for class_func in cls.class_factory:
            try:
                newcls = class_func(params)
                if newcls:
                    return newcls
            except Exception:
                pass
        logger.debug("found no matching class for this monitoring detail %s" % params)


