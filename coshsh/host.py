#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Represents a single monitored host (server, network device, etc.).

Sole responsibility: hold all datasource-provided attributes for one host,
normalise them, and render monitoring configuration files via Jinja2
template rules inherited from Item.

This module does NOT:
- discover or load Host subclasses -- that is handled by the datasource
  layer and class-factory machinery in Application / MonitoringDetail.
- own template files -- those live on disk and are loaded by the Jinja2
  environment configured on the Item base class.

Key classes:
    Host  -- the default host implementation; subclassable per-recipe via
             a custom ``classes/host.py`` to add site-specific logic
             (extra hostgroups, contacts, template rules, etc.).

AI agent note: Host objects are keyed by ``fingerprint()`` (== host_name)
inside ``recipe.objects['hosts']``.  The recipe's ``assemble()`` phase
calls ``resolve_monitoring_details``, ``create_hostgroups``,
``create_contacts``, and ``create_templates`` on every host before
rendering.
"""

from __future__ import annotations

from typing import Any, ClassVar

import coshsh


class Host(coshsh.item.Item):
    """A single monitored host and all its configuration metadata.

    Inherits template rendering, monitoring-detail resolution, and config
    file writing from ``Item``.  Recipes may replace this class entirely
    by placing a custom ``host.py`` with its own ``Host`` class in the
    recipe's ``classes_dir``.
    """

    template_rules: ClassVar[list[coshsh.templaterule.TemplateRule]] = [
        coshsh.templaterule.TemplateRule(needsattr=None,
            template="host",
            self_name="host",
        ),
    ]
    # WHY: lower_columns lists attributes that are normalised to lowercase
    # during __init__.  Datasource data arrives in unpredictable casing
    # (e.g. "Windows" vs "windows", "VMware" vs "vmware").  Lowercasing
    # these columns guarantees that template rules, class-factory ident
    # functions, and recipe logic can rely on a single canonical form
    # (e.g. ``host.os == "windows"``) without case-insensitive comparisons
    # scattered throughout the codebase.
    lower_columns: ClassVar[list[str]] = ['address', 'type', 'os', 'hardware', 'virtual', 'location', 'department']

    def __init__(self, params: dict[str, Any] = {}) -> None:
        """Initialise a Host from a datasource parameter dict.

        Processing steps:
        1. Normalise ``lower_columns`` values to lowercase.  If a column
           is present but its value is not a string (so ``.lower()`` fails),
           it is set to ``None`` as a safe fallback.
        2. Set up empty collection attributes (hostgroups, contacts, etc.)
           so that downstream code can always append without checking.
        3. Delegate to ``Item.__init__`` which copies every remaining
           key/value pair from *params* onto the instance.
        4. Default ``alias`` to ``host_name`` when the datasource did not
           supply one.
        5. Bind ``fingerprint`` as an instance-level callable so that the
           recipe can obtain the host's identity without knowing the class.
        """
        # WHY: normalisation happens *before* super().__init__ so that
        # Item.__init__ stores the already-lowered values as attributes.
        for c in self.__class__.lower_columns:
            try:
                params[c] = params[c].lower()
            except Exception:
                if c in params:
                    params[c] = None
        self.hostgroups = []
        self.contacts = []
        self.contact_groups = []
        self.templates = []
        # WHY: default ports to [22] (SSH) because coshsh was originally
        # written for Nagios-style monitoring where SSH-based checks are the
        # most common remote access method.  A MonitoringDetail of type PORT
        # can override or extend this list during resolve_monitoring_details().
        self.ports = [22] # can be changed with a PORT detail
        super(Host, self).__init__(params)
        self.alias = getattr(self, 'alias', self.host_name)
        if not hasattr(self, "macros"):
            self.macros = {}
        self.fingerprint = lambda s=self:s.__class__.fingerprint(params)

    @classmethod
    def fingerprint(cls, params: dict[str, Any]) -> str:
        """Return a unique identity string for the host described by *params*.

        The fingerprint is used as the dict key in
        ``recipe.objects['hosts']`` so it must be deterministic and unique
        across all hosts in a recipe.
        """
        return f"{params['host_name']}"

    def is_correct(self) -> bool:
        """Validate that this host has the minimum required attributes.

        Returns ``True`` when the host carries a non-None ``host_name``.
        Datasources call this after construction to decide whether the
        host should be kept or discarded as incomplete input data.
        """
        # WHY: is_correct() acts as a data-quality gate.  Datasources may
        # yield rows with missing or NULL host_name values (e.g. empty CSV
        # lines, SQL outer-join artefacts).  Checking here lets the caller
        # silently skip garbage rows instead of failing later during
        # template rendering or config writing.
        return hasattr(self.host_name) and self.host_name != None

    def create_hostgroups(self) -> None:
        """Hook for subclasses to populate ``self.hostgroups`` at assemble time.

        Called by ``Recipe.assemble()`` after monitoring details have been
        resolved.  The base implementation is a no-op; override in a
        custom Host subclass to derive hostgroups from host attributes
        (e.g. grouping by OS, location, or department).
        """
        pass

    def create_contacts(self) -> None:
        """Hook for subclasses to populate ``self.contacts`` at assemble time.

        Called by ``Recipe.assemble()`` after monitoring details have been
        resolved.  Override to derive contact assignments from host
        attributes such as department or location.
        """
        pass

    def create_templates(self) -> None:
        """Hook for subclasses to modify ``self.template_rules`` at assemble time.

        Called by ``Recipe.assemble()`` after monitoring details have been
        resolved.  Override to dynamically add or remove template rules
        based on resolved host attributes (e.g. add an extra template
        when the host has a certain OS or hardware type).
        """
        pass

