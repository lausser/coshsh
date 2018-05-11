#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import os
import re
import logging
from copy import copy
import coshsh
from coshsh.datasource import Datasource
from coshsh.host import Host
from coshsh.util import compare_attr

logger = logging.getLogger("coshsh")

def __ds_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "simplesample"):
        return SimpleSample


class SimpleSample(coshsh.datasource.Datasource):
    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        self.dir = kwargs["dir"]
        self.only_the_test_simplesample = True

    def read(self, filter=None, objects={}, **kwargs):
        self.objects = objects
        logger.info('read items from simplesample')
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
        self.add('hosts', coshsh.host.Host(hostdata))
