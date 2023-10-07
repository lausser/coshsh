#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import sys
import os
import re
import logging
import coshsh

logger = logging.getLogger('coshsh')


class DatasourceNotImplemented(Exception):
    pass


class DatasourceNotReady(Exception):
    # datasource is currently being updated
    pass


class DatasourceNotCurrent(Exception):
    # datasources was not updated lately.
    # it makes no sense to continue.
    pass


class DatasourceNotAvailable(Exception):
    pass


class DatasourceCorrupt(Exception):
    pass


class Datasource(coshsh.datainterface.CoshshDatainterface):

    my_type = 'datasource'
    class_file_prefixes = ["datasource"]
    class_file_ident_function = "__ds_ident__"
    class_factory = []

    def __init__(self, **params):
        #print "datasourceinit with", self.__class__
        for key in [k for k in params if k.startswith("recipe_")]:
            setattr(self, key, params[key])
            short = key.replace("recipe_", "")
            if not short in params:
                params[short] = params[key]
        for key in params.keys():
            if isinstance(params[key], str):
                params[key] = re.sub('%.*?%', coshsh.util.substenv, params[key])
        if self.__class__ == Datasource:
            #print "generic ds", params
            newcls = self.__class__.get_class(params)
            if newcls:
                #print "i rebless anon datasource to", newcls, params
                self.__class__ = newcls
                self.__init__(**params)
            else:
                logger.critical('datasource for %s is not implemented' % params, exc_info=1)
                #print "i raise DatasourceNotImplemented"
                raise DatasourceNotImplemented
        else:
            setattr(self, 'name', params["name"])
            self.objects = {}
            pass
        # i am a generic datasource
        # i find a suitable class
        # i rebless
        # i call __init__

    def open(self, **kwargs):
        pass

    def read(self, **kwargs):
        pass

    def close(self):
        pass

    def add(self, objtype, obj):
        try:
            self.objects[objtype][obj.fingerprint()] = obj
        except Exception:
            self.objects[objtype] = {}
            self.objects[objtype][obj.fingerprint()] = obj
        if objtype == 'applications':
            if self.find('hosts', obj.host_name):
                setattr(obj, 'host', self.get('hosts', obj.host_name))

    def get(self, objtype, fingerprint):
        try:
            return self.objects[objtype][fingerprint]
        except Exception:
            # should be None
            return None
            return 'i do not exist. no. no!'

    def getall(self, objtype):
        try:
            return list(self.objects[objtype].values())
        except Exception:
            return []

    def find(self, objtype, fingerprint):
        return objtype in self.objects and fingerprint in self.objects[objtype]
