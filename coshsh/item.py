#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Item base class for all monitoring objects.

This module defines the Item class which is the base class for all
monitoring objects (Hosts, Applications, Contacts, etc.). It provides
template rendering, monitoring detail resolution, and configuration
file generation.
"""

from __future__ import annotations

import os
import re
import locale
import logging
import functools
from typing import Dict, Any, Optional, List, Union
from jinja2 import FileSystemLoader, Environment, TemplateSyntaxError, TemplateNotFound
from copy import copy, deepcopy

import coshsh

logger = logging.getLogger('coshsh')


class EmptyObject:
    """Placeholder object for dynamic attribute assignment.

    Used when creating nested attribute structures on-the-fly
    during monitoring detail resolution.
    """
    pass


class Item(coshsh.datainterface.CoshshDatainterface):
    """Base class for all monitoring objects.

    Item is the foundation for Hosts, Applications, Contacts, and other
    monitoring objects. It provides:
        - Template rendering via Jinja2
        - Monitoring detail resolution
        - Configuration file generation
        - Object lifecycle tracking (chronicle)

    Attributes:
        monitoring_details: List of MonitoringDetail objects to be resolved
        config_files: Dict of rendered configuration files by tool
        object_chronicle: List of lifecycle messages for debugging
        template_cache: Class-level cache of compiled templates
        env: Jinja2 environment for template rendering
        templates_path: Path to template directory

    Template Rendering:
        Items render configuration files using Jinja2 templates.
        Each subclass defines template_rules that specify which
        templates to use and when.

    Monitoring Details:
        MonitoringDetails provide additional configuration data.
        The resolve_monitoring_details() method converts these
        into object attributes, supporting:
            - Generic attributes (set directly)
            - List properties (append to lists)
            - Dict properties (add to dictionaries)
            - Nested attributes (dict:key syntax)
            - Unique attributes (replace existing)

    Configuration Files:
        Rendered templates are stored in config_files dict:
            config_files[tool][filename] = content
        Example: config_files['nagios']['host_web01.cfg'] = '...'

    Chronicle:
        Object lifecycle events are recorded in object_chronicle
        for debugging and auditing purposes.
    """

    # Class-level template cache shared by all instances
    template_cache: Dict[str, Any] = {}

    @classmethod
    def reload_template_path(cls) -> None:
        """Reload Jinja2 environment with current template path.

        Creates a new Jinja2 environment with FileSystemLoader pointing
        to cls.templates_path. Sets trim_blocks for cleaner output.

        Note:
            Called by Recipe when template path changes or on initialization.
        """
        loader = FileSystemLoader(cls.templates_path)
        cls.env = Environment(loader=loader)
        cls.env.trim_blocks = True

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """Initialize an Item with parameters.

        Args:
            params: Dictionary of object attributes

        String Handling:
            By default, string values are stripped of whitespace.
            Control this with dont_strip_attributes:
                - True: Never strip strings
                - List: Don't strip attributes in list
                - Otherwise: Strip all strings

        Monitoring Details:
            If the class defines monitoring_details, it's copied to
            the instance. Otherwise, an empty list is created.
        """
        params = params or {}

        # Set attributes from params
        for key in params:
            if hasattr(self, "dont_strip_attributes") and isinstance(params[key], str):
                # Check dont_strip_attributes configuration
                if isinstance(self.dont_strip_attributes, bool) and self.dont_strip_attributes:
                    setattr(self, key, params[key])
                elif isinstance(self.dont_strip_attributes, list) and key in self.dont_strip_attributes:
                    setattr(self, key, params[key])
                else:
                    setattr(self, key, params[key].strip())
            elif isinstance(params[key], str):
                # Default: strip whitespace from strings
                setattr(self, key, params[key].strip())
            else:
                # Non-strings: set as-is
                setattr(self, key, params[key])

        # Initialize or copy monitoring_details
        if not hasattr(self, "monitoring_details"):
            self.monitoring_details: List[Any] = []
        else:
            # Copy class-level monitoring_details to instance
            setattr(self, "monitoring_details", list(self.__class__.monitoring_details))

        # Initialize configuration storage
        self.config_files: Dict[str, Dict[str, str]] = {}
        self.object_chronicle: List[str] = []

    def record_in_chronicle(self, message: str = "") -> None:
        """Record a lifecycle event in the object chronicle.

        Args:
            message: Description of the event

        Note:
            Chronicle entries help debug object creation, modification,
            and rendering processes.
        """
        if message:
            self.object_chronicle.append(message)

    def write_config(
        self,
        target_dir: str,
        want_tool: Optional[str] = None
    ) -> None:
        """Write configuration files to disk.

        Creates a subdirectory under target_dir/hosts/<host_name>/
        and writes all rendered configuration files.

        Args:
            target_dir: Base directory for output
            want_tool: Optional specific tool to write configs for
                      (e.g., "nagios", "icinga"). If None, writes all tools.

        Example:
            item.write_config("/etc/nagios/objects", "nagios")
            # Creates: /etc/nagios/objects/hosts/web01/host_web01.cfg
        """
        my_target_dir = os.path.join(target_dir, "hosts", self.host_name)
        if not os.path.exists(my_target_dir):
            os.makedirs(my_target_dir)

        for tool in self.config_files:
            if not want_tool or want_tool == tool:
                for filename in self.config_files[tool]:
                    content = self.config_files[tool][filename]
                    filepath = os.path.join(my_target_dir, filename)

                    with open(filepath, "w") as f:
                        f.write(content)

    def resolve_monitoring_details(self) -> None:
        """Resolve monitoring details into object attributes.

        This complex method processes monitoring_details and converts
        them into object attributes. It supports multiple patterns:

        Generic Properties:
            - dict: Sets attributes from dictionary keys
            - dict with "key:subkey": Creates nested attributes
            - list: Extends or creates list attributes
            - scalar: Sets single attribute

        Named Properties:
            - list: Appends to or creates list attribute
            - dict: Adds key/value pairs to dictionary
            - object: Sets object reference

        Unique Attributes:
            If a detail has unique_attribute defined, it replaces
            any existing detail with the same attribute value.

        Property Flattening:
            If property_flat is True, the detail's property value
            is set directly rather than the detail object.

        Post-Processing:
            After resolution, calls wemustrepeat() for subclass hooks,
            then handles singular/plural property name conversions.

        Note:
            Each detail is removed from monitoring_details after
            resolution to prevent duplicate processing.
        """
        details = [d for d in self.monitoring_details]

        for detail in details:
            property = detail.__class__.property

            if property == "generic":
                # Generic property - sets attributes directly
                if detail.__class__.property_type == dict:
                    for key in detail.dictionary:
                        if key:
                            if ":" in key:
                                # Nested attribute: "macros:_CUSTOM"
                                dictname, key_part = key.split(":")
                                try:
                                    setattr(
                                        getattr(self, dictname),
                                        key_part,
                                        detail.dictionary[dictname + ":" + key_part]
                                    )
                                except AttributeError:
                                    # Create nested object if doesn't exist
                                    setattr(self, dictname, EmptyObject())
                                    setattr(
                                        getattr(self, dictname),
                                        key_part,
                                        detail.dictionary[dictname + ":" + key_part]
                                    )
                            else:
                                # Simple attribute
                                setattr(self, key, detail.dictionary[key])

                elif detail.__class__.property_type == list:
                    for key in detail.dictionary:
                        if key:
                            try:
                                getattr(self, key).extend(detail.dictionary[key])
                            except AttributeError:
                                setattr(self, key, detail.dictionary[key])
                else:
                    # Scalar property
                    setattr(self, detail.attribute, detail.value)

            else:
                # Named property
                if detail.__class__.property_type == list:
                    # Create list if doesn't exist
                    if not hasattr(self, property):
                        setattr(self, property, [])

                    if hasattr(detail.__class__, "unique_attribute"):
                        # Replace existing detail with same unique attribute
                        existing = [
                            o for o in getattr(self, property)
                            if o.__class__ == detail.__class__ and
                            getattr(o, detail.__class__.unique_attribute) ==
                            getattr(detail, detail.__class__.unique_attribute)
                        ]

                        if existing:
                            # Remove old, add new
                            old = getattr(self, property)
                            new = [
                                o for o in old
                                if not (o.__class__ == detail.__class__ and
                                        getattr(o, detail.__class__.unique_attribute) ==
                                        getattr(detail, detail.__class__.unique_attribute))
                            ]
                            new.append(detail)
                            setattr(self, property, new)
                        else:
                            getattr(self, property).append(detail)
                    else:
                        # Append to list
                        if hasattr(detail.__class__, "property_attr"):
                            # Append specific attribute of detail
                            getattr(self, property).append(
                                getattr(detail, getattr(detail.__class__, "property_attr"))
                            )
                        else:
                            # Append detail object
                            getattr(self, property).append(detail)

                elif detail.__class__.property_type == dict:
                    # Create dict if doesn't exist
                    if not hasattr(self, property):
                        setattr(self, property, {})

                    if hasattr(detail, "key") and hasattr(detail, "value"):
                        getattr(self, property)[detail.key] = detail.value

                else:
                    # Object property
                    if getattr(detail.__class__, 'property_flat', False):
                        # Flatten: set property value instead of detail object
                        # Ex: appl.role = "webserver" instead of appl.role.role = "webserver"
                        setattr(self, property, getattr(detail, property))
                    else:
                        setattr(self, property, detail)

            # Remove resolved detail to prevent re-processing
            self.monitoring_details.remove(detail)

        # Call subclass hook
        self.wemustrepeat()

        # Handle singular/plural property name conversion
        # If we have self.ports = [port1, port2] and self.port exists,
        # replace self.port with self.ports[0].port
        for one_property in [
            detail.__class__.property.rstrip('s')
            for detail in details
            if (detail.__class__.property_type == list and
                not hasattr(detail.__class__, "unique_attribute") and
                not hasattr(detail.__class__, "property_attr") and
                detail.__class__.property.endswith('s') and
                hasattr(self, detail.__class__.property.rstrip('s')))
        ]:
            if (hasattr(self, one_property + 's') and
                getattr(self, one_property + 's') and
                hasattr(getattr(self, one_property + 's')[0], one_property)):
                setattr(
                    self,
                    one_property,
                    getattr(getattr(self, one_property + 's')[0], one_property)
                )

    def wemustrepeat(self) -> None:
        """Hook method for subclasses to interact with monitoring details.

        This method is called during resolve_monitoring_details() to allow
        subclasses to perform additional processing when different types
        of monitoring details need to interact.

        Example:
            Username/password from LOGIN detail and URL detail need to
            be merged or validated together.

        Note:
            The name is a tribute to the band Rotersand.
            https://www.youtube.com/watch?v=hRguZr0xCOc&feature=youtu.be&t=212
        """
        pass

    def pythonize(self) -> None:
        """Convert comma-separated string attributes to lists.

        Transforms string attributes into list format for easier
        processing in Python. Handles these attributes:
            - templates, contactgroups, contact_groups
            - contacts, hostgroups, servicegroups
            - members, parents
            - host_notification_commands, service_notification_commands

        Example:
            Before: self.contacts = "admin,ops,dev"
            After:  self.contacts = ["admin", "ops", "dev"]
        """
        if hasattr(self, "templates"):
            self.templates = self.templates.split(',')
        if hasattr(self, "contactgroups"):
            self.contactgroups = self.contactgroups.split(',')
        if hasattr(self, "contact_groups"):  # contacts have contact_groups
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
        """Convert list attributes to comma-separated strings.

        Transforms list attributes into Nagios/Icinga compatible
        comma-separated format. Also sorts and deduplicates values.

        Example:
            Before: self.contacts = ["ops", "admin", "dev", "ops"]
            After:  self.contacts = "admin,dev,ops"

        Note:
            templates are not sorted/deduplicated to preserve order
        """
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

    def render_cfg_template(
        self,
        jinja2: Any,
        template_cache: Dict[str, Any],
        name: str,
        output_name: str,
        suffix: str,
        for_tool: str,
        **kwargs: Any
    ) -> int:
        """Render a single configuration template.

        Args:
            jinja2: Jinja2 environment wrapper
            template_cache: Dictionary of cached compiled templates
            name: Template name (without .tpl extension)
            output_name: Base name for output file
            suffix: File extension (cfg, conf, etc.)
            for_tool: Tool name (nagios, icinga, etc.)
            **kwargs: Variables to pass to template (self, recipe, etc.)

        Returns:
            Number of errors encountered (0 for success)

        Process:
            1. Load/cache template
            2. Convert lists to strings via depythonize()
            3. Render template with kwargs
            4. Store in config_files[for_tool][filename]
            5. Convert back to lists via pythonize()

        Note:
            Template errors are logged but don't stop processing
        """
        render_errors = 0

        # Load template (with caching)
        try:
            if name not in template_cache:
                template_cache[name] = jinja2.env.get_template(name + ".tpl")
                logger.info(f"load template {name}")
        except TemplateSyntaxError as e:
            logger.critical(
                f"{self.__class__.__name__} template {name} has an error "
                f"in line {e.lineno}: {e.message}",
                exc_info=1
            )
            render_errors += 1
        except TemplateNotFound:
            logger.error(f"cannot find template {name}")
        except Exception as exp:
            logger.critical(
                f"error in template {name} ({exp.__class__.__name__},{exp})",
                exc_info=1
            )
            render_errors += 1

        # Render template
        if name in template_cache:
            # Convert lists to comma-separated strings
            self.depythonize()

            try:
                # Initialize tool dict if needed
                if for_tool not in self.config_files:
                    self.config_files[for_tool] = {}

                # Render and store
                if suffix:
                    self.config_files[for_tool][output_name + "." + suffix] = \
                        template_cache[name].render(kwargs)
                else:
                    # Files without suffix
                    self.config_files[for_tool][output_name] = \
                        template_cache[name].render(kwargs)

            except Exception as exp:
                if hasattr(self, "fingerprint"):
                    logger.critical(
                        f"render exception in template {name} for {self} "
                        f"{self.fingerprint()}: {exp}",
                        exc_info=1
                    )
                else:
                    logger.critical(
                        f"render exception in template {name} for {self}: {exp}",
                        exc_info=1
                    )
                render_errors += 1

            # Convert back to lists
            self.pythonize()

        return render_errors

    def render(
        self,
        template_cache: Dict[str, Any],
        jinja2: Any,
        recipe: Any
    ) -> int:
        """Render all templates for this object based on template_rules.

        Template rules control which templates are rendered:
            - needsattr: Attribute that must exist
            - isattr: Value or regex that attribute must match
            - template: Template name to render
            - unique_attr: Attribute(s) for unique output filename
            - unique_config: Filename pattern with %s placeholders

        Args:
            template_cache: Dictionary of cached templates
            jinja2: Jinja2 environment wrapper
            recipe: Recipe object containing configuration

        Returns:
            Number of render errors encountered

        Template Rule Matching:
            - No needsattr: Always render
            - needsattr but no isattr: Render if attribute exists
            - needsattr + isattr: Render if attribute equals or matches isattr
            - needsattr + isattr + list: Render if any list element matches

        Example Rules:
            TemplateRule(template="host")
            -> Always render host template

            TemplateRule(needsattr="cluster", isattr="veritas",
                        template="host_veritas")
            -> Render if self.cluster == "veritas"
        """
        render_errors = 0

        if not hasattr(self, 'template_rules'):
            return render_errors

        for rule in self.template_rules:
            render_this = False

            try:
                if not rule.needsattr:
                    # No requirements - always render
                    render_this = True

                elif hasattr(self, rule.needsattr) and rule.isattr is None:
                    # Attribute exists and no value check required
                    render_this = True

                elif (hasattr(self, rule.needsattr) and
                      not isinstance(getattr(self, rule.needsattr), list) and
                      (getattr(self, rule.needsattr) == rule.isattr or
                       re.match(rule.isattr, getattr(self, rule.needsattr)))):
                    # Attribute value matches or regex matches
                    render_this = True

                elif (hasattr(self, rule.needsattr) and
                      isinstance(getattr(self, rule.needsattr), list) and
                      [elem for elem in getattr(self, rule.needsattr)
                       if elem == rule.isattr or re.match(rule.isattr, elem)]):
                    # List attribute has at least one matching element
                    render_this = True

                elif hasattr(self, rule.needsattr) and isinstance(getattr(self, rule.needsattr), list):
                    # Has attribute but no match - don't render
                    pass

            except Exception as e:
                logger.critical(
                    f"error in {self.__class__.__name__} template rules. "
                    f"please check {rule}. Error was: {e}",
                    exc_info=1
                )
                render_errors += 1

            if render_this:
                # Determine output filename
                if rule.unique_config and isinstance(rule.unique_attr, str) and hasattr(self, rule.unique_attr):
                    # Single unique attribute
                    render_errors += self.render_cfg_template(
                        jinja2, template_cache, rule.template,
                        rule.unique_config % getattr(self, rule.unique_attr),
                        rule.suffix, rule.for_tool,
                        **dict([(rule.self_name, self), ("recipe", recipe)])
                    )

                elif (rule.unique_config and isinstance(rule.unique_attr, list) and
                      functools.reduce(lambda x, y: x and y,
                                      [hasattr(self, ua) for ua in rule.unique_attr])):
                    # Multiple unique attributes
                    render_errors += self.render_cfg_template(
                        jinja2, template_cache, rule.template,
                        rule.unique_config % tuple([getattr(self, a) for a in rule.unique_attr]),
                        rule.suffix, rule.for_tool,
                        **dict([(rule.self_name, self), ("recipe", recipe)])
                    )

                else:
                    # No unique config - use template name as filename
                    render_errors += self.render_cfg_template(
                        jinja2, template_cache, rule.template,
                        rule.template, rule.suffix, rule.for_tool,
                        **dict([(rule.self_name, self), ("recipe", recipe)])
                    )

        return render_errors

    def fingerprint(self) -> Union[str, int]:
        """Return unique identifier for this object.

        Tries multiple strategies:
            1. host_name + name + type (for applications)
            2. host_name alone (for hosts)
            3. Raises ValueError if impossible

        Returns:
            Fingerprint string

        Raises:
            ValueError: If no valid fingerprint can be constructed

        Note:
            Subclasses typically override this with specific logic
        """
        try:
            return f"{self.host_name}+{self.name}+{self.type}"
        except AttributeError:
            pass

        try:
            return f"{self.host_name}"
        except AttributeError:
            pass

        raise ValueError("Cannot construct fingerprint - missing required attributes")
