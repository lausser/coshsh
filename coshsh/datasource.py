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

    def __new__(cls, params):
        print "new datasource", params
        try:
            newcls = cls.get_class(params)
            if newcls:
                return newcls(params)
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

    @classmethod
    def init_classes(cls, classpath):
        print "i am Datasource init_classes", cls
        for p in [p for p in reversed(classpath) if os.path.exists(p) and os.path.isdir(p)]:
            for module, path in [(item, p) for item in os.listdir(p) if item[-3:] == ".py" and item.startswith('datasource_')]:
                try:
                    path = os.path.abspath(path)
                    fp, filename, data = imp.find_module(module.replace('.py', ''), [path])
                    toplevel = imp.load_module('', fp, '', ('py', 'r', imp.PY_SOURCE))
                    for cl in inspect.getmembers(toplevel, inspect.isfunction):
                        if cl[0] ==  "__ds_ident__":
                            cls.class_factory.append([path, module, cl[1]])
                            print "i cache", path, cl
                except Exception, e:
                    print e
                finally:
                    if fp:
                        fp.close()
        print "i was Datasource init_classes", cls.class_factory


    @classmethod
    def get_class(cls, params={}):
        print "i am Datasource get_class", cls, cls.class_factory
        for path, module, class_func in cls.class_factory:
            print "it is class", class_func
            try:
                newcls = class_func(params)
                if newcls:
                    
                    return newcls
            except Exception:
                pass
        logger.debug("found no matching class for this monitoring item %s" % params)




