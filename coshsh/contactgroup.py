#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import os
import coshsh


class ContactGroup(coshsh.item.Item):

    template_rules = [
        coshsh.templaterule.TemplateRule(
            template="contactgroup",
            self_name="contactgroup",
            unique_attr="contactgroup_name", unique_config="contactgroup_%s",
        )
    ]

    def __init__(self, params={}):
        self.members = []
        super(ContactGroup, self).__init__(params)
        self.fingerprint = lambda s=self:s.__class__.fingerprint(params)

    @classmethod
    def fingerprint(self, params):
        return "%s" % (params["contactgroup_name"], )

    def __str__(self):
        return "contactgroup %s" % self.contactgroup_name

