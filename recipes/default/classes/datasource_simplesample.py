#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import os
import re
import logging
from util import compare_attr
from datasource import Datasource
from copy import copy
from host import Host
from application import Application
from contactgroup import ContactGroup
from contact import Contact
from monitoring_detail import MonitoringDetail

logger = logging.getLogger('coshsh')

def __ds_ident__(params={}):
    if compare_attr("type", params, "simplesample"):
        return SimpleSample


class SimpleSample(Datasource):
    def __init__(self, **kwargs):
        #self.name = kwargs["name"]
        self.dir = kwargs.get("dir", "/tmp")
        self.objects = {}

    def open(self):
        logger.info('open datasource %s' % self.name)
        return True

    def read(self, filter=None, objects={}, force=None, **kwargs):
        logger.info('read items from simplesample')
        #self.add('hosts', Host(...))

