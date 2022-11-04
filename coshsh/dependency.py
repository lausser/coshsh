#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).


class Dependency(object):

    def __init__(self, params={}):
        self.host_name = params["host_name"]
        self.parent_host_name = params["parent_host_name"]
        
