#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from application import Application, ApplicationNotImplemented
from util import compare_attr
from coshsh.log import logger

class OperatingSystem(Application):
    def __new__(cls, params={}):
        newcls = cls.get_class(params)
        if not newcls:
            logger.info("found unknown operating system %s (version: %s)" % (params.get("type", "null_type"), params.get("version", "")))
            pass
        try:
            #print "i __new a", newcls.__name__
            return newcls.__new__(newcls, params)
        except ApplicationNotImplemented, e:
            #print "i don't know this type of os", params["type"], params["version"]
            print "error is", e
            raise ApplicationNotImplemented
        except Exception as e:
            raise ApplicationNotImplemented


    def __str__(self):
        descr = "OS %s (%s)" % (self.__class__.__name__, self.type)
        if hasattr(self, "host"):
            descr += " Host %s" % self.host.host_name
        return descr
