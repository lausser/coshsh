#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union, List


@dataclass
class TemplateRule:
    """Rule for matching monitoring objects to Jinja2 templates.

    Template rules define when a template should be rendered for a monitoring
    object (host, application, contact, etc.) based on the object's attributes.

    Attributes:
        needsattr: Attribute that must exist on the object for this rule to apply.
            If None, the rule applies unconditionally.
        isattr: Value or regex pattern that needsattr must match. If None,
            only the existence of needsattr is checked.
        template: Name of the Jinja2 template file (without .tpl extension)
        unique_attr: Attribute(s) used to create unique config filenames.
            Can be a single attribute name or list of attribute names.
        unique_config: Format string for the config filename. Can contain %s
            placeholders for unique_attr values.
        self_name: Name of the variable to pass to the template (default: "application")
        suffix: File extension for generated config files (default: "cfg")
        for_tool: Target monitoring tool (default: "nagios")

    Example:
        >>> # Render os_linux_default.tpl for all objects
        >>> rule = TemplateRule(template="os_linux_default")
        >>>
        >>> # Render only if object has filesystems attribute
        >>> rule = TemplateRule(
        ...     needsattr="filesystems",
        ...     template="os_linux_fs"
        ... )
        >>>
        >>> # Render only if cluster attribute matches "veritas"
        >>> rule = TemplateRule(
        ...     needsattr="cluster",
        ...     isattr="veritas",
        ...     template="os_solaris_cluster_veritas"
        ... )
    """

    needsattr: Optional[str] = None
    isattr: Optional[str] = None
    template: Optional[str] = None
    unique_attr: Union[str, List[str]] = "name"
    unique_config: Optional[str] = None
    self_name: str = "application"
    suffix: str = "cfg"
    for_tool: str = "nagios"

    def __str__(self) -> str:
        """Return a human-readable representation of the template rule."""
        return (
            f"Rule: needsattr={self.needsattr}, isattr={self.isattr}, "
            f"template={self.template}, unique_attr={self.unique_attr}, "
            f"unique_config={self.unique_config}, suffix={self.suffix}, "
            f"self_name={self.self_name}"
        )

