#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Base class for all coshsh configuration objects (Host, Application,
Contact, HostGroup, ContactGroup).

Sole responsibility: provide template rendering and monitoring detail
resolution so that every configuration object can turn itself into one or
more output files for any monitoring tool.

This module does NOT handle plugin/class discovery -- that logic lives in
datainterface.py (CoshshDatainterface).
"""

from __future__ import annotations

import functools
import logging
import re
from copy import copy, deepcopy
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, TemplateSyntaxError

import coshsh

logger = logging.getLogger('coshsh')


class EmptyObject:
    pass


class Item(coshsh.datainterface.CoshshDatainterface):
    template_cache = {}

    @classmethod
    def reload_template_path(cls) -> None:
        loader = FileSystemLoader(cls.templates_path)
        cls.env = Environment(loader=loader)
        cls.env.trim_blocks = True

    def __init__(self, params: dict[str, Any] = {}) -> None:
        """Initialise an Item from a dict of datasource parameters.

        Each key/value pair in *params* becomes an instance attribute.
        String values are stripped of surrounding whitespace unless the
        subclass opts out via ``dont_strip_attributes`` (bool or list).

        Sets up three core bookkeeping structures:
        - ``monitoring_details``: list of detail objects waiting to be
          resolved onto this item (see ``resolve_monitoring_details``).
        - ``config_files``: rendered output, ready to be written to disk.
        - ``object_chronicle``: audit trail of notable events for this
          object.
        """
        for key in params:
            if hasattr(self, "dont_strip_attributes") and isinstance(params[key], str):
                if isinstance(self.dont_strip_attributes, bool) and self.dont_strip_attributes == True:
                    setattr(self, key, params[key])
                elif isinstance(self.dont_strip_attributes, list) and key in self.dont_strip_attributes:
                    setattr(self, key, params[key])
                else:
                    setattr(self, key, params[key].strip())
            elif isinstance(params[key], str):
                setattr(self, key, params[key].strip())
            else:
                setattr(self, key, params[key])

        if not hasattr(self, "monitoring_details"):
            # if not pre-set through the class
            self.monitoring_details = []
        else:
            setattr(self, "monitoring_details", list(self.__class__.monitoring_details))
        # WHY: config_files is a dict keyed by tool name (e.g. 'nagios',
        # 'prometheus') because different datarecipients route output to
        # different monitoring tools.  Each tool key maps to another dict of
        # {filename: rendered_content}, allowing a single Item to produce
        # output for multiple backends in a single render pass.
        self.config_files = {}
        self.object_chronicle = []

    def record_in_chronicle(self, message: str = "") -> None:
        if message:
            self.object_chronicle.append(message)

    def write_config(self, target_dir: str, want_tool: str | None = None) -> None:
        """Write all rendered config files for this item to disk.

        Creates a per-host subdirectory under *target_dir*/hosts/ and
        writes every file previously stored in ``self.config_files``.
        If *want_tool* is given, only files for that specific monitoring
        tool are written (e.g. ``want_tool='nagios'``); otherwise all
        tools are written.
        """
        my_target_dir = Path(target_dir) / "hosts" / self.host_name
        my_target_dir.mkdir(parents=True, exist_ok=True)
        for tool in self.config_files:
            if not want_tool or want_tool == tool:
                for file in self.config_files[tool]:
                    content = self.config_files[tool][file]
                    with open(my_target_dir / file, "w") as f:
                        f.write(content)

    def resolve_monitoring_details(self) -> None:
        """Flatten monitoring detail objects into attributes on this item.

        Each monitoring detail carries data from the datasource (e.g. a
        filesystem to monitor, a TCP port, login credentials).  Resolution
        walks the detail list and sets, appends, or merges each detail's
        payload onto the parent object.  After resolution the item has
        concrete attributes such as ``filesystems``, ``login``, ``ports``,
        ``urls``, ``services``, etc. that templates can reference directly.

        Details are consumed (removed from ``self.monitoring_details``) so
        that calling this method again is safe and idempotent.
        """
        # WHY: monitoring detail resolution sets/appends/merges attributes
        # onto the parent object.  After this loop the object gains
        # attributes like ``filesystems``, ``login``, ``ports`` etc. that
        # Jinja2 templates can iterate over when rendering config files.
        details = list(self.monitoring_details)
        for detail in details:
            property = detail.__class__.property
            if property == "generic":
                if detail.__class__.property_type == dict:
                    for key in detail.dictionary:
                        if key:
                            if ":" in key:
                                dictname, key = key.split(":")
                                if not hasattr(self, dictname):
                                    setattr(self, dictname, EmptyObject())
                                setattr(getattr(self, dictname), key, detail.dictionary[dictname + ":" + key])
                            else:
                                setattr(self, key, detail.dictionary[key])
                elif detail.__class__.property_type == list:
                    for key in detail.dictionary:
                        if key:
                            existing = getattr(self, key, None)
                            if existing is not None:
                                existing.extend(detail.dictionary[key])
                            else:
                                setattr(self, key, detail.dictionary[key])
                else:
                    setattr(self, detail.attribute, detail.value)
            else:
                if detail.__class__.property_type == list:
                    if not hasattr(self, property):
                        setattr(self, property, [])
                    if hasattr(detail.__class__, "unique_attribute"):
                        # WHY: unique_attribute enforces replacement-instead-of-append
                        # semantics.  If a detail class declares unique_attribute="path",
                        # then two FILESYSTEM details with the same path value won't both
                        # appear in the list — the newer one replaces the older one.
                        # This prevents duplicate monitoring entries when the same detail
                        # is supplied from multiple datasources or repeated in the data.
                        prop_list = getattr(self, property)
                        unique_attr_name = detail.__class__.unique_attribute
                        unique_val = getattr(detail, unique_attr_name)
                        replaced = False
                        for i, o in enumerate(prop_list):
                            if o.__class__ == detail.__class__ and getattr(o, unique_attr_name) == unique_val:
                                prop_list[i] = detail
                                replaced = True
                                break
                        if not replaced:
                            prop_list.append(detail)
                    else:
                        if hasattr(detail.__class__, "property_attr"):
                            getattr(self, property).append(getattr(detail, getattr(detail.__class__, "property_attr")))
                        else:
                            getattr(self, property).append(detail)
                elif detail.__class__.property_type == dict:
                    if not hasattr(self, property):
                        setattr(self, property, {})
                    if hasattr(detail, "key") and hasattr(detail, "value"):
                        getattr(self, property)[detail.key] = detail.value
                else:
                    if getattr(detail.__class__, 'property_flat', False):
                        # ex. MonitoringDetailRole: appl.role == str instead of appl.role.role == str
                        setattr(self, property, getattr(detail, property))
                    else:
                        setattr(self, property, detail)
        # Clear all resolved details at once (O(1) instead of O(n) per remove)
        self.monitoring_details.clear()
        self.wemustrepeat()
        # example: if we have self.ports
        # and self.ports[0] has an inside property ports
        # and self has d default property port (set in __init__)
        # replace the self.port by self.ports[0].port
        for one_property in [detail.__class__.property.rstrip('s') for detail in details if detail.__class__.property_type == list and not hasattr(detail.__class__, "unique_attribute") and not hasattr(detail.__class__, "property_attr") and detail.__class__.property.endswith('s') and hasattr(self, detail.__class__.property.rstrip('s'))]:
            if hasattr(getattr(self, one_property + 's')[0], one_property):
                setattr(self, one_property, getattr(getattr(self, one_property + 's')[0], one_property))

    def wemustrepeat(self) -> None:
        """
        This method is called by some classes if different monitoring_details need to interact.
        Ex. (username/password was set in a LOGIN detail and/or a URL detail
        The name is a tribute to my favorite band.
        https://www.youtube.com/watch?v=hRguZr0xCOc&feature=youtu.be&t=212
        """
        # WHY: this is a post-detail-resolution hook.  It runs after ALL
        # monitoring_details have been promoted to attributes on the object
        # but before create_templates/create_hostgroups/create_contacts.
        # Subclasses override it to perform cross-detail reconciliation
        # (e.g. merging LOGIN credentials into URL details, setting host
        # macros from application details, or adding hostgroups based on
        # detail values).  The base implementation is intentionally a no-op.
        pass

    def pythonize(self) -> None:
        # WHY: datasources deliver list-type attributes as comma-separated
        # strings (Nagios format).  pythonize converts them to Python lists
        # so code can use append/extend/set operations.  depythonize is the
        # inverse, called before rendering to restore Nagios-compatible CSV.
        # The render_cfg_template cycle is: depythonize → render → pythonize,
        # so list form is the "resting state" between renders.  Note that
        # depythonize deduplicates and sorts all attributes EXCEPT templates
        # (template ordering matters for Nagios config inheritance).
        if hasattr(self, "templates"):
            self.templates = self.templates.split(',')
        if hasattr(self, "contactgroups"):
            self.contactgroups = self.contactgroups.split(',')
        if hasattr(self, "contact_groups"): #! contacts have contact!_!groups
            self.contact_groups = self.contact_groups.split(',')
        if hasattr(self, "contacts"):
            self.contacts = self.contacts.split(',')
        if hasattr(self, "hostgroups"):
            self.hostgroups = self.hostgroups.split(',')
        if hasattr(self, "servicegroups"):
            self.servicegroups = self.servicegroups.split(',')
        if hasattr(self, "members"):
            self.members = self.members.split(',')
        if hasattr(self, "parents"):
            self.parents = self.parents.split(',')
        if hasattr(self, "host_notification_commands"):
            self.host_notification_commands = self.host_notification_commands.split(',')
        if hasattr(self, "service_notification_commands"):
            self.service_notification_commands = self.service_notification_commands.split(',')

    def depythonize(self) -> None:
        if hasattr(self, "templates"):
            self.templates = ",".join(self.templates)
        if hasattr(self, "contactgroups"):
            self.contactgroups = ",".join(sorted(list(set(self.contactgroups))))
        if hasattr(self, "contact_groups"):
            self.contact_groups = ",".join(sorted(list(set(self.contact_groups))))
        if hasattr(self, "contacts"):
            self.contacts = ",".join(sorted(list(set(self.contacts))))
        if hasattr(self, "hostgroups"):
            self.hostgroups = ",".join(sorted(list(set(self.hostgroups))))
        if hasattr(self, "servicegroups"):
            self.servicegroups = ",".join(sorted(list(set(self.servicegroups))))
        if hasattr(self, "members"):
            self.members = ",".join(sorted(list(set(self.members))))
        if hasattr(self, "parents"):
            self.parents = ",".join(sorted(list(set(self.parents))))
        if hasattr(self, "host_notification_commands"):
            self.host_notification_commands = ",".join(sorted(list(set(self.host_notification_commands))))
        if hasattr(self, "service_notification_commands"):
            self.service_notification_commands = ",".join(sorted(list(set(self.service_notification_commands))))

    def render_cfg_template(self, jinja2: Any, template_cache: dict[str, Any], name: str, output_name: str, suffix: str, for_tool: str, _skip_pythonize: bool = False, **kwargs: Any) -> int:
        """Load a single Jinja2 template and render it into ``config_files``.

        Parameters
        ----------
        jinja2 : object
            Object whose ``env`` attribute is a Jinja2 Environment.
        template_cache : dict
            Shared cache mapping template names to compiled Template objects.
        name : str
            Logical template name (without ``.tpl`` extension).
        output_name : str
            Base filename for the rendered output.
        suffix : str
            File extension appended to *output_name* (e.g. ``'cfg'``).
            When empty the file is written without an extension.
        for_tool : str
            Monitoring tool key (e.g. ``'nagios'``, ``'prometheus'``)
            under which the output is stored in ``self.config_files``.
        **kwargs
            Extra variables passed into the Jinja2 render context
            (typically ``self`` and the active recipe).

        Returns
        -------
        int
            Number of rendering errors encountered (0 on success).
        """
        # WHY: render_errors is a counter that accumulates Jinja2 rendering
        # failures without aborting the whole run.  The caller aggregates
        # the total so that coshsh can report how many templates failed
        # while still producing output for everything that succeeded.
        render_errors = 0
        try:
            if not name in template_cache:
                template_cache[name] = jinja2.env.get_template(name + ".tpl")
                logger.info("load template " + name)
        except TemplateSyntaxError as e:
            logger.critical("%s template %s has an error in line %d: %s" % (self.__class__.__name__, name, e.lineno, e.message), exc_info=1)
            render_errors += 1
        except TemplateNotFound:
            logger.error("cannot find template " + name)
        except Exception as exp:
            logger.critical("error in template %s (%s,%s)" % (name, exp.__class__.__name__, exp), exc_info=1)
            render_errors += 1

        if name in template_cache:
            if not _skip_pythonize:
                # transform hostgroups, contacts, etc. from list to string
                self.depythonize()
            try:
                if not for_tool in self.config_files:
                    self.config_files[for_tool] = {}
                if suffix:
                    self.config_files[for_tool][output_name + "." + suffix] = template_cache[name].render(kwargs)
                else:
                    # files without suffix
                    self.config_files[for_tool][output_name] = template_cache[name].render(kwargs)
            except Exception as exp:
                if hasattr(self, "fingerprint"):
                    logger.critical("render exception in template %s for %s %s: %s" % (name, self, self.fingerprint(), exp), exc_info=1)
                else:
                    logger.critical("render exception in template %s for %s: %s" % (name, self, exp), exc_info=1)
                render_errors += 1
            if not _skip_pythonize:
                # transform hostgroups, contacts, etc. back to lists
                self.pythonize()
        return render_errors

    def render(self, template_cache: dict[str, Any], jinja2: Any, recipe: Any) -> int:
        """Render all applicable template rules for this item.

        Iterates over ``self.template_rules`` and evaluates each rule's
        conditions (``needsattr`` / ``isattr``) against the current
        object state.  When a rule matches it delegates to
        ``render_cfg_template`` to produce the output.

        Returns the total number of render errors across all rules.
        """
        render_errors = 0
        if not hasattr(self, 'template_rules'):
            return render_errors
        self.depythonize()
        for rule in self.template_rules:
            render_this = False
            try:
                if not rule.needsattr:
                    # TemplateRule(template="os_solaris_default")
                    render_this = True
    
                elif (hasattr(self, rule.needsattr) and rule.isattr == None):
                    # TemplateRule(needsattr=None,template="os_solaris_default")
                    render_this = True
    
                elif hasattr(self, rule.needsattr) and not isinstance (getattr(self, rule.needsattr), list) and ((getattr(self, rule.needsattr) == rule.isattr) or rule._isattr_re.match(getattr(self, rule.needsattr))):
                    # TemplateRule(needsattr="cluster", isattr="veritas",
                    #     template="os_solaris_cluster_veritas")
                    render_this = True

                elif hasattr(self, rule.needsattr) and isinstance (getattr(self, rule.needsattr), list) and any(elem == rule.isattr or rule._isattr_re.match(elem) for elem in getattr(self, rule.needsattr)):
                    # TemplateRule(needsattr="hostgroups",
                    #     isattr="cluster_solaris_veritas.*",
                    #     template="os_solaris_cluster_veritas")
                    render_this = True
                    
                elif hasattr(self, rule.needsattr) and isinstance (getattr(self, rule.needsattr), list):
                    pass
            except Exception as e:
                logger.critical("error in %s template rules. please check %s. Error was: %s" % (self.__class__.__name__, rule, str(e)), exc_info=1)
                render_errors += 1

            if render_this:
                # WHY: unique_config generates per-instance filenames
                # (e.g. one file per filesystem, one per URL) by
                # interpolating unique_attr values into a format string.
                # Default (else branch) generates one file per template
                # rule, using the template name as the output filename.
                if rule.unique_config and isinstance(rule.unique_attr, str) and hasattr(self, rule.unique_attr):
                    render_errors += self.render_cfg_template(jinja2, template_cache, rule.template, rule.unique_config % getattr(self, rule.unique_attr), rule.suffix, rule.for_tool, _skip_pythonize=True, **dict([(rule.self_name, self), ("recipe", recipe)]))
                elif rule.unique_config and isinstance(rule.unique_attr, list) and functools.reduce(lambda x, y: x and y, [hasattr(self, ua) for ua in rule.unique_attr]):
                    render_errors += self.render_cfg_template(jinja2, template_cache, rule.template, rule.unique_config % tuple([getattr(self, a) for a in rule.unique_attr]), rule.suffix, rule.for_tool, _skip_pythonize=True, **dict([(rule.self_name, self), ("recipe", recipe)]))
                else:
                    render_errors += self.render_cfg_template(jinja2, template_cache, rule.template, rule.template, rule.suffix, rule.for_tool, _skip_pythonize=True, **dict([(rule.self_name, self), ("recipe", recipe)]))
        self.pythonize()
        return render_errors

    def fingerprint(self) -> str:
        try:
            return f"{self.host_name}+{self.name}+{self.type}"
        except AttributeError:
            pass
        try:
            return f"{self.host_name}"
        except AttributeError:
            pass
        raise "impossible fingerprint"

