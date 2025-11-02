#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Generator class - orchestrates recipe execution from cookbook configuration.

This module defines the Generator class which reads cookbook configuration
files and executes recipes to generate monitoring configurations.
"""

from __future__ import annotations

import os
import re
import logging
import time
import sys
import getpass
from tempfile import gettempdir
from typing import Dict, List, Any, Optional, Callable
from logging import INFO, DEBUG, getLogger

import coshsh
from coshsh.datainterface import CoshshDatainterface
from coshsh.vault import Vault

logger = logging.getLogger('coshsh')


class Generator:
    """Orchestrates recipe execution from cookbook configuration.

    The Generator class provides the high-level interface for coshsh:
    1. Reads cookbook configuration files
    2. Creates recipe instances
    3. Configures datasources, datarecipients, vaults
    4. Executes recipes (collect, assemble, render, output)
    5. Optionally reports metrics to Prometheus pushgateway

    Attributes:
        recipes: Dict of Recipe instances by name
        cookbook: Parsed cookbook configuration
        cookbook_files: Concatenated base names of cookbook files
        default_log_level: Default logging level (info/debug)
        log_dir: Directory for log files
        pg_job: Prometheus pushgateway job name (if configured)
        pg_address: Prometheus pushgateway address (if configured)
        pg_username: Prometheus pushgateway username (if configured)
        pg_password: Prometheus pushgateway password (if configured)

    Cookbook Configuration:
        Cookbook files use INI format with sections:
        - [defaults]: Global settings (log_dir, log_level, recipes)
        - [recipe_NAME]: Recipe configuration
        - [datasource_NAME]: Datasource configuration
        - [datarecipient_NAME]: Datarecipient configuration
        - [vault_NAME]: Vault configuration for secrets
        - [mapping_NAME]: Configuration value mappings
        - [prometheus_pushgateway]: Optional metrics reporting

    Recipe Selection:
        Recipes can be specified:
        1. Via command line (default_recipe parameter)
        2. Via cookbook [defaults] recipes setting
        3. All recipes not starting with _ (auto-discovery)

    Recipe Matching:
        Recipe names support regex matching. If "recipe_lebensmitteldiscounter_.*_.*"
        exists, it will match "lebensmitteldiscounter_at_hq".

    Error Handling:
        - Vault errors: Recipe is removed and skipped
        - Recipe errors: Logged but don't stop other recipes
        - Datasource/datarecipient errors: Logged as warnings

    Prometheus Integration:
        If configured, pushes metrics after each recipe:
        - coshsh_recipe_last_generated: Timestamp
        - coshsh_recipe_number_of_objects: Object counts by type
        - coshsh_recipe_last_duration: Recipe duration in seconds
        - coshsh_recipe_render_errors: Render error count
        - coshsh_recipe_last_success: Last successful run timestamp

    Example Usage:
        generator = Generator()
        generator.set_default_log_level("debug")
        generator.read_cookbook(
            ["cookbook.cfg"],
            default_recipe="production",
            force=False,
            safe_output=True
        )
        generator.run()
    """

    # Class-level attributes
    base_dir: str = os.path.dirname(os.path.dirname(__file__))
    messages: List[str] = []

    def __init__(self) -> None:
        """Initialize a Generator.

        Creates an empty ordered dictionary of recipes and sets
        default log level to info.
        """
        self.recipes: Dict[str, Any] = coshsh.util.odict()
        self.default_log_level: str = "info"

    def set_default_log_level(self, default_log_level: str) -> None:
        """Set the default logging level.

        Args:
            default_log_level: Log level ("info" or "debug")
        """
        self.default_log_level = default_log_level

    def add_recipe(self, *args: Any, **kwargs: Any) -> None:
        """Create and add a recipe to the generator.

        Args:
            **kwargs: Recipe configuration parameters passed to Recipe()

        Note:
            If recipe creation fails, logs error but continues.
            This allows other recipes to still run.
        """
        try:
            recipe = coshsh.recipe.Recipe(**kwargs)
            self.recipes[kwargs["name"]] = recipe
        except Exception as e:
            logger.error(f"exception creating a recipe: {e}")

    def get_recipe(self, name: str) -> Optional[Any]:
        """Get a recipe by name.

        Args:
            name: Recipe name

        Returns:
            Recipe instance or None if not found
        """
        return self.recipes.get(name, None)

    def add_pushgateway(self, *args: Any, **kwargs: Any) -> None:
        """Configure Prometheus pushgateway for metrics reporting.

        Args:
            **kwargs: Pushgateway configuration:
                - job: Job name (default: "coshsh")
                - address: Pushgateway address (default: "127.0.0.1:9091")
                - username: Optional HTTP basic auth username
                - password: Optional HTTP basic auth password

        Note:
            Metrics are only pushed if prometheus_client module is available.
        """
        self.pg_job: str = kwargs.get("job", "coshsh")
        self.pg_address: str = kwargs.get("address", "127.0.0.1:9091")
        self.pg_username: Optional[str] = kwargs.get("username", None)
        self.pg_password: Optional[str] = kwargs.get("password", None)

    def run(self) -> None:
        """Execute all configured recipes.

        For each recipe:
        1. Update class factories
        2. Create PID file
        3. Collect data from datasources
        4. Assemble object hierarchies
        5. Render templates
        6. Write output via datarecipients
        7. Push metrics to Prometheus (if configured)
        8. Remove PID file

        Error Handling:
            - RecipePidAlreadyRunning: Skip recipe (already running)
            - RecipePidNotWritable: Skip recipe (can't write PID file)
            - RecipePidGarbage: Skip recipe (corrupt PID file)
            - Other exceptions: Log and skip recipe

        Metrics:
            If Prometheus pushgateway is configured and prometheus_client
            module is available, pushes metrics after each recipe run.

        Debug Mode:
            If default_log_level is "debug", dumps class usage statistics.
        """
        # Try to import Prometheus client
        has_prometheus = False
        pg_auth_handler: Optional[Callable] = None
        coshshuser = None
        hostname = None

        try:
            from prometheus_client import (
                CollectorRegistry, Gauge, push_to_gateway, pushadd_to_gateway
            )
            from prometheus_client.exposition import basic_auth_handler, default_handler
            from urllib.parse import quote_plus
            from socket import gethostname

            has_prometheus = True

            # Get user and hostname for metrics
            try:
                coshshuser = getpass.getuser()
            except Exception:
                coshshuser = os.getenv("username")
            hostname = gethostname()

            # Set up authentication handler
            if hasattr(self, "pg_username") and self.pg_username:
                pg_auth_handler = lambda url, method, timeout, headers, data: basic_auth_handler(
                    url, method, timeout, headers, data,
                    self.pg_username, self.pg_password
                )
            else:
                pg_auth_handler = default_handler

        except Exception as e:
            if hasattr(self, "pg_job"):
                logger.critical(f"problem with prometheus modules: {e}", exc_info=1)
            has_prometheus = False

        # Disable Prometheus if not configured
        if has_prometheus and not hasattr(self, "pg_address"):
            has_prometheus = False

        # Execute each recipe
        for recipe in self.recipes.values():
            recipe_completed = False

            try:
                # Update class factories for this recipe
                recipe.update_item_class_factories()

                # Switch to recipe-specific logging
                coshsh.util.switch_logging(logfile=recipe.log_file)

                # Protect against concurrent execution
                if recipe.pid_protect():
                    registry = None
                    if has_prometheus:
                        registry = CollectorRegistry()

                    tic = time.time()

                    # Execute recipe pipeline
                    if recipe.collect():
                        recipe.assemble()
                        recipe.render()
                        recipe.output()
                        recipe_completed = True

                        # Record metrics
                        if has_prometheus and registry:
                            # Timestamp of generation
                            g = Gauge(
                                "coshsh_recipe_last_generated",
                                "The timestamp when a configuration was generated",
                                registry=registry
                            )
                            g.set_to_current_time()

                            # Object counts by type
                            g = Gauge(
                                "coshsh_recipe_number_of_objects",
                                "The number of objects of a certain type",
                                ['type'],
                                registry=registry
                            )
                            for objtype in recipe.objects.keys():
                                g.labels(type=objtype).set(len(recipe.objects[objtype]))

                            # Recipe duration
                            g = Gauge(
                                "coshsh_recipe_last_duration",
                                "The duration of a recipe",
                                registry=registry
                            )
                            g.set(time.time() - tic)

                            # Render errors
                            g = Gauge(
                                "coshsh_recipe_render_errors",
                                "The number of render errors",
                                registry=registry
                            )
                            g.set(recipe.render_errors)

                    # Record success timestamp
                    if has_prometheus and registry:
                        g = Gauge(
                            "coshsh_recipe_last_success",
                            "The timestamp when the recipe successfully ran last time",
                            registry=registry
                        )
                        g.set_to_current_time()

                        # Push metrics to gateway
                        try:
                            pushadd_to_gateway(
                                self.pg_address,
                                grouping_key={
                                    'hostname': hostname,
                                    'username': coshshuser,
                                    'cookbook': self.cookbook_files,
                                    'recipe': recipe.name
                                },
                                job=self.pg_job,
                                registry=registry,
                                handler=pg_auth_handler
                            )
                        except Exception as e:
                            logger.warning(
                                f"could not write to pushgateway {self.pg_address}: {e}"
                            )

                    recipe.pid_remove()

            except coshsh.recipe.RecipePidAlreadyRunning:
                logger.info(f"skipping recipe {recipe.name}. already running")
            except coshsh.recipe.RecipePidNotWritable:
                logger.error(
                    f"skipping recipe {recipe.name}. cannot write pid file to {recipe.pid_dir}"
                )
            except coshsh.recipe.RecipePidGarbage:
                logger.error(
                    f"skipping recipe {recipe.name}. pid file {recipe.pid_file} contains garbage"
                )
            except Exception as exp:
                logger.error(f"skipping recipe {recipe.name} ({exp})")
            else:
                if recipe_completed:
                    logger.info(
                        f"recipe {recipe.name} completed with {recipe.render_errors} problems"
                    )

            # Dump class usage in debug mode
            if self.default_log_level == "debug":
                CoshshDatainterface.dump_classes_usage()

            # Restore original logging
            coshsh.util.restore_logging()

    def read_cookbook(
        self,
        cookbook_files: List[str],
        default_recipe: Optional[str],
        force: bool,
        safe_output: bool
    ) -> None:
        """Read cookbook configuration files and create recipes.

        Args:
            cookbook_files: List of cookbook file paths to read
            default_recipe: Comma-separated list of recipe names to run
                           (None = use cookbook defaults or all)
            force: Force regeneration even if not needed
            safe_output: Use safe output mode

        Process:
            1. Parse cookbook files
            2. Extract vault, datasource, datarecipient, recipe configs
            3. Extract configuration mappings
            4. Determine which recipes to create
            5. Set up logging
            6. Create recipes with their dependencies

        Recipe Selection:
            - If default_recipe specified: Use those recipes
            - Else if [defaults] recipes exists: Use those
            - Else: Use all recipes not starting with _

        Recipe Matching:
            Supports regex matching. If "recipe_pattern_.*" exists,
            it matches "pattern_specific_instance".

        Configuration Inheritance:
            - Command-line force/safe_output override cookbook settings
            - Global defaults apply to all recipes
            - Recipe-specific settings override defaults

        Error Handling:
            - Missing cookbook files: Exit with error
            - Unknown vaults/datasources/datarecipients: Log error
            - Vault errors: Remove recipe and skip
            - Recipe creation errors: Log and continue

        Exits:
            Calls sys.exit(2) if cookbook files are bad or missing
        """
        # Create cookbook filename identifier for metrics
        self.cookbook_files = '___'.join(
            map(lambda cf: os.path.basename(os.path.abspath(cf)), cookbook_files)
        )

        # Configuration storage
        recipe_configs: Dict[str, List[tuple]] = {}
        datasource_configs: Dict[str, List[tuple]] = {}
        datarecipient_configs: Dict[str, List[tuple]] = {}
        coshsh_config_mappings: Dict[str, Dict[str, str]] = {}
        vault_configs: Dict[str, List[tuple]] = {}
        recipes: List[str] = []

        # Parse cookbook files
        cookbook = coshsh.configparser.CoshshConfigParser()
        self.cookbook = cookbook
        cookbook.read(cookbook_files)

        if cookbook._sections == {}:
            print(f"Bad or missing cookbook files : {', '.join(cookbook_files)}")
            sys.exit(2)

        # Extract vault configurations
        for vault in [s for s in cookbook.sections() if s.startswith('vault_')]:
            vault_name = vault.replace("vault_", "", 1).lower()
            vault_configs[vault_name] = cookbook.items(vault) + [('name', vault_name)]

        # Extract configuration mappings
        for mapping in [s for s in cookbook.sections() if s.startswith('mapping_')]:
            mapping_name = mapping.replace("mapping_", "")
            coshsh_config_mappings[mapping_name] = dict(cookbook.items(mapping))

        # Extract datarecipient configurations
        for dr in [s for s in cookbook.sections() if s.startswith('datarecipient_')]:
            dr_name = dr.replace("datarecipient_", "", 1).lower()
            datarecipient_configs[dr_name] = cookbook.items(dr) + [('name', dr_name)]

        # Extract datasource configurations
        for ds in [s for s in cookbook.sections() if s.startswith('datasource_')]:
            ds_name = ds.replace("datasource_", "", 1).lower()
            datasource_configs[ds_name] = cookbook.items(ds) + [('name', ds_name)]

        # Extract recipe configurations
        for recipe in [s for s in cookbook.sections() if s.startswith('recipe_')]:
            recipe_name = recipe.replace("recipe_", "", 1).lower()
            recipe_configs[recipe_name] = cookbook.items(recipe) + [('name', recipe_name)]

        # Determine which recipes to create
        if default_recipe:
            # Command-line specified recipes
            recipes = [r.lower() for r in default_recipe.split(",")]
        else:
            # Check cookbook defaults
            if "defaults" in cookbook.sections():
                defaults = dict(cookbook.items("defaults"))
                if "recipes" in defaults:
                    recipes = [r.lower() for r in defaults["recipes"].split(",")]
                else:
                    # Auto-discover all non-underscore recipes
                    recipes = list(filter(lambda r: not r.startswith("_"), recipe_configs.keys()))
            else:
                # Auto-discover all non-underscore recipes
                recipes = list(filter(lambda r: not r.startswith("_"), recipe_configs.keys()))

        # Set up logging directories
        if "defaults" in cookbook.sections():
            defaults = dict(cookbook.items("defaults"))

            # Log directory
            if "log_dir" in defaults:
                log_dir = re.sub('%.*?%', coshsh.util.substenv, defaults["log_dir"])
            elif 'OMD_ROOT' in os.environ:
                log_dir = os.path.join(os.environ['OMD_ROOT'], "var", "coshsh")
            else:
                log_dir = gettempdir()

            # PID directory
            if "pid_dir" in defaults:
                pid_dir = re.sub('%.*?%', coshsh.util.substenv, defaults["pid_dir"])
            else:
                pid_dir = gettempdir()

            # Backup count
            if "backup_count" in defaults:
                backup_count = int(defaults["backup_count"])
            else:
                backup_count = 2

            # Log level
            debug_mode = (
                (self.default_log_level and self.default_log_level.lower() == "debug") or
                ("log_level" in defaults and defaults["log_level"].lower() == "debug")
            )
        else:
            # No defaults section - use fallbacks
            if 'OMD_ROOT' in os.environ:
                log_dir = os.path.join(os.environ['OMD_ROOT'], "var", "coshsh")
            else:
                log_dir = gettempdir()
            pid_dir = gettempdir()
            backup_count = 2
            debug_mode = (
                self.default_log_level and self.default_log_level.lower() == "debug"
            )

        # Set up logging
        if debug_mode:
            coshsh.util.setup_logging(
                logdir=log_dir,
                scrnloglevel=DEBUG,
                backup_count=backup_count
            )
        else:
            coshsh.util.setup_logging(
                logdir=log_dir,
                scrnloglevel=INFO,
                backup_count=backup_count
            )

        self.log_dir = log_dir
        logger = getLogger('coshsh')

        # Create recipes
        for recipe in recipes:
            # Try regex matching if exact match not found
            matching_recipes = [
                r for r in sorted(recipe_configs.keys(), key=lambda x: len(x), reverse=True)
                if re.match(r, recipe)
            ]

            if recipe in recipe_configs.keys():
                # Exact match
                matching_recipes = [recipe]
            elif matching_recipes:
                # Regex match - use first (longest) match
                logger.info(
                    f"no direct hit, but matching recipes found: {', '.join(matching_recipes)}"
                )
                recipe_configs[recipe] = recipe_configs[matching_recipes[0]]
                # Update name to actual recipe name
                recipe_configs[recipe] = [
                    ('name', recipe) if kv[0] == 'name' else kv
                    for kv in recipe_configs[recipe]
                ]

            if not matching_recipes:
                logger.error(f"Recipe {recipe} is unknown")
                continue

            # Add command-line parameters
            recipe_configs[recipe].append(('force', force))

            # Add safe_output if not already set
            existing_safe_output = [v for k, v in recipe_configs[recipe] if k == "safe_output"]
            if not existing_safe_output or not existing_safe_output[0]:
                recipe_configs[recipe].append(('safe_output', safe_output))

            # Add default PID directory if not set
            if not [c for c in recipe_configs[recipe] if c[0] == 'pid_dir']:
                recipe_configs[recipe].append(('pid_dir', pid_dir))

            # Add configuration mappings
            recipe_configs[recipe].append(('coshsh_config_mappings', coshsh_config_mappings))

            # Create recipe
            self.add_recipe(**dict(recipe_configs[recipe]))

            if recipe not in self.recipes:
                # Recipe creation failed - error already logged
                continue

            # Add vaults
            vault_problems = False
            for vault in self.recipes[recipe].vault_names:
                if vault in vault_configs.keys():
                    try:
                        self.recipes[recipe].add_vault(**dict(vault_configs[vault]))
                    except Exception as e:
                        vault_problems = True
                        logger.error(f"Problem with vault {vault}: {e}")
                else:
                    logger.error(f"Vault {vault} is unknown")
                    vault_problems = True

            if vault_problems:
                # Vault errors are fatal - remove recipe
                # (we need secrets now for datasource passwords)
                del self.recipes[recipe]
                continue

            # Add datasources
            for ds in self.recipes[recipe].datasource_names:
                if ds in datasource_configs.keys():
                    datasource_configs[ds].append(
                        ('coshsh_config_mappings', coshsh_config_mappings)
                    )
                    self.recipes[recipe].add_datasource(**dict(datasource_configs[ds]))
                else:
                    logger.error(f"Datasource {ds} is unknown")

            # Add datarecipients
            for dr in self.recipes[recipe].datarecipient_names:
                if dr == "datarecipient_coshsh_default":
                    # Implicitly added by recipe.__init__
                    pass
                elif dr in datarecipient_configs.keys():
                    datarecipient_configs[dr].append(
                        ('coshsh_config_mappings', coshsh_config_mappings)
                    )
                    self.recipes[recipe].add_datarecipient(**dict(datarecipient_configs[dr]))
                else:
                    logger.error(f"Datarecipient {dr} is unknown")

        # Configure Prometheus pushgateway if specified
        if "prometheus_pushgateway" in cookbook.sections():
            pg_items = dict(cookbook.items("prometheus_pushgateway"))
            if "address" in pg_items:
                self.add_pushgateway(**pg_items)
