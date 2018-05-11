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
from coshsh.datasource import Datasource, DatasourceNotCurrent
from coshsh.util import compare_attr

logger = logging.getLogger('coshsh')

def __ds_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "handshake"):
        return Handshake


class Handshake(coshsh.datasource.Datasource):
    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        self.only_the_test_simplesample = True

    def read(self, filter=None, objects={}, **kwargs):
        logger.info('read items from handshake')
        raise coshsh.datasource.DatasourceNotCurrent
        self.objects = objects
