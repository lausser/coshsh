#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import os
import re
import logging
import coshsh
from coshsh.host import Host
from coshsh.datasource import Datasource
from coshsh.application import Application
from coshsh.monitoringdetail import MonitoringDetail
from coshsh.util import compare_attr

logger = logging.getLogger('coshsh')

def __ds_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "lazy"):
        return LazyDs

class MyHost(coshsh.host.Host):
    def __init__(self, params={}):
        superclass = super(MyHost, self)
        superclass.__init__(params)
        self.my_host = True

class LazyDs(coshsh.datasource.Datasource):
    class_only_the_test_simplesample = True
    def __init__(self, **kwargs):
        print(kwargs)
        self.name = kwargs["name"]
        self.dir = kwargs["dir"]
        self.only_the_test_simplesample = True

    def read(self, filter=None, objects={}, **kwargs):
        logger.info('read items from simplesample')
        self.objects = objects
        hostdata = {
            'host_name': 'test_host_0',
            'address': '127.0.0.9',
            'type': 'test',
            'hardware': 'Vmware',
            'virtual': 'vs',
            'notification_period': '7x24',
            'location': 'esxsrv10',
            'department': 'test',
        }
        self.add('hosts', MyHost(hostdata))
        appdata = {
            'host_name': 'test_host_0',
            'name': 'os',
            'type': 'Windows',
            'component': '',
            'version': '2008',
            'patchlevel': 'R2',
            'host_name': 'test_host_0',
            'check_period': '7x24',
        }
        self.add('applications', coshsh.application.Application(appdata))
        detdata = {
            'host_name': 'test_host_0',
            'name': 'os',
            'type': 'Windows',
            'monitoring_type': 'KEYVALUES',
            'monitoring_0': 'huhu',
            'monitoring_1': 'dada',
        }
        self.add('details', coshsh.monitoringdetail.MonitoringDetail(detdata))

