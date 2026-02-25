#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# Actually Copyright is a concept which does not exist in the german Urheberrecht. But as everybody writes somethins about Copyright in the file header, i do it as well.
# Und im Klartext: wennst an Scheis baust (siehe GAGPL), na hau i dir links und raechts a drumm Fotzn owa.
# 
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""
coshsh package: A configuration generator for monitoring systems.

Sole responsibility: This package provides the complete framework for
transforming inventory data (hosts, applications, contacts) from arbitrary
datasources into monitoring configuration files for Nagios, Icinga, Naemon,
Shinken, and Prometheus.

Does NOT: coshsh does not execute monitoring checks, manage monitoring
daemons, or provide a user interface. It only generates configuration files.

Key classes:
    Generator: Reads cookbook INI files and orchestrates recipe execution.
    Recipe: Owns the four-phase pipeline (collect, assemble, render, output).
    Datasource: Base class for reading inventory data from external sources.
    Datarecipient: Base class for writing generated configuration to targets.
    Application: Represents a monitored application; selected via class factory.
    Host: Represents a monitored host/server.
    Contact: Represents a notification recipient.
    MonitoringDetail: Fine-grained configuration attributes attached to objects.
    TemplateRule: Declarative rule binding Jinja2 templates to objects.
    Vault: Base class for secrets/credential management.

AI agent note: The import order below matters — modules are imported in
dependency order. Changing the import order can cause ImportError at startup
because some modules reference each other during class factory initialisation.
"""

from __future__ import annotations

import coshsh.configparser
import coshsh.jinja2_extensions
import coshsh.templaterule
import coshsh.datainterface
import coshsh.datasource
import coshsh.datarecipient
import coshsh.item
import coshsh.application
import coshsh.host
import coshsh.hostgroup
import coshsh.contact
import coshsh.contactgroup
import coshsh.monitoringdetail
import coshsh.recipe
import coshsh.generator
import coshsh.util
