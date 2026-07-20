#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Fixture datasource for the template-render-error tests (spec 007).

WHY this fixture is hosts-only and one-rule-per-class: the tests it serves make
assertions about exact counts and exact percentages ("2% of renderings failed,
tolerance is 5%, must publish"). Anything that renders on its own initiative --
applications, hostgroups, contacts -- adds attempts the test did not ask for and
turns a precise ratio into an approximate one. Every host here contributes
exactly one render attempt with exactly one known outcome, so a cookbook that
says ``num_good = 98`` and ``num_broken = 2`` produces exactly 2%.

The counts are read from the ``[datasource_*]`` cookbook section, so one fixture
tree serves every ratio the tests need without a new file per case:

    [datasource_RENDERR_MOSTLYGOOD]
    type        = renderr
    num_good    = 98
    num_broken  = 2

Template outcomes:

    renderr_good    exists and renders               -> success
    renderr_broken  exists, Jinja2 syntax error      -> errors
    renderr_raise   exists, raises while rendering   -> errors
    renderr_gone    does not exist anywhere          -> missing
"""

import logging

import coshsh
from coshsh.datasource import Datasource
from coshsh.host import Host
from coshsh.templaterule import TemplateRule

logger = logging.getLogger('coshsh')


def __ds_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "^renderr$"):
        return RenderErr


class RenderErrHost(coshsh.host.Host):
    """Base for the fixture hosts: no hostgroups, no contacts, one template rule.

    WHY it overrides template_rules rather than extending them: the stock Host
    renders ``host.tpl`` unconditionally, which would add one attempt per host
    that no test asked about. Replacing the list keeps the arithmetic exact.
    """
    template_rules = []


class GoodHost(RenderErrHost):
    template_rules = [
        TemplateRule(needsattr=None, template="renderr_good", self_name="host"),
    ]


class BrokenHost(RenderErrHost):
    template_rules = [
        TemplateRule(needsattr=None, template="renderr_broken", self_name="host"),
    ]


class MissingHost(RenderErrHost):
    template_rules = [
        TemplateRule(needsattr=None, template="renderr_gone", self_name="host"),
    ]


class RaisingHost(RenderErrHost):
    template_rules = [
        TemplateRule(needsattr=None, template="renderr_raise", self_name="host"),
    ]


class RenderErr(coshsh.datasource.Datasource):
    """Emit a configurable mix of hosts whose renderings succeed or fail."""

    # WHY a plain dict rather than one attribute per kind: the read() loop below
    # is then the same three lines for every kind, and adding a kind (as T041
    # does for the raising template) is a one-line change here.
    FLAVORS = {
        "num_good": GoodHost,
        "num_broken": BrokenHost,
        "num_missing": MissingHost,
        "num_raise": RaisingHost,
    }

    def __init__(self, **kwargs):
        super(RenderErr, self).__init__(**kwargs)
        self.name = kwargs["name"]
        # Cookbook values arrive as strings; absent means none of that kind.
        self.counts = dict(
            (key, int(kwargs.get(key, 0))) for key in self.FLAVORS
        )
        self.objects = {}

    def open(self):
        logger.info('open datasource %s' % self.name)

    def read(self, filter=None, objects={}, force=False, **kwargs):
        self.objects = objects
        for key, host_class in self.FLAVORS.items():
            for i in range(self.counts[key]):
                # WHY the host_name carries the flavor: when a test fails, the
                # log line names e.g. "renderr_broken_3" and the failing object
                # is identifiable without cross-referencing the fixture.
                host_name = "%s_%d" % (key.replace("num_", "renderr_"), i)
                self.add('hosts', host_class({
                    'host_name': host_name,
                    'address': '127.0.0.1',
                    'type': 'server',
                }))

    def close(self):
        pass
