#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import os
import imp
import inspect
from log import logger
from util import compare_attr


class DatasourceNotImplemented(Exception):
    pass

class DatasourceNotReady(Exception):
    # datasource is currently being updated
    pass

class DatasourceNotAvailable(Exception):
    pass

class DatasourceCorrupt(Exception):
    pass


class Datasource(object):

    my_type = 'datasource'
    class_factory = []

    def __init__(self, **params):
        #print "datasourceinit with", self.__class__
        if self.__class__ == Datasource:
            #print "generic ds", params
            newcls = self.__class__.get_class(params)
            if newcls:
                #print "i rebless anon datasource to", newcls, params
                self.__class__ = newcls
                self.__init__(**params)
            else:
                print "scheise", params
                logger.critical('datasource for %s is not implemented' % params)
                #print "i raise DatasourceNotImplemented"
                raise DatasourceNotImplemented
        else:
            setattr(self, 'name', params["name"])
            pass
        # i am a generic datasource
        # i find a suitable class
        # i rebless
        # i call __init__
        
    def open(self):
        pass

    def close(self):
        pass

    @classmethod
    def init_classes(cls, classpath):
        for p in [p for p in reversed(classpath) if os.path.exists(p) and os.path.isdir(p)]:
        #for p in [p for p in classpath if os.path.exists(p) and os.path.isdir(p)]:
            for module, path in [(item, p) for item in os.listdir(p) if item[-3:] == ".py" and item.startswith('datasource_')]:
                try:
                    #print "try ds", module, path
                    path = os.path.abspath(path)
                    fp, filename, data = imp.find_module(module.replace('.py', ''), [path])
                    toplevel = imp.load_module('', fp, '', ('py', 'r', imp.PY_SOURCE))
                    for cl in inspect.getmembers(toplevel, inspect.isfunction):
                        if cl[0] ==  "__ds_ident__":
                            cls.class_factory.append([path, module, cl[1]])
                except Exception, exp:
                    logger.critical("could not load datasource %s from %s: %s" % (module, path, exp))
                finally:
                    if fp:
                        fp.close()


    @classmethod
    def get_class(cls, params={}):
        #print "get_classhoho", cls, len(cls.class_factory), cls.class_factory
        for path, module, class_func in cls.class_factory:
            try:
                #print "try", path, module, class_func
                newcls = class_func(params)
                if newcls:
                    return newcls
            except Exception ,exp:
                print "Datasource.get_class exception", exp
                pass
        logger.debug("found no matching class for this datasource %s" % params)




