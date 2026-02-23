#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Host-group model for coshsh-generated monitoring configuration.

Sole responsibility: represent a single Nagios/Icinga hostgroup and produce
the corresponding configuration files via Jinja2 templates.

Does NOT: decide which hosts belong to which groups.  Membership is driven
from the Host side -- each Host carries a ``hostgroups`` list (populated
by ``Host.create_hostgroups()`` during assemble).  The recipe's
``assemble()`` method then iterates over all hosts, collects the declared
group names, and creates HostGroup objects for each unique name.

Key classes:
    HostGroup -- Item subclass keyed by ``hostgroup_name``.  Carries
                 ``members`` (list of host_name strings), ``contacts``,
                 ``contactgroups``, and ``templates`` lists that can be
                 populated by subclass hooks.

AI agent note: HostGroup objects are created *late* in ``Recipe.assemble()``,
after all hosts and applications have been processed.  This deliberate
ordering allows applications to modify ``host.hostgroups`` during their
own ``wemustrepeat()`` / resolve phase before hostgroup objects are built.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import coshsh


class HostGroup(coshsh.item.Item):

    template_rules: ClassVar[list[coshsh.templaterule.TemplateRule]] = [
        coshsh.templaterule.TemplateRule(needsattr=None,
            template="hostgroup",
            self_name="hostgroup",
            unique_attr="hostgroup_name", unique_config="hostgroup_%s",
        ),
    ]

    def __init__(self, params: dict[str, Any] = {}) -> None:
        """Create a HostGroup from a params dict.

        Args:
            params: dict containing at least ``hostgroup_name``.  May also
                    contain ``members`` (list of host_name strings).
                    All key/value pairs become instance attributes via
                    ``Item.__init__``.
        """
        # WHY: List attributes are initialised before super().__init__ so
        # that values supplied in params can safely overwrite the defaults
        # (Item.__init__ sets attributes from params after these lines run).
        self.members: list[str] = []
        self.contacts: list[str] = []
        self.contactgroups: list[str] = []
        self.templates: list[str] = []
        super(HostGroup, self).__init__(params)

    def is_correct(self) -> bool:
        """Validate the hostgroup.  Always returns True for the base class.

        Subclasses may override this to enforce constraints (e.g. non-empty
        members list).
        """
        return True

    def write_config(self, target_dir: str, want_tool: str | None = None) -> None:
        """Write rendered configuration files to the hostgroups sub-directory.

        Creates ``<target_dir>/hostgroups/<hostgroup_name>/`` and writes
        each rendered config file there.  Overrides the default
        ``Item.write_config`` to use a hostgroup-specific directory layout.

        Args:
            target_dir: Root output directory for the recipe.
            want_tool:  Optional monitoring-tool filter.  When set, only
                        config files for that tool are written.
        """
        my_target_dir = Path(target_dir) / "hostgroups" / self.hostgroup_name
        my_target_dir.mkdir(parents=True, exist_ok=True)
        for tool in self.config_files:
            if not want_tool or want_tool == tool:
                for file in self.config_files[tool]:
                    content = self.config_files[tool][file]
                    with open(my_target_dir / file, "w") as f:
                        f.write(content)

    def create_members(self) -> None:
        """Hook for subclasses to populate the ``members`` list.

        The base implementation is a no-op because members are supplied
        by ``Recipe.assemble()`` via the params dict.
        """
        pass

    def create_contacts(self) -> None:
        """Hook for subclasses to populate the ``contacts`` list.

        Called by ``Recipe.assemble()`` after the HostGroup is created.
        The base implementation is a no-op.
        """
        pass

    def create_templates(self) -> None:
        """Hook for subclasses to populate the ``templates`` list.

        Called by ``Recipe.assemble()`` after the HostGroup is created.
        The base implementation is a no-op.
        """
        pass
