#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""
Declarative rule that binds a Jinja2 template to a monitoring object based
on attribute matching conditions.

Does NOT: render templates or produce output files -- rendering is performed
by Item.resolve_monitoring_details() / Item.render_cfg_template() using the
rule's attributes.

Key classes:
    TemplateRule -- immutable-ish descriptor declaring when and how a Jinja2
        template should be rendered for a given monitoring object (Host,
        Application, Contact, etc.).

AI agent note:
    TemplateRules are typically declared as class-level lists
    (``template_rules = [TemplateRule(...), ...]``) inside Application or Host
    subclasses. They are evaluated in list order by Item.resolve_monitoring_details(),
    and multiple rules can fire for the same object.
"""

from __future__ import annotations

import re
from typing import Any


class TemplateRule:
    """Declares the conditions under which a Jinja2 template is rendered for
    a monitoring object and how the output file is named.

    Matching logic precedence (evaluated in Item.resolve_monitoring_details):
        1. needsattr is None  -->  rule always fires (unconditional).
        2. needsattr set, isattr is None  -->  fires if the object simply
           *has* the attribute (existence check only).
        3. needsattr set, isattr set, attribute is a scalar  -->  fires if
           the attribute value equals isattr or matches isattr as a regex.
        4. needsattr set, isattr set, attribute is a list  -->  fires if
           *any* list element equals isattr or matches isattr as a regex.
    Earlier rules in the template_rules list are evaluated first, but each
    rule is independent -- multiple rules can fire for the same object.
    """

    def __init__(self, needsattr: str | None = None, isattr: str | None = None, template: str | None = None, unique_attr: str | list[str] = "name", unique_config: str | None = None, self_name: str = "application", suffix: str = "cfg", for_tool: str = "nagios") -> None:
        """Initialise a TemplateRule with matching conditions and output parameters.

        Args:
            needsattr: Name of an object attribute that must exist for this
                rule to fire.  None means the rule is unconditional (always
                fires).
            isattr: Required value (or regex pattern) the attribute named by
                needsattr must match.  None means any value is accepted
                (existence check only).  When the attribute is a list, the
                pattern is tested against each element.
            template: Name of the Jinja2 template file (without extension)
                to render when this rule fires.  Looked up from the recipe's
                templates_path directories.
            unique_attr: Attribute name (str) or list of attribute names used
                to derive a per-instance output filename via unique_config.
                Defaults to "name".  When a list, each element is resolved
                and passed as positional args to unique_config % (...).
            unique_config: A printf-style format string (e.g. "app_%s_%s")
                that produces the output filename stem by interpolating
                unique_attr values.  None means the template name is used
                as the output filename.
            self_name: Variable name under which the rendering object is
                passed into the Jinja2 template context.  Defaults to
                "application".  Set to "host", "contact", etc. for
                non-application object types.
            suffix: File extension for the output config file.  Defaults
                to "cfg".
            for_tool: Target monitoring tool identifier.  Defaults to
                "nagios".  Used by the datarecipient to route output into
                the correct directory structure.
        """
        # This rule applies by default (needsattr=None) or if a certain
        # property exists
        # WHY: needsattr=None is the common case for "always render this
        # template" rules (e.g. the base OS template).  This avoids forcing
        # every rule declaration to invent a dummy attribute.
        self.needsattr = needsattr
        # WHY: isattr adds value-level filtering on top of the existence
        # check.  It supports both exact match and regex, allowing a single
        # rule to cover families of values (e.g. isattr="linux.*" matches
        # linux, linux_suse, linux_rhel).
        self.isattr = isattr
        self._isattr_re = re.compile(isattr) if isattr is not None else None
        self.template = template
        # Sometimes more than one configs are needed
        # This property is used to separate the application objects
        # WHY: unique_attr + unique_config together enable per-instance
        # output files.  For example, filesystem monitoring creates one
        # config file per filesystem by setting unique_attr to the
        # filesystem attribute and unique_config to "app_%s_fs".
        self.unique_attr = unique_attr
        # The name of the config file which can contain %s
        self.unique_config = unique_config
        # WHY: suffix defaults to "cfg" for Nagios-style config, but some
        # tools (e.g. Prometheus) need different extensions.
        self.suffix = suffix
        # WHY: self_name controls the template variable name so that the
        # same rendering machinery works for hosts, contacts, and
        # applications without each needing its own render pipeline.
        self.self_name = self_name
        # WHY: for_tool allows the same recipe to emit config for multiple
        # monitoring tools side by side (e.g. nagios + prometheus), with the
        # datarecipient using this field to file output into separate trees.
        self.for_tool = for_tool

    _MISSING = object()

    def matches(self, item: Any) -> bool:
        """Return True if this rule should fire for *item*."""
        if not self.needsattr:
            return True
        val = getattr(item, self.needsattr, self._MISSING)
        if val is self._MISSING:
            return False
        if self.isattr is None:
            return True
        if isinstance(val, list):
            return any(elem == self.isattr or self._isattr_re.match(elem) for elem in val)
        return val == self.isattr or bool(self._isattr_re.match(val))

    def __str__(self) -> str:
        """Return a human-readable representation of this rule for logging."""
        return f"Rule: needsattr={self.needsattr}, isattr={self.isattr}, template={self.template}, unique_attr={self.unique_attr}, unique_config={self.unique_config}, suffix={self.suffix}, self_name={self.self_name}"

