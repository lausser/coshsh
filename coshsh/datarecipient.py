#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import os
import re
import imp
import inspect
import logging
from util import compare_attr, substenv

logger = logging.getLogger('coshsh')

class DatarecipientNotImplemented(Exception):
    pass

class DatarecipientNotReady(Exception):
    # datarecipient is currently being updated
    pass

class DatarecipientNotCurrent(Exception):
    # datarecipients was not updated lately.
    # it makes no sense to continue.
    pass

class DatarecipientNotAvailable(Exception):
    pass

class DatarecipientCorrupt(Exception):
    pass


class Datarecipient(object):

    my_type = 'datarecipient'
    class_factory = []

    def __init__(self, **params):
        #print "datarecipientinit with", self.__class__
        for key in params.iterkeys():
            params[key] = re.sub('%.*?%', substenv, params[key])
        if self.__class__ == Datarecipient:
            #print "generic ds", params
            newcls = self.__class__.get_class(params)
            if newcls:
                #print "i rebless anon datarecipient to", newcls, params
                self.__class__ = newcls
                self.__init__(**params)
            else:
                logger.critical('datarecipient for %s is not implemented' % params)
                #print "i raise DatarecipientNotImplemented"
                raise DatarecipientNotImplemented
        else:
            setattr(self, 'name', params["name"])
            self.objects = {}
            pass

    def load(self, filter=None, objects={}):
        logger.info('load items to %s' % (self.name, ))
        self.objects = objects

    def item_write_config(self, obj, dynamic_dir, objtype):
        my_target_dir = os.path.join(dynamic_dir, objtype)
        if not os.path.exists(my_target_dir):
            os.makedirs(my_target_dir)
        for file in obj.config_files:
            content = obj.config_files[file]
            with open(os.path.join(my_target_dir, file), "w") as f:
                f.write(content)

    def output(self, filter=None):
        for hostgroup in self.objects['hostgroups'].values():
            self.item_write_config(hostgroup, self.dynamic_dir, "hostgroups")
        for host in self.objects['hosts'].values():
            self.item_write_config(host, self.dynamic_dir, os.path.join("hosts", host.host_name))
        for app in self.objects['applications'].values():
            self.item_write_config(app, self.dynamic_dir, os.path.join("hosts", app.host_name))
        for cg in self.objects['contactgroups'].values():
            self.item_write_config(cg, self.dynamic_dir, "contactgroups")
        for c in self.objects['contacts'].values():
            self.item_write_config(c, self.dynamic_dir, "contacts")

    def count_objects(self):
        try:
            hosts = len([name for name in os.listdir(os.path.join(self.dynamic_dir, 'hosts')) if os.path.isdir(os.path.join(self.dynamic_dir, 'hosts', name))])
            apps = len([app for host in os.listdir(os.path.join(self.dynamic_dir, 'hosts')) if os.path.isdir(os.path.join(self.dynamic_dir, 'hosts', host)) for app in os.listdir(os.path.join(self.dynamic_dir, 'hosts', host)) if app != 'host.cfg'])
            return (hosts, apps)
        except Exception:
            return (0, 0)

    def count_before_objects(self):
        self.old_objects = self.count_objects()

    def count_after_objects(self):
        self.new_objects = self.count_objects()


    @classmethod
    def init_classes(cls, classpath):
        for p in [p for p in reversed(classpath) if os.path.exists(p) and os.path.isdir(p)]:
        #for p in [p for p in classpath if os.path.exists(p) and os.path.isdir(p)]:
            for module, path in [(item, p) for item in os.listdir(p) if item[-3:] == ".py" and item.startswith('datarecipient_')]:
                try:
                    #print "try dr", module, path
                    path = os.path.abspath(path)
                    fp, filename, data = imp.find_module(module.replace('.py', ''), [path])
                    toplevel = imp.load_module('', fp, '', ('py', 'r', imp.PY_SOURCE))
                    for cl in inspect.getmembers(toplevel, inspect.isfunction):
                        if cl[0] ==  "__ds_ident__":
                            cls.class_factory.append([path, module, cl[1]])
                except Exception, exp:
                    logger.critical("could not load datarecipient %s from %s: %s" % (module, path, exp))
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
                print "Datarecipient.get_class exception", exp
                pass
        logger.debug("found no matching class for this datarecipient %s" % params)




