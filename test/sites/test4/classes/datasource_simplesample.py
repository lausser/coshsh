#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from datasource import Datasource
import os
import re
from copy import copy
from host import Host
from application import Application
#from contactgroup import ContactGroup
#from contact import Contact
#from monitoring_detail import MonitoringDetail
#from coshsh.log import logger
from util import compare_attr

def __ds_ident__(params={}):
    print "this is simplesample ident"
    if compare_attr("type", params, "simplesample"):
        print "this is match simplesample ident"
        print "i return a SimpleSample", SimpleSample
        print "i return a SimpleSample", SimpleSample.class_only_the_test_simplesample
        return SimpleSample

class MyHost(Host):
    def __init__(self, params={}):
        superclass = super(MyHost, self)
        superclass.__init__(params)
        self.my_host = True

class SimpleSample(Datasource):
    class_only_the_test_simplesample = True
    def __init__(self, **kwargs):
        print "i am the init od SimpleSample custom"
        #self.name = kwargs["name"]
        self.dir = kwargs["dir"]
        self.hosts = {}
        self.applications = {}
        self.appdetails = {}
        self.contacts = {}
        self.contactgroups = {}
        self.dependencies = {}
        self.bps = {}
        self.only_the_test_simplesample = True

    def read(self, filter=None, intermediate_hosts=[], intermediate_applications=[]):
        print "logger"
        logger.info('read items from simplesample')
        print "logger"
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
        self.hosts['test_host_0'] = MyHost(hostdata)
        appdata = {
            'name': 'os',
            'type': 'Red Hat',
            'component': '',
            'version': '6.3',
            'patchlevel': '',
            'host_name': 'test_host_0',
            'check_period': '7x24',
        }
        print "now create appl"
        a = Application(appdata)
        self.applications[a.fingerprint()] = a
        
        return self.hosts.values(), self.applications.values(), self.contacts.values(), self.contactgroups.values(), self.appdetails, self.dependencies, self.bps

