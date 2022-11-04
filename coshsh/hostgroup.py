#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import coshsh


class HostGroup(coshsh.item.Item):

    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None, 
            template="hostgroup", 
            self_name="hostgroup",
            unique_attr="hostgroup_name", unique_config="hostgroup_%s",
        ),
    ]

    def __init__(self, params={}):
        self.members = []
        self.contacts = []
        self.contactgroups = []
        self.templates = []
        superclass = super(HostGroup, self)
        superclass.__init__(params)
        
    def is_correct(self):
        return True

    def write_config(self, target_dir, want_tool=None):
        my_target_dir = os.path.join(target_dir, "hostgroups", self.hostgroup_name)
        if not os.path.exists(my_target_dir):
            os.makedirs(my_target_dir)
        for tool in self.config_files:
            if not want_tool or want_tool == tool:
                for file in self.config_files[tool]:
                    content = self.config_files[tool][file]
                    with open(os.path.join(my_target_dir, file), "w") as f:
                        f.write(content)


    def create_members(self):
        pass

    def create_contacts(self):
        pass

    def create_templates(self):
        pass

