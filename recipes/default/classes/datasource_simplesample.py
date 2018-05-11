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
from copy import copy
from coshsh.util import compare_attr
from coshsh.datasource import Datasource
from coshsh.host import Host
from coshsh.application import Application
from coshsh.contactgroup import ContactGroup
from coshsh.contact import Contact
from coshsh.monitoringdetail import MonitoringDetail

logger = logging.getLogger('coshsh')

def __ds_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "simplesample"):
        return SimpleSample


class SimpleSample(coshsh.datasource.Datasource):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__(**kwargs)
        # default name is taken from the ini-section
        # [datasource_thisisthename]
        #self.name = kwargs["name"]
        self.dir = kwargs.get("dir", "/tmp")
        self.objects = {}

    def open(self):
        logger.info('open datasource %s' % self.name)
        return True

    def read(self, filter=None, objects={}, force=None, **kwargs):
        logger.info('read items from simplesample')
        # if the recipe has read other datasources before, then these
        # are the objects collected so far:
        self.objects = objects
        #self.add('hosts', Host(...))

    def close(self):
        # close a database, file, ...
        pass

