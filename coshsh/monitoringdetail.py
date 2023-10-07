#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import sys
import os
import logging
from urllib.parse import urlparse
import coshsh

logger = logging.getLogger('coshsh')


class MonitoringDetailNotImplemented(Exception):
    pass


class MonitoringDetail(coshsh.item.Item):

    class_factory = []
    class_file_prefixes = ["detail_"]
    class_file_ident_function = "__detail_ident__"
    my_type = "detail"
    lower_columns = ['name', 'type', 'application_name', 'application_type']

    def __init__(self, params):
        if self.__class__.__name__ == "MonitoringDetail":
            for c in self.__class__.lower_columns:
                try:
                    params[c] = params[c].lower()
                except Exception:
                    if c in params:
                        params[c] = None
            # name, type is preferred, because a detail can also be a host detail
            # application_name, application_type is ok too. in any case these will be internally used
            if 'name' in params:
                params['application_name'] = params['name']
                del params['name']
            if 'type' in params:
                params['application_type'] = params['type']
                del params['type']
            newcls = self.__class__.get_class(params)
            if newcls:
                self.__class__ = newcls
                super(MonitoringDetail, self).__init__(params)
                self.__init__(params)
            else:
                logger.info("monitoring detail of type %s for host %s / appl %s had a problem" % (params["monitoring_type"], params.get("host_name", "unkn. host"), params.get("application_name", "unkn. application")))
                raise MonitoringDetailNotImplemented
        else:
            pass

    def fingerprint(self):
        # it does not make sense to construct an id from the random attributes
        # id is used in self.add('details')
        return id(self)

    def application_fingerprint(self):
        if hasattr(self, 'application_name') and self.application_name and hasattr(self, 'application_type') and self.application_type:
            return "%s+%s+%s" % (self.host_name, self.application_name, self.application_type)
        elif self.host_name:
            return "%s" % (self.host_name, )
        raise "impossible fingerprint"

    def __eq__(self, other):
        return ((self.monitoring_type, str(self.monitoring_0)) == (other.monitoring_type, str(other.monitoring_0)))

    def __ne__(self, other):
        return ((self.monitoring_type, str(self.monitoring_0)) != (other.monitoring_type, str(other.monitoring_0)))

    def __lt__(self, other):
        return ((self.monitoring_type, str(self.monitoring_0)) < (other.monitoring_type, str(other.monitoring_0)))

    def __le__(self, other):
        return ((self.monitoring_type, str(self.monitoring_0)) <= (other.monitoring_type, str(other.monitoring_0)))

    def __gt__(self, other):
        return ((self.monitoring_type, str(self.monitoring_0)) > (other.monitoring_type, str(other.monitoring_0)))

    def __ge__(self, other):
        return ((self.monitoring_type, str(self.monitoring_0)) >= (other.monitoring_type, str(other.monitoring_0)))

    def __repr__(self):
        return "%s %s" % (self.monitoring_type, str(self.monitoring_0))

