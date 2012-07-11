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
from contactgroup import ContactGroup
from contact import Contact
from monitoring_detail import MonitoringDetail
from coshsh.log import logger
from util import compare_attr

def __ds_ident__(params={}):
    print "this is orschknorsch"
    if compare_attr("type", params, "simplesample"):
        return SimpleSample


class SimpleSample(Datasource):
    def __init__(self, **kwargs):
        print "init default SimpleSample"
        #self.name = kwargs["name"]
        self.dir = kwargs["dir"]
        self.hosts = {}
        self.applications = {}
        self.appdetails = {}
        self.contacts = {}
        self.contactgroups = {}
        self.dependencies = {}
        self.bps = {}

    def read(self, filter=None, intermediate_hosts=[], intermediate_applications=[]):
        logger.info('read items from simplesample')
        return self.hosts.values(), self.applications.values(), self.contacts.values(), self.contactgroups.values(), self.appdetails, self.dependencies, self.bps


