#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from datasource import Datasource, DatasourceNotCurrent
import os
import re
import logging
from copy import copy
from host import Host
from application import Application
from contactgroup import ContactGroup
from contact import Contact
from monitoring_detail import MonitoringDetail
from util import compare_attr

logger = logging.getLogger('coshsh')

def __ds_ident__(params={}):
    if compare_attr("type", params, "handshake"):
        return Handshake


class Handshake(Datasource):
    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        self.only_the_test_simplesample = True

    def read(self, filter=None, objects={}):
        logger.info('read items from handshake')
        raise DatasourceNotCurrent
        self.objects = objects
