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

"""Coshsh - Configuration generator for monitoring systems.

Coshsh (Config SHell SHell) is a framework for generating monitoring
configuration from various data sources (databases, CSV files, CMDBs, etc.)
and outputting them to monitoring systems (Nagios, Naemon, Icinga, etc.).

Main components:
    - Datasources: Read monitoring data from various sources
    - Recipes: Define how to generate configurations
    - Datarecipients: Write generated configs to destinations
    - Templates: Jinja2 templates for generating config files
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
