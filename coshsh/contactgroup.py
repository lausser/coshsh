#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Contact-group model for coshsh-generated monitoring configuration.

Sole responsibility: represent a single Nagios/Icinga contactgroup and
produce the corresponding configuration via Jinja2 templates.

Does NOT: define which contacts belong to the group at the data-model level.
Membership is driven from the other direction -- each Contact carries a
``contactgroups`` list, and during assemble the datasource (e.g.
datasource_csvfile) creates a ContactGroup object for every group name it
encounters.

Key classes:
    ContactGroup -- Thin Item subclass keyed by ``contactgroup_name``.

AI agent note: ContactGroup objects are typically created during the
datasource ``read()`` phase (not during ``assemble()``).  They are stored
in ``recipe.objects['contactgroups']`` and rendered alongside hosts,
applications, and contacts.
"""

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
        """Create a ContactGroup from a params dict.

        Args:
            params: dict containing at least ``contactgroup_name``.
                    All key/value pairs are set as instance attributes
                    by the parent ``Item.__init__``.
        """
        # WHY: members is initialised before super().__init__ so that
        # params can safely overwrite it if the datasource provides an
        # explicit member list.
        self.members = []
        super(ContactGroup, self).__init__(params)
        self.fingerprint = lambda s=self:s.__class__.fingerprint(params)

    @classmethod
    def fingerprint(self, params):
        """Return the unique identity string for this contactgroup.

        The fingerprint is simply the ``contactgroup_name`` because
        group names are globally unique within a monitoring installation.
        """
        return "%s" % (params["contactgroup_name"], )

    def __str__(self):
        """Return a human-readable label for logging and debugging."""
        return "contactgroup %s" % self.contactgroup_name

