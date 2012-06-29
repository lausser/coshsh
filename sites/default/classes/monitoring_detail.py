#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from urlparse import urlparse
from coshsh.log import logger
from application import Application


class MonitoringDetailNotImplemented(Exception):
    pass


class MonitoringDetail(object):
    detail_factory = []

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
    def get_detail(cls, params={}):
        for class_func in cls.detail_factory:
            try:
                newcls = class_func(params)
                if newcls:
                    return newcls
            except Exception:
                pass
        logger.debug("found no matching detail for type %s" % params["monitoring_type"])

