#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Recipe class - main orchestration for monitoring config generation.

This module defines the Recipe class which orchestrates the entire
config generation pipeline:
    - Loading plugins (datasources, applications, contacts, etc.)
    - Reading data from datasources
    - Assembling object hierarchies
    - Rendering templates
    - Writing output via datarecipients
"""

from __future__ import annotations

import sys
import os
import io
import re
import inspect
import time
import logging
import errno
from typing import Dict, List, Any, Optional, Tuple, Union
from jinja2 import FileSystemLoader, Environment, TemplateSyntaxError, TemplateNotFound

import coshsh

logger = logging.getLogger('coshsh')


class EmptyObject:
    """Placeholder object for dynamic attribute assignment.

    Used for creating ad-hoc objects with arbitrary attributes
    (e.g., jinja2 wrapper with loader and env attributes).
    """
    pass


class RecipePidAlreadyRunning(Exception):
    """Raised when another recipe instance is already running.

    Indicates that a PID file exists and points to a running process.
    """
    pass


class RecipePidNotWritable(Exception):
    """Raised when PID file or directory is not writable.

    Indicates insufficient filesystem permissions for PID file management.
    """
    pass


class RecipePidGarbage(Exception):
    """Raised when PID file contains invalid data.

    Indicates that the PID file exists but doesn't contain a valid
    integer process ID.
    """
    pass


class Recipe:
    """Main orchestration class for monitoring config generation.

    The Recipe class coordinates the entire config generation pipeline:

    1. Initialization
        - Sets up paths for classes and templates
        - Initializes Jinja2 environment
        - Loads plugin class factories
        - Creates vaults, datasources, datarecipients

    2. Collection (collect)
        - Opens datasources
        - Reads monitoring data
        - Populates object dictionaries

    3. Assembly (assemble)
        - Attaches monitoring details to hosts/applications
        - Resolves monitoring details
        - Creates hostgroups
        - Establishes object relationships

    4. Rendering (render)
        - Renders Jinja2 templates for all objects
        - Generates configuration files

    5. Output (output)
        - Writes configuration files via datarecipients
        - Handles cleanup and preparation

    Attributes:
        name: Recipe name
        classes_path: List of directories for plugin classes
        templates_path: List of directories for Jinja2 templates
        objects: Dict of monitoring objects by type
        datasources: List of Datasource instances
        datarecipients: List of Datarecipient instances
        vaults: List of Vault instances for secret management
        vault_secrets: Dict of secrets loaded from vaults
        jinja2: Jinja2 environment wrapper
        render_errors: Count of template rendering errors

    Plugin Management:
        Recipes manage three types of plugins:
        - Datasources (read monitoring data)
        - Datarecipients (write monitoring configs)
        - Item classes (Applications, Contacts, MonitoringDetails)

    Path Priority:
        User paths override default paths for both classes and templates.
        "catchall" directories always come last in priority.

    Environment Variables:
        - RECIPE_NAME: Set to recipe name
        - RECIPE_NAME1, RECIPE_NAME2, etc: Set to name components
        - env_* parameters: Exported as environment variables

    Configuration Mappings:
        @MAPPING_NAME[key] syntax allows configuration value substitution.

    Vault Integration:
        @VAULT[identifier] syntax allows secret substitution from vaults.

    Example Usage:
        recipe = Recipe(
            name="production",
            classes_dir="/custom/classes",
            templates_dir="/custom/templates",
            datasources="mysql,ldap",
            objects_dir="/etc/nagios/conf.d"
        )

        recipe.add_datasource(type="mysql", name="cmdb", ...)
        recipe.pid_protect()
        recipe.collect()
        recipe.assemble()
        recipe.render()
        recipe.output()
        recipe.pid_remove()
    """

    # Attributes that are passed to datasources/datarecipients
    attributes_for_adapters = [
        "name", "force", "safe_output", "pid_dir", "pid_file",
        "templates_dir", "classes_dir", "objects_dir",
        "max_delta", "max_delta_action", "classes_path",
        "templates_path", "filter", "git_init"
    ]

    def __del__(self) -> None:
        """Cleanup on deletion.

        Note:
            Cannot unset sys.path here as it's already invisible.
        """
        pass

    def __init__(self, **kwargs: Any):
        """Initialize a Recipe with configuration.

        Args:
            **kwargs: Recipe configuration including:
                - name: Required recipe name
                - classes_dir: Comma-separated list of class directories
                - templates_dir: Comma-separated list of template directories
                - datasources: Comma-separated list of datasource names
                - datarecipients: Comma-separated list of datarecipient names
                - objects_dir: Output directory (shortcut for default datarecipient)
                - vaults: Comma-separated list of vault names
                - filter: Datasource filter expressions
                - max_delta: Max change threshold (single int or min:max)
                - max_delta_action: Action when max_delta exceeded
                - log_dir, log_file: Logging configuration
                - force: Force regeneration
                - safe_output: Safe mode for output
                - pid_dir: Directory for PID file
                - git_init: Initialize git repo in output (default: yes)
                - coshsh_config_mappings: Dict of configuration mappings
                - my_jinja2_extensions: Custom Jinja2 extensions
                - env_*: Environment variables to set

        Environment Setup:
            Sets RECIPE_NAME and splits name into RECIPE_NAME1, RECIPE_NAME2, etc.

        Variable Expansion:
            - %ENV_VAR%: Expands environment variables
            - @MAPPING_NAME[key]: Expands configuration mappings
            - @VAULT[identifier]: Expands vault secrets

        Path Priority:
            User paths before default paths, catchall directories last.
        """
        # Set environment variables from recipe name
        os.environ['RECIPE_NAME'] = kwargs["name"]
        for idx, elem in enumerate(kwargs["name"].split("_")):
            os.environ[f'RECIPE_NAME{idx+1}'] = elem

        # Track additional recipe fields for passing to adapters
        self.additional_recipe_fields: Dict[str, str] = {}

        # Expand environment variables in all string parameters
        for key in list(kwargs.keys()):
            if isinstance(kwargs[key], str):
                kwargs[key] = re.sub('%.*?%', coshsh.util.substenv, kwargs[key])
                if key not in self.attributes_for_adapters:
                    self.additional_recipe_fields[key] = kwargs[key]

        # Expand configuration mappings (@MAPPING_NAME[key])
        for key in list(kwargs.keys()):
            if isinstance(kwargs[key], str):
                for mapping in kwargs.get("coshsh_config_mappings", {}):
                    mapping_keyword_pat = f"(@MAPPING_{mapping.upper()}\\[(.*?)\\])"
                    for match in re.findall(mapping_keyword_pat, kwargs[key]):
                        if match[1] in kwargs["coshsh_config_mappings"][mapping]:
                            oldstr = f"@MAPPING_{mapping.upper()}[{match[1]}]"
                            newstr = kwargs["coshsh_config_mappings"][mapping][match[1]]
                            kwargs[key] = kwargs[key].replace(oldstr, newstr)

        # Set environment variables from env_* parameters
        for key in list(kwargs.keys()):
            if isinstance(kwargs[key], str) and key.startswith("env_"):
                os.environ[key.replace("env_", "").upper()] = kwargs[key]

        # Basic attributes
        self.name: str = kwargs["name"]
        self.log_file: Optional[str] = kwargs.get("log_file", None)
        self.log_dir: Optional[str] = kwargs.get("log_dir", None)
        self.backup_count: Optional[int] = kwargs.get("backup_count", None)

        # Configure logging
        coshsh.util.switch_logging(
            logdir=self.log_dir,
            logfile=self.log_file,
            backup_count=self.backup_count
        )
        logger.info(f"recipe {self.name} init")

        # Operation modes
        self.force: Optional[bool] = kwargs.get("force")
        self.safe_output: Optional[bool] = kwargs.get("safe_output")

        # PID file management
        self.pid_dir: str = kwargs.get("pid_dir") or self._default_pid_dir()
        self.pid_file: str = os.path.join(
            self.pid_dir,
            "coshsh.pid." + re.sub(r'[/\.]', '_', self.name)
        )

        # Directory configuration
        self.templates_dir: Optional[str] = kwargs.get("templates_dir")
        self.classes_dir: Optional[str] = kwargs.get("classes_dir")

        # Delta checking
        self.max_delta: Union[Tuple[int, int], Tuple[()]] = kwargs.get("max_delta", ())
        self.max_delta_action: Optional[str] = kwargs.get("max_delta_action", None)
        if isinstance(self.max_delta, str):
            if ":" in self.max_delta:
                self.max_delta = tuple(map(int, self.max_delta.split(":")))
            else:
                val = int(self.max_delta)
                self.max_delta = (val, val)

        # Jinja2 extensions
        self.my_jinja2_extensions: Optional[str] = kwargs.get("my_jinja2_extensions", None)

        # Git initialization
        self.git_init: bool = False if kwargs.get("git_init", "yes") == "no" else True

        # Set up classes path (user paths + defaults, catchall last)
        self.classes_path: List[str] = self._init_classes_path()
        self.set_recipe_sys_path()

        # Set up templates path (user paths + defaults, catchall last)
        self.templates_path: List[str] = self._init_templates_path()
        logger.info(f"recipe {self.name} classes_dir {','.join([os.path.abspath(p) for p in self.classes_path])}")
        logger.info(f"recipe {self.name} templates_dir {','.join([os.path.abspath(p) for p in self.templates_path])}")

        # Initialize Jinja2 environment
        self._init_jinja2()

        # Initialize collections
        self.vaults: List[Any] = []
        self.vault_secrets: Dict[str, str] = {}
        self.datasources: List[Any] = []
        self.datarecipients: List[Any] = []

        # Object storage
        self.objects: Dict[str, Dict[Any, Any]] = {
            'hosts': {},
            'hostgroups': {},
            'applications': {},
            'details': {},
            'contacts': {},
            'contactgroups': {},
            'commands': {},
            'timeperiods': {},
            'dependencies': {},
            'bps': {},
        }

        # Object counters
        self.old_objects: Tuple[int, int] = (0, 0)
        self.new_objects: Tuple[int, int] = (0, 0)

        # Initialize plugin class factories
        self.init_vault_class_factories()
        self.init_ds_dr_class_factories()
        self.init_item_class_factories()

        # Parse vault names
        if kwargs.get("vaults"):
            self.vault_names: List[str] = [
                vault.lower().strip() for vault in kwargs.get("vaults").split(",")
            ]
        else:
            self.vault_names = []

        # Parse datasource names
        if kwargs.get("datasources"):
            self.datasource_names: List[str] = [
                ds.lower().strip() for ds in kwargs.get("datasources").split(",")
            ]
        else:
            self.datasource_names = []

        # Parse datarecipient names
        self._init_datarecipients(kwargs)

        # Parse datasource filters
        self._init_datasource_filters(kwargs)

        self.render_errors: int = 0

    def _default_pid_dir(self) -> str:
        """Determine default PID directory based on environment."""
        if 'OMD_ROOT' in os.environ:
            return os.path.join(os.environ['OMD_ROOT'], 'tmp/run')
        elif "cygwin" in sys.platform or "linux" in sys.platform:
            return "/tmp"
        else:
            return os.environ.get("%TEMP%", "C:/TEMP")

    def _init_classes_path(self) -> List[str]:
        """Initialize classes path with defaults and user paths."""
        if 'OMD_ROOT' in os.environ:
            default_path = [os.path.join(os.environ['OMD_ROOT'], 'share/coshsh/recipes/default/classes')]
        else:
            default_path = [os.path.join(os.path.dirname(__file__), '../recipes/default/classes')]

        if self.classes_dir:
            # User paths (non-catchall) + defaults + user paths (catchall)
            user_paths = [p.strip() for p in self.classes_dir.split(',')]
            non_catchall = [p for p in user_paths if os.path.basename(p) != 'catchall']
            catchall = [p for p in user_paths if os.path.basename(p) == 'catchall']
            return non_catchall + default_path + catchall
        else:
            return default_path

    def _init_templates_path(self) -> List[str]:
        """Initialize templates path with defaults and user paths."""
        if 'OMD_ROOT' in os.environ:
            default_path = [os.path.join(os.environ['OMD_ROOT'], 'share/coshsh/recipes/default/templates')]
        else:
            default_path = [os.path.join(os.path.dirname(__file__), '../recipes/default/templates')]

        if self.templates_dir:
            # User paths (non-catchall) + defaults + user paths (catchall)
            user_paths = [p.strip() for p in self.templates_dir.split(',')]
            non_catchall = [p for p in user_paths if os.path.basename(p) != 'catchall']
            catchall = [p for p in user_paths if os.path.basename(p) == 'catchall']
            paths = non_catchall + default_path + catchall
            logger.debug(f"recipe.templates_path reloaded {':'.join(paths)}")
            return paths
        else:
            return default_path

    def _init_jinja2(self) -> None:
        """Initialize Jinja2 environment with extensions and filters."""
        self.jinja2 = EmptyObject()
        setattr(self.jinja2, 'loader', FileSystemLoader(self.templates_path))
        setattr(self.jinja2, 'env', Environment(
            loader=self.jinja2.loader,
            extensions=['jinja2.ext.do']
        ))
        self.jinja2.env.trim_blocks = True

        # Register standard extensions
        self.jinja2.env.tests['re_match'] = coshsh.jinja2_extensions.is_re_match
        self.jinja2.env.filters['re_sub'] = coshsh.jinja2_extensions.filter_re_sub
        self.jinja2.env.filters['re_escape'] = coshsh.jinja2_extensions.filter_re_escape
        self.jinja2.env.filters['service'] = coshsh.jinja2_extensions.filter_service
        self.jinja2.env.filters['host'] = coshsh.jinja2_extensions.filter_host
        self.jinja2.env.filters['contact'] = coshsh.jinja2_extensions.filter_contact
        self.jinja2.env.filters['custom_macros'] = coshsh.jinja2_extensions.filter_custom_macros
        self.jinja2.env.filters['rfc3986'] = coshsh.jinja2_extensions.filter_rfc3986
        self.jinja2.env.filters['neighbor_applications'] = coshsh.jinja2_extensions.filter_neighbor_applications
        self.jinja2.env.globals['environ'] = coshsh.jinja2_extensions.global_environ

        # Register custom extensions
        if self.my_jinja2_extensions:
            for extension in [e.strip() for e in self.my_jinja2_extensions.split(",")]:
                imported = getattr(
                    __import__("my_jinja2_extensions", fromlist=[extension]),
                    extension
                )
                if extension.startswith("is_"):
                    self.jinja2.env.tests[extension.replace("is_", "")] = imported
                elif extension.startswith("filter_"):
                    self.jinja2.env.filters[extension.replace("filter_", "")] = imported
                elif extension.startswith("global_"):
                    self.jinja2.env.globals[extension.replace("global_", "")] = imported

    def _init_datarecipients(self, kwargs: Dict[str, Any]) -> None:
        """Initialize datarecipient configuration."""
        if kwargs.get("objects_dir") and not kwargs.get("datarecipients"):
            self.objects_dir: str = kwargs["objects_dir"]
            logger.info(f"recipe {self.name} objects_dir {os.path.abspath(self.objects_dir)}")
            self.datarecipient_names: List[str] = ["datarecipient_coshsh_default"]
        elif kwargs.get("objects_dir") and kwargs.get("datarecipients"):
            self.objects_dir = kwargs["objects_dir"]
            self.datarecipient_names = [
                ds.lower().strip() for ds in kwargs.get("datarecipients").split(",")
            ]
        else:
            self.datarecipient_names = [
                ds.lower().strip() for ds in kwargs.get("datarecipients", "").split(",")
            ]

        # Replace >>> shorthand with default datarecipient
        self.datarecipient_names = [
            'datarecipient_coshsh_default' if dr == '>>>' else dr
            for dr in self.datarecipient_names
        ]

        # Add default datarecipient if specified
        if 'datarecipient_coshsh_default' in self.datarecipient_names:
            self.add_datarecipient(**{
                'type': 'datarecipient_coshsh_default',
                'name': 'datarecipient_coshsh_default',
                'objects_dir': self.objects_dir,
                'max_delta': self.max_delta,
                'max_delta_action': self.max_delta_action,
                'safe_output': self.safe_output
            })

    def _init_datasource_filters(self, kwargs: Dict[str, Any]) -> None:
        """Parse datasource filter expressions."""
        self.datasource_filters: Dict[str, str] = {}
        self.filter: Optional[str] = kwargs.get("filter")

        if not self.filter:
            return

        dsfilter_p = re.compile(r'(([^,^(^)]+)\((.*?)\))')

        # First pass: handle regex datasource names
        for rule in dsfilter_p.findall(self.filter):
            if rule[1].lower() not in self.datasource_names:
                # Could be a regex
                tmp_dsname = rule[1]
                if not tmp_dsname.startswith("^"):
                    tmp_dsname = "^" + tmp_dsname
                if not tmp_dsname.endswith("$"):
                    tmp_dsname = tmp_dsname + "$"
                rule_p = re.compile(tmp_dsname)
                for ds in self.datasource_names:
                    if rule_p.match(ds):
                        self.datasource_filters[ds] = rule[2]

        # Second pass: handle direct matches (overrides regex)
        for rule in dsfilter_p.findall(self.filter):
            if rule[1].lower() in self.datasource_names:
                self.datasource_filters[rule[1].lower()] = rule[2]

    def set_recipe_sys_path(self) -> None:
        """Add classes_path to sys.path for plugin discovery."""
        sys.path[0:0] = self.classes_path

    def unset_recipe_sys_path(self) -> None:
        """Remove classes_path from sys.path."""
        for p in [p for p in self.classes_path if os.path.exists(p) and os.path.isdir(p)]:
            sys.path.pop(0)

    def collect(self) -> bool:
        """Collect data from all datasources.

        Opens each datasource, reads monitoring data, and populates
        the objects dictionary.

        Returns:
            True if all datasources succeeded, False otherwise

        Process:
            1. Open datasource
            2. Read data (with optional filter)
            3. Count objects read
            4. Close datasource
            5. Log results

        Error Handling:
            Catches and logs datasource exceptions:
            - DatasourceNotCurrent: Stale data
            - DatasourceNotReady: Update in progress
            - DatasourceNotAvailable: Connection failed
            - Other exceptions: General errors
        """
        data_valid = True

        for ds in self.datasources:
            filter_expr = self.datasource_filters.get(ds.name)

            try:
                ds.open()

                # Count objects before read
                pre_count = {key: len(self.objects[key]) for key in self.objects}
                pre_detail_count = sum(
                    len(obj.monitoring_details) if hasattr(obj, 'monitoring_details') else 99
                    for objs in self.objects.values()
                    for obj in objs.values()
                )

                # Read from datasource
                ds.read(filter=filter_expr, objects=self.objects, force=self.force)

                # Count objects after read
                post_count = {key: len(self.objects[key]) for key in self.objects}
                post_detail_count = sum(
                    len(obj.monitoring_details) if hasattr(obj, 'monitoring_details') else 99
                    for objs in self.objects.values()
                    for obj in objs.values()
                )

                # Calculate deltas
                pre_count['details'] = pre_detail_count
                post_count['details'] = post_detail_count
                pre_count.update(dict.fromkeys(
                    [k for k in post_count if k not in pre_count], 0
                ))

                chg_keys = [
                    (key, post_count[key] - pre_count[key])
                    for key in set(list(pre_count.keys()) + list(post_count.keys()))
                    if post_count[key] != pre_count[key]
                ]

                logger.info(
                    f"recipe {self.name} read from datasource {ds.name} "
                    f"{', '.join([f'{k[1]} {k[0]}' for k in chg_keys])}"
                )

                ds.close()

            except coshsh.datasource.DatasourceNotCurrent:
                data_valid = False
                logger.info(f"datasource {ds.name} is not current", exc_info=False)
            except coshsh.datasource.DatasourceNotReady:
                data_valid = False
                logger.info(f"datasource {ds.name} is busy", exc_info=False)
            except coshsh.datasource.DatasourceNotAvailable:
                data_valid = False
                logger.info(f"datasource {ds.name} is not available", exc_info=False)
            except Exception as exp:
                data_valid = False
                logger.critical(f"datasource {ds.name} returns bad data ({exp})", exc_info=True)

            if not data_valid:
                logger.info("aborting collection phase")
                return False

        return data_valid

    def assemble(self) -> bool:
        """Assemble object hierarchies and relationships.

        Returns:
            True on success

        Process:
            1. Attach monitoring details to applications/hosts
            2. Handle generic details (wildcards)
            3. Resolve monitoring details for hosts
            4. Create host templates, hostgroups, contacts
            5. Attach applications to hosts
            6. Resolve monitoring details for applications
            7. Create application templates, servicegroups, contacts
            8. Create hostgroup objects with members

        Generic Details:
            Details with '*' fingerprint apply to all hosts.
            Details with '*+type+name' apply to all apps of that type/name.

        Orphaned Applications:
            Applications referencing non-existent hosts are logged and removed.
        """
        # Attach monitoring details to applications/hosts
        generic_details: List[Any] = []

        for detail in self.objects['details'].values():
            fingerprint = detail.application_fingerprint()

            if fingerprint in self.objects['applications']:
                self.objects['applications'][fingerprint].monitoring_details.append(detail)
            elif fingerprint in self.objects['hosts']:
                self.objects['hosts'][fingerprint].monitoring_details.append(detail)
            elif fingerprint.startswith('*'):
                generic_details.append(detail)
            else:
                logger.info(
                    f"found a {detail.__class__.__name__} detail {detail} "
                    f"for an unknown application {fingerprint}"
                )

        # Apply generic details
        for detail in generic_details:
            dfingerprint = detail.application_fingerprint()

            if dfingerprint == '*':
                # Apply to all hosts
                for host in self.objects['hosts'].values():
                    host.monitoring_details.insert(0, detail)
            else:
                # Apply to matching applications
                for app in self.objects['applications'].values():
                    afingerprint = app.fingerprint()
                    if dfingerprint[1:] == afingerprint[afingerprint.index('+'):]:
                        app.monitoring_details.insert(0, detail)

        # Process hosts
        for host in self.objects['hosts'].values():
            host.resolve_monitoring_details()

            # Sort list/tuple attributes (except templates)
            for key in [
                k for k in host.__dict__.keys()
                if not k.startswith("__") and isinstance(getattr(host, k), (list, tuple))
                and k not in ["templates"]
            ]:
                getattr(host, key).sort()

            host.create_templates()
            host.create_hostgroups()
            host.create_contacts()
            setattr(host, "applications", [])

        # Process applications
        orphaned_applications: List[Any] = []

        for app in self.objects['applications'].values():
            try:
                # Link to host
                setattr(app, 'host', self.objects['hosts'][app.host_name])
                app.host.applications.append(app)

                app.resolve_monitoring_details()

                # Sort list/tuple attributes
                for key in [
                    k for k in app.__dict__.keys()
                    if not k.startswith("__") and isinstance(getattr(app, k), (list, tuple))
                ]:
                    getattr(app, key).sort()

                app.create_templates()
                app.create_servicegroups()
                app.create_contacts()

            except KeyError:
                logger.info(
                    f"application {app.name} {app.type} refers to "
                    f"non-existing host {app.host_name}"
                )
                orphaned_applications.append(app.fingerprint())

        # Remove orphaned applications
        for oa in orphaned_applications:
            del self.objects['applications'][oa]

        # Create hostgroups
        # (Done after application processing to allow modification in app.wemustrepeat())
        for host in self.objects['hosts'].values():
            for hostgroup in host.hostgroups:
                try:
                    self.objects['hostgroups'][hostgroup].append(host.host_name)
                except KeyError:
                    self.objects['hostgroups'][hostgroup] = []
                    self.objects['hostgroups'][hostgroup].append(host.host_name)

        for (hostgroup_name, members) in self.objects['hostgroups'].items():
            logger.debug(f"creating hostgroup {hostgroup_name}")
            self.objects['hostgroups'][hostgroup_name] = coshsh.hostgroup.HostGroup({
                "hostgroup_name": hostgroup_name,
                "members": members
            })
            self.objects['hostgroups'][hostgroup_name].create_templates()
            self.objects['hostgroups'][hostgroup_name].create_contacts()

        return True

    def render(self) -> None:
        """Render templates for all objects.

        Calls render() on all monitoring objects to generate
        configuration files from Jinja2 templates.

        Object Order:
            1. Hosts
            2. Applications
            3. Contact groups
            4. Contacts
            5. Hostgroups
            6. Other custom objects

        Template Cache:
            Compiled templates are cached for performance.

        Error Counting:
            Render errors are accumulated in self.render_errors.
        """
        template_cache: Dict[str, Any] = {}

        # Render hosts
        for host in self.objects['hosts'].values():
            self.render_errors += host.render(template_cache, self.jinja2, self)

        # Render applications
        for app in self.objects['applications'].values():
            self.render_errors += app.render(template_cache, self.jinja2, self)

        # Render contact groups
        for cg in self.objects['contactgroups'].values():
            self.render_errors += cg.render(template_cache, self.jinja2, self)

        # Render contacts
        for c in self.objects['contacts'].values():
            self.render_errors += c.render(template_cache, self.jinja2, self)

        # Render hostgroups
        for hg in self.objects['hostgroups'].values():
            self.render_errors += hg.render(template_cache, self.jinja2, self)

        # Render other custom objects
        for item in sum([
            list(self.objects[itype].values())
            for itype in self.objects
            if itype not in ['hosts', 'applications', 'details', 'contactgroups', 'contacts', 'hostgroups']
        ], []):
            # Only render if not already populated (e.g., from datasource)
            if hasattr(item, 'config_files') and not item.config_files:
                self.render_errors += item.render(template_cache, self.jinja2, self)

    def count_before_objects(self) -> None:
        """Count objects before output (for delta checking)."""
        for datarecipient in self.datarecipients:
            datarecipient.count_before_objects()

        self.old_objects = (
            sum([dr.old_objects[0] for dr in self.datarecipients], 0),
            sum([dr.old_objects[1] for dr in self.datarecipients], 0)
        )

    def count_after_objects(self) -> None:
        """Count objects after output (for delta checking)."""
        for datarecipient in self.datarecipients:
            datarecipient.count_after_objects()

        self.new_objects = (
            sum([dr.new_objects[0] for dr in self.datarecipients], 0),
            sum([dr.new_objects[1] for dr in self.datarecipients], 0)
        )

    def cleanup_target_dir(self) -> None:
        """Clean up output directories."""
        for datarecipient in self.datarecipients:
            datarecipient.cleanup_target_dir()

    def prepare_target_dir(self) -> None:
        """Prepare output directories."""
        for datarecipient in self.datarecipients:
            datarecipient.prepare_target_dir()

    def output(self) -> None:
        """Write configuration files via datarecipients.

        For each datarecipient:
            1. Count objects before
            2. Load objects
            3. Cleanup target directory (if not already cleaned)
            4. Prepare target directory
            5. Write output

        Note:
            Directories are only cleaned once even if multiple
            datarecipients write to the same location.
        """
        cleaned_dirs: List[str] = []

        for datarecipient in self.datarecipients:
            datarecipient.count_before_objects()
            datarecipient.load(None, self.objects)

            # Cleanup directory (only once per unique dir)
            if (hasattr(datarecipient, 'dynamic_dir') and
                datarecipient.dynamic_dir not in cleaned_dirs):
                datarecipient.cleanup_target_dir()
                cleaned_dirs.append(datarecipient.dynamic_dir)

            datarecipient.prepare_target_dir()
            datarecipient.output()

    def read(self) -> Dict[str, Dict[Any, Any]]:
        """Return the objects dictionary.

        Returns:
            Dictionary of monitoring objects by type
        """
        return self.objects

    def add_class_factory(
        self,
        cls: type,
        path: List[str],
        factory: List[Tuple[str, str, Any]]
    ) -> None:
        """Add a class factory for plugin discovery.

        Args:
            cls: Class type (e.g., Datasource, Application)
            path: Classpath used for discovery
            factory: List of (dirname, filename, ident_func) tuples
        """
        logger.debug(f"init {cls.__name__} classes ({len(factory)})")
        path_text = ",".join(path)

        if not hasattr(self, "class_factory"):
            self.class_factory: Dict[type, Dict[str, List[Tuple[str, str, Any]]]] = {}
        if cls not in self.class_factory:
            self.class_factory[cls] = {}

        self.class_factory[cls][path_text] = factory

    def get_class_factory(
        self,
        cls: type,
        path: List[str]
    ) -> List[Tuple[str, str, Any]]:
        """Get class factory for a class type and path.

        Args:
            cls: Class type
            path: Classpath

        Returns:
            Factory list for the class/path combination
        """
        path_text = ",".join(path)
        return self.class_factory[cls][path_text]

    def init_vault_class_factories(self) -> None:
        """Initialize Vault class factories."""
        self.add_class_factory(
            coshsh.vault.Vault,
            self.classes_path,
            coshsh.vault.Vault.init_class_factory(self.classes_path)
        )

    def init_ds_dr_class_factories(self) -> None:
        """Initialize Datasource and Datarecipient class factories."""
        self.add_class_factory(
            coshsh.datasource.Datasource,
            self.classes_path,
            coshsh.datasource.Datasource.init_class_factory(self.classes_path)
        )
        self.add_class_factory(
            coshsh.datarecipient.Datarecipient,
            self.classes_path,
            coshsh.datarecipient.Datarecipient.init_class_factory(self.classes_path)
        )

    def update_vault_class_factories(self) -> None:
        """Update Vault class factory with current recipe's factory."""
        coshsh.vault.Vault.update_class_factory(
            self.get_class_factory(coshsh.vault.Vault, self.classes_path)
        )

    def update_ds_dr_class_factories(self) -> None:
        """Update Datasource and Datarecipient class factories."""
        coshsh.datasource.Datasource.update_class_factory(
            self.get_class_factory(coshsh.datasource.Datasource, self.classes_path)
        )
        coshsh.datarecipient.Datarecipient.update_class_factory(
            self.get_class_factory(coshsh.datarecipient.Datarecipient, self.classes_path)
        )

    def init_item_class_factories(self) -> None:
        """Initialize Application, MonitoringDetail, Contact class factories."""
        self.add_class_factory(
            coshsh.application.Application,
            self.classes_path,
            coshsh.application.Application.init_class_factory(self.classes_path)
        )
        self.add_class_factory(
            coshsh.monitoringdetail.MonitoringDetail,
            self.classes_path,
            coshsh.monitoringdetail.MonitoringDetail.init_class_factory(self.classes_path)
        )
        self.add_class_factory(
            coshsh.contact.Contact,
            self.classes_path,
            coshsh.contact.Contact.init_class_factory(self.classes_path)
        )

    def update_item_class_factories(self) -> None:
        """Update Application, MonitoringDetail, Contact class factories."""
        coshsh.application.Application.update_class_factory(
            self.get_class_factory(coshsh.application.Application, self.classes_path)
        )
        coshsh.monitoringdetail.MonitoringDetail.update_class_factory(
            self.get_class_factory(coshsh.monitoringdetail.MonitoringDetail, self.classes_path)
        )
        coshsh.contact.Contact.update_class_factory(
            self.get_class_factory(coshsh.contact.Contact, self.classes_path)
        )

    def add_vault(self, **kwargs: Any) -> None:
        """Add a vault for secret management.

        Args:
            **kwargs: Vault configuration parameters

        Process:
            1. Expand environment variables
            2. Find vault plugin class
            3. Add recipe attributes
            4. Create vault instance
            5. Read secrets
        """
        # Expand environment variables
        for key in [k for k in kwargs.keys() if isinstance(kwargs[k], str)]:
            kwargs[key] = re.sub('%.*?%', coshsh.util.substenv, kwargs[key])

        newcls = coshsh.vault.Vault.get_class(kwargs)
        if newcls:
            # Add recipe attributes
            for key in [attr for attr in self.attributes_for_adapters if hasattr(self, attr)]:
                kwargs[f'recipe_{key}'] = getattr(self, key)
            for key, value in self.additional_recipe_fields.items():
                kwargs[f'recipe_{key}'] = value

            vault = newcls(**kwargs)
            self.vaults.append(vault)

            try:
                self.vault_secrets.update(vault.read())
            except Exception as e:
                logger.critical(f"problem with vault {vault.name}: {e}")
                raise e
        else:
            logger.warning("could not find a suitable vault")

    def substsecret(self, match: re.Match) -> str:
        """Substitute vault secret from match object.

        Args:
            match: Regex match for @VAULT[identifier]

        Returns:
            Secret value if found, original string otherwise
        """
        identifier = match.group(1)
        if identifier in self.vault_secrets:
            return self.vault_secrets[identifier]
        else:
            return match.group(0)

    def add_datasource(self, **kwargs: Any) -> None:
        """Add a datasource for reading monitoring data.

        Args:
            **kwargs: Datasource configuration parameters

        Process:
            1. Expand environment variables
            2. Substitute vault secrets (@VAULT[id])
            3. Expand configuration mappings
            4. Find datasource plugin class
            5. Add recipe attributes
            6. Create datasource instance
        """
        for key in [k for k in kwargs.keys() if isinstance(kwargs[k], str)]:
            # Expand environment variables
            kwargs[key] = re.sub('%.*?%', coshsh.util.substenv, kwargs[key])

            # Substitute vault secrets
            kwargs[key] = re.sub(r'@VAULT\[(.*?)\]', self.substsecret, kwargs[key])

            # Expand configuration mappings
            for mapping in kwargs.get("coshsh_config_mappings", {}):
                mapping_keyword_pat = f"(@MAPPING_{mapping.upper()}\\[(.*?)\\])"
                for match in re.findall(mapping_keyword_pat, kwargs[key]):
                    if match[1] in kwargs["coshsh_config_mappings"][mapping]:
                        oldstr = f"@MAPPING_{mapping.upper()}[{match[1]}]"
                        newstr = kwargs["coshsh_config_mappings"][mapping][match[1]]
                        kwargs[key] = kwargs[key].replace(oldstr, newstr)

        newcls = coshsh.datasource.Datasource.get_class(kwargs)
        if newcls:
            # Add recipe attributes
            for key in [attr for attr in self.attributes_for_adapters if hasattr(self, attr)]:
                kwargs[f'recipe_{key}'] = getattr(self, key)
            for key, value in self.additional_recipe_fields.items():
                kwargs[f'recipe_{key}'] = value

            datasource = newcls(**kwargs)
            self.datasources.append(datasource)
        else:
            logger.warning("could not find a suitable datasource")

    def get_datasource(self, name: str) -> Optional[Any]:
        """Get datasource by name.

        Args:
            name: Datasource name

        Returns:
            Datasource instance or None
        """
        try:
            return [ds for ds in self.datasources if ds.name == name][0]
        except (IndexError, AttributeError):
            return None

    def add_datarecipient(self, **kwargs: Any) -> None:
        """Add a datarecipient for writing monitoring configs.

        Args:
            **kwargs: Datarecipient configuration parameters

        Process:
            1. Expand environment variables
            2. Substitute vault secrets
            3. Expand configuration mappings
            4. Find datarecipient plugin class
            5. Add recipe attributes
            6. Create datarecipient instance
        """
        for key in [k for k in kwargs.keys() if isinstance(kwargs[k], str)]:
            # Expand environment variables
            kwargs[key] = re.sub('%.*?%', coshsh.util.substenv, kwargs[key])

            # Substitute vault secrets
            kwargs[key] = re.sub(r'@VAULT\[(.*?)\]', self.substsecret, kwargs[key])

            # Expand configuration mappings
            for mapping in kwargs.get("coshsh_config_mappings", {}):
                mapping_keyword_pat = f"(@MAPPING_{mapping.upper()}\\[(.*?)\\])"
                for match in re.findall(mapping_keyword_pat, kwargs[key]):
                    if match[1] in kwargs["coshsh_config_mappings"][mapping]:
                        oldstr = f"@MAPPING_{mapping.upper()}[{match[1]}]"
                        newstr = kwargs["coshsh_config_mappings"][mapping][match[1]]
                        kwargs[key] = kwargs[key].replace(oldstr, newstr)

        newcls = coshsh.datarecipient.Datarecipient.get_class(kwargs)
        if newcls:
            # Add recipe attributes
            for key in [attr for attr in self.attributes_for_adapters if hasattr(self, attr)]:
                kwargs[f'recipe_{key}'] = getattr(self, key)

            datarecipient = newcls(**kwargs)
            self.datarecipients.append(datarecipient)
        else:
            logger.warning("could not find a suitable datarecipient")

    def get_datarecipient(self, name: str) -> Optional[Any]:
        """Get datarecipient by name.

        Args:
            name: Datarecipient name

        Returns:
            Datarecipient instance or None
        """
        try:
            return [dr for dr in self.datarecipients if dr.name == name][0]
        except (IndexError, AttributeError):
            return None

    def pid_exists(self, pid: int) -> bool:
        """Check if a process ID exists.

        Args:
            pid: Process ID to check

        Returns:
            True if process exists, False otherwise
        """
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            # The pid doesn't exist
            return False
        except PermissionError:
            # The pid exists but is not mine
            return False
        else:
            return True

    def pid_protect(self) -> str:
        """Create PID file to prevent concurrent execution.

        Returns:
            Path to PID file

        Raises:
            RecipePidAlreadyRunning: If another instance is running
            RecipePidNotWritable: If PID file/dir not writable
            RecipePidGarbage: If PID file contains invalid data

        Process:
            1. Check if PID file exists
            2. If exists, validate and check if process running
            3. Remove stale PID files
            4. Create new PID file with current PID
        """
        if os.path.exists(self.pid_file):
            if not os.access(self.pid_file, os.W_OK):
                raise RecipePidNotWritable("PID file not writable")

            try:
                with io.open(self.pid_file) as f:
                    pid = int(f.read().strip())
            except ValueError:
                # Handle empty PID file (might be from full filesystem)
                if (os.stat(self.pid_file).st_size == 0 and
                    os.statvfs(self.pid_file).f_bavail > 0):
                    logger.info(f'removing empty pidfile {self.pid_file}')
                    os.remove(self.pid_file)
                raise RecipePidGarbage("PID file contains invalid data")
            except Exception as e:
                logger.info(f'some other trouble with the pid file {self.pid_file}')
                raise RecipePidGarbage(f"PID file error: {e}")

            if not self.pid_exists(pid):
                # Stale PID file
                os.remove(self.pid_file)
                logger.info(f'removing stale (pid {pid}) pidfile {self.pid_file}')
            else:
                logger.info(f'another instance seems to be running (pid {pid}), exiting')
                raise RecipePidAlreadyRunning(f"Process {pid} already running")
        else:
            if not os.access(self.pid_dir, os.W_OK):
                raise RecipePidNotWritable("PID directory not writable")

        # Write PID file
        pid = str(os.getpid())
        try:
            with io.open(self.pid_file, 'w') as f:
                f.write(pid)
        except Exception as e:
            raise RecipePidNotWritable(f"Cannot write PID file: {e}")

        return self.pid_file

    def pid_remove(self) -> None:
        """Remove PID file.

        Called after recipe execution completes to allow
        future executions.
        """
        try:
            os.remove(self.pid_file)
        except Exception:
            pass
