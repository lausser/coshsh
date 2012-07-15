#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

print "--->datasource"
import os
import imp
import inspect
from log import logger
from util import compare_attr
print "<---datasource"


class DatasourceNotImplemented(Exception):
    pass

class DatasourceNotReady(Exception):
    # datasource is currently being updated
    pass

class DatasourceNotAvailable(Exception):
    pass


class Datasource(object):

    my_type = 'datasource'
    class_factory = []

    def __new__(cls, **params):
        print "new datasource", params
        try:
            newcls = cls.get_class(params)
            if newcls:
                print "i return", newcls, params
                return newcls(**params)
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

    def __init__(self, **params):
        if self.__class__ == Datasource:
            print "i am just a wrapper
            newcls = self.__class__.get_class(params)
            if newcls:
                print "i return", newcls, params
        else:
            pass
        # i am a generic datasource
        # i find a suitable class
        # i rebless
        # i call __init__
        

    @classmethod
    def init_classes(cls, classpath):
        for p in [p for p in reversed(classpath) if os.path.exists(p) and os.path.isdir(p)]:
        #for p in [p for p in classpath if os.path.exists(p) and os.path.isdir(p)]:
            for module, path in [(item, p) for item in os.listdir(p) if item[-3:] == ".py" and item.startswith('datasource_')]:
                try:
                    path = os.path.abspath(path)
                    fp, filename, data = imp.find_module(module.replace('.py', ''), [path])
                    toplevel = imp.load_module('', fp, '', ('py', 'r', imp.PY_SOURCE))
                    for cl in inspect.getmembers(toplevel, inspect.isfunction):
                        if cl[0] ==  "__ds_ident__":
                            cls.class_factory.append([path, module, cl[1]])
                except Exception, e:
                    print e
                finally:
                    if fp:
                        fp.close()


    @classmethod
    def get_class(cls, params={}):
        print "i am Datasource get_class", cls, cls.class_factory
        for path, module, class_func in cls.class_factory:
            try:
                print "Datasource.get_class", path, module, class_func
                newcls = class_func(params)
                if newcls:
                    print "ok Datasource", newcls
                    return newcls
            except Exception ,exp:
                print "Datasource.get_class exception", exp
                pass
        logger.debug("found no matching class for this monitoring item %s" % params)




