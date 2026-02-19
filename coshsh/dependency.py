#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Host-dependency (parent/child) model for coshsh-generated monitoring configuration.

Sole responsibility: represent a single parent-child relationship between
two hosts so that the monitoring engine can suppress notifications for
child hosts when the parent host is down (network reachability).

Does NOT: model service dependencies, dependency periods, or execution
dependencies.  It only captures the structural host-to-host link.

Key classes:
    Dependency -- Lightweight data object holding ``host_name`` and
                  ``parent_host_name``.

AI agent note: Unlike Host, Application, and Contact, Dependency does NOT
inherit from Item or CoshshDatainterface.  It is a plain ``object`` subclass
because it does not need template rendering, class-factory lookup, or
monitoring-detail resolution.  Dependency objects are created by datasources
that provide parent/child host information and are stored for later use
during configuration output.
"""


# WHY: Dependency is a plain object (not an Item subclass) because it only
# stores two strings and never needs template rendering, class-factory lookup,
# monitoring-detail resolution, or fingerprint-based deduplication.  Keeping it
# lightweight avoids pulling in the full Item/CoshshDatainterface machinery for
# what is essentially a two-field data record.
class Dependency(object):

    def __init__(self, params={}):
        self.host_name = params["host_name"]
        self.parent_host_name = params["parent_host_name"]
        
