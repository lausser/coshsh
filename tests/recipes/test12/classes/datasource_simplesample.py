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
from coshsh.util import compare_attr

logger = logging.getLogger('coshsh')

def __ds_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "simplesample"):
        return SimpleSample

class MyHost(coshsh.host.Host):
    def __init__(self, params={}):
        superclass = super(MyHost, self)
        superclass.__init__(params)
        self.my_host = True

class SimpleSample(coshsh.datasource.Datasource):
    class_only_the_test_simplesample = True
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__(**kwargs)
        self.name = kwargs["name"]
        self.only_the_test_simplesample = True

    def read(self, filter=None, objects={}, **kwargs):
        logger.info('read items from simplesample')
        self.objects = objects
        hostdata = {
            'host_name': 'test_host_0',
            'address': '127.0.0.9',
            'type': 'test',
            'os': 'Red Hat 6.3',
            'hardware': 'Vmware',
            'virtual': 'vs',
            'notification_period': '7x24',
            'location': 'esxsrv10',
            'department': 'test',
        }
        self.add('hosts', MyHost(hostdata))
        appdata = {
            'name': 'os',
            'type': 'Red Hat',
            'component': '',
            'version': '6.3',
            'patchlevel': '',
            'host_name': 'test_host_0',
            'check_period': '7x24',
        }
        self.add('applications', coshsh.application.Application(appdata))
        appdata = {
            'name': 'os',
            'type': 'Windows',
            'component': '',
            'version': '2008',
            'patchlevel': 'R2',
            'host_name': 'test_host_0',
            'check_period': '7x24',
        }
        self.add('applications', coshsh.application.Application(appdata))
        fsc = {
            'monitoring_type': 'FILESYSTEM',
            'monitoring_0': 'C',
            'monitoring_1': '10',
            'monitoring_2': '20',
            'monitoring_3': '%',
        }
        fsd = {
            'monitoring_type': 'FILESYSTEM',
            'monitoring_0': 'D',
            'monitoring_1': '12',
            'monitoring_2': '24',
            'monitoring_3': '%',
        }
        self.get('applications', coshsh.application.Application(appdata).fingerprint()).monitoring_details.append(coshsh.monitoringdetail.MonitoringDetail(fsc))
        self.get('applications', coshsh.application.Application(appdata).fingerprint()).monitoring_details.append(coshsh.monitoringdetail.MonitoringDetail(fsd))

