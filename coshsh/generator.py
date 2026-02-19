#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""
Generator: top-level entry point that reads cookbook config files and drives recipe execution.

Sole responsibility:
    - Parse one or more INI-style "cookbook" files to discover recipe, datasource,
      datarecipient, vault, and mapping definitions.
    - Instantiate Recipe objects wired to their declared components.
    - Iterate over recipes and delegate the collect -> assemble -> render -> output
      pipeline to each Recipe.

Does NOT:
    - Implement any pipeline logic itself (that lives in coshsh.recipe.Recipe).
    - Know about specific datasource, datarecipient, or vault plugins.
    - Write monitoring config files to disk (datarecipients do that).

Key classes:
    Generator -- the single class in this module; typically instantiated once
                 by the ``coshsh-cook`` CLI entry point.

AI agent note:
    The normal call sequence from ``bin/coshsh-cook`` is:
        1. generator = Generator()
        2. generator.set_default_log_level(...)
        3. generator.read_cookbook(cookbook_files, ...)   # parses config, creates recipes
        4. generator.run()                              # executes every recipe's pipeline
    read_cookbook() is where cookbook INI sections are classified by prefix
    (``recipe_``, ``datasource_``, ``datarecipient_``, ``vault_``, ``mapping_``)
    and wired into Recipe objects.  run() then simply iterates and delegates.
"""

import os
import re
import logging
import time
import sys
import getpass
from tempfile import gettempdir
import coshsh
from coshsh.datainterface import CoshshDatainterface
from coshsh.vault import Vault
from logging import INFO, DEBUG, getLogger

logger = logging.getLogger('coshsh')


class Generator(object):
    """Top-level controller that reads cookbook configs and runs recipes.

    A Generator owns an ordered collection of Recipe objects.  It is the only
    class that touches the cookbook INI files; once recipes are built, it hands
    control to each Recipe for the actual data pipeline.
    """

    base_dir = os.path.dirname(os.path.dirname(__file__))
    messages = []

    def __init__(self):
        # WHY: recipes is an odict (ordered dict) rather than a plain dict so
        # that recipes execute in the order they appear in the cookbook file.
        # The cookbook author controls execution order by section ordering, and
        # some deployments depend on earlier recipes populating shared state
        # (e.g. class factories or filesystem artifacts) before later ones run.
        self.recipes = coshsh.util.odict()
        self.default_log_level = "info"

    def set_default_log_level(self, default_log_level):
        """Set the log level that will be used when logging is initialized during read_cookbook().

        This must be called *before* read_cookbook() because the cookbook reader
        configures the logging subsystem based on this value.
        """
        self.default_log_level = default_log_level

    def add_recipe(self, *args, **kwargs):
        """Create a Recipe from keyword arguments and register it by name.

        kwargs are the key-value pairs extracted from one ``[recipe_*]``
        section of the cookbook.  On any exception the recipe is silently
        skipped (an error is logged).
        """
        try:
            recipe = coshsh.recipe.Recipe(**kwargs)
            self.recipes[kwargs["name"]] = recipe
        except Exception as e:
            logger.error("exception creating a recipe: %s" % e)

    def get_recipe(self, name):
        """Return the Recipe registered under *name*, or None if it does not exist."""
        return self.recipes.get(name, None)

    def add_pushgateway(self, *args, **kwargs):
        """Store Prometheus Pushgateway connection details for run()-time metrics export."""
        self.pg_job = kwargs.get("job", "coshsh")
        self.pg_address = kwargs.get("address", "127.0.0.1:9091")
        self.pg_username = kwargs.get("username", None)
        self.pg_password = kwargs.get("password", None)

    def run(self):
        """Execute every registered recipe's data pipeline.

        For each recipe the sequence is:
            update_item_class_factories -> pid_protect -> collect -> assemble ->
            render -> output -> pid_remove

        If a Prometheus Pushgateway was configured (via ``[prometheus_pushgateway]``
        in the cookbook), timing and object-count metrics are pushed after each
        recipe completes.
        """
        # WHY: Generator delegates to Recipe rather than running the pipeline
        # itself.  Each Recipe encapsulates its own datasources, datarecipients,
        # vaults, Jinja2 environment, class factories, and PID-file lock.
        # Keeping all pipeline logic inside Recipe means Generator stays a thin
        # orchestrator that only knows *which* recipes to run and in what
        # order -- it never touches raw host/application data.  This separation
        # makes it possible to test and reuse Recipe independently (e.g. in
        # unit tests that call recipe.collect() directly) and keeps Generator
        # focused on config parsing and recipe lifecycle management.
        #
        # NOTE: The prometheus_client import is inside a try/except because
        # the library is an optional dependency.  If it is not installed,
        # has_prometheus is set to False and all metrics-related code is skipped.
        try:
            from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, pushadd_to_gateway
            from prometheus_client.exposition import basic_auth_handler, default_handler
            from urllib.parse import quote_plus
            from socket import gethostname
            has_prometheus = True
            try:
                coshshuser = getpass.getuser()
            except Exception:
                coshshuser = os.getenv("username")
            hostname = gethostname()
            if hasattr(self, "pg_username"):
                pg_auth_handler = lambda url, method, timeout, headers, data: basic_auth_handler(url, method, timeout, headers, data, self.pg_username, self.pg_password)
            else:
                pg_auth_handler = default_handler
        except Exception as e:
            if hasattr(self, "pg_job"):
                logger.critical("problem with prometheus modules: %s" % e, exc_info=1)
            has_prometheus = False
        if has_prometheus and not hasattr(self, "pg_address"):
            has_prometheus = False
        for recipe in self.recipes.values():
            recipe_completed = False
            try:
                recipe.update_item_class_factories()
                coshsh.util.switch_logging(logfile=recipe.log_file)
                if recipe.pid_protect():
                    if has_prometheus:
                        registry = CollectorRegistry()
                    tic = time.time()
                    if recipe.collect():
                        recipe.assemble()
                        recipe.render()
                        recipe.output()
                        recipe_completed = True
                        if has_prometheus:
                            g = Gauge("coshsh_recipe_last_generated",
                                "The timestamp when a configuration was generated",
                                registry=registry)
                            g.set_to_current_time()
                            g = Gauge("coshsh_recipe_number_of_objects",
                                "The number of objects of a certain type", ['type'],
                                registry=registry)
                            for objtype in recipe.objects.keys():
                                g.labels(type=objtype).set(len(recipe.objects[objtype]))
                            g = Gauge("coshsh_recipe_last_duration",
                                "The duration of a recipe",
                                registry=registry)
                            g.set(time.time() - tic)
                            g = Gauge("coshsh_recipe_render_errors",
                                "The number of render errors",
                                registry=registry)
                            g.set(recipe.render_errors)
                    if has_prometheus:
                        g = Gauge("coshsh_recipe_last_success",
                            "The timestamp when the recipe successfully ran last time",
                            registry=registry)
                        g.set_to_current_time()
                        try:
                            pushadd_to_gateway(self.pg_address, grouping_key={
                                'hostname': hostname,
                                'username': coshshuser,
                                'cookbook': self.cookbook_files,
                                'recipe': recipe.name
                            }, job=self.pg_job, registry=registry, handler=pg_auth_handler)
                        except Exception as e:
                            logger.warning("could not write to pushgateway "+self.pg_address+": "+str(e))
                    recipe.pid_remove()
            except coshsh.recipe.RecipePidAlreadyRunning:
                logger.info("skipping recipe %s. already running" % (recipe.name))
            except coshsh.recipe.RecipePidNotWritable as e:
                logger.error("skipping recipe %s. cannot write pid file to %s" % (recipe.name, recipe.pid_dir))
            except coshsh.recipe.RecipePidGarbage:
                logger.error("skipping recipe %s. pid file %s contains garbage" % (recipe.name, recipe.pid_file))
            except Exception as exp:
                logger.error("skipping recipe %s (%s)" % (recipe.name, exp))
            else:
                if recipe_completed:
                    logger.info("recipe {} completed with {} problems".format(recipe.name, recipe.render_errors))
            if self.default_log_level == "debug":
                CoshshDatainterface.dump_classes_usage()
            coshsh.util.restore_logging()

    def read_cookbook(self, cookbook_files, default_recipe, force, safe_output):
        """Parse cookbook INI files and build fully wired Recipe objects.

        Parameters:
            cookbook_files  -- list of filesystem paths to INI cookbook files.
            default_recipe -- comma-separated recipe names from --recipe flag,
                              or None to use the cookbook's [defaults] section.
            force          -- if True, datasources re-read even if cache is fresh.
            safe_output    -- if True, datarecipients guard against accidental
                             mass-deletion of monitoring configs.
        """
        # WHY: Cookbook parsing -- the cookbook is one or more INI files whose
        # section names carry semantic prefixes (``recipe_``, ``datasource_``,
        # ``datarecipient_``, ``vault_``, ``mapping_``).  This method classifies
        # sections by prefix and collects their key-value pairs into dicts so
        # they can later be passed as **kwargs to the appropriate add_*()
        # methods.  The prefix-based convention keeps the cookbook format flat
        # and human-editable while still encoding the type of each component.
        #
        # After collecting all section configs, the method resolves which
        # recipes to run (explicit --recipe flag, ``[defaults].recipes``, or
        # all non-underscore-prefixed recipes).  For each selected recipe it:
        #   1. Instantiates the Recipe (add_recipe)
        #   2. Attaches vaults        (add_vault -- must run first so secrets
        #      are available for datasource/datarecipient password resolution)
        #   3. Attaches datasources   (add_datasource)
        #   4. Attaches datarecipients (add_datarecipient)
        # This ordering is critical; see the ``# WHY: Vault resolution order``
        # comment in recipe.py for details.
        self.cookbook_files = '___'.join(map(lambda cf: os.path.basename(os.path.abspath(cf)), cookbook_files))
        recipe_configs = {}
        datasource_configs = {}
        datarecipient_configs = {}
        coshsh_config_mappings = {}
        vault_configs = {}
        recipes = []
        cookbook = coshsh.configparser.CoshshConfigParser()
        self.cookbook = cookbook
        cookbook.read(cookbook_files)
        if cookbook._sections == {}:
            print("Bad or missing cookbook files : %s " % ', '.join(cookbook_files))
            sys.exit(2)
        for vault in [section for section in cookbook.sections() if section.startswith('vault_')]:
            vault_configs[vault.replace("vault_", "", 1).lower()] = cookbook.items(vault) + [('name', vault.replace("vault_", "", 1).lower())]
        for mapping in [section for section in cookbook.sections() if section.startswith('mapping_')]:
            coshsh_config_mappings[mapping.replace("mapping_", "")] = dict(cookbook.items(mapping))
        for ds in [section for section in cookbook.sections() if section.startswith('datarecipient_')]:
            datarecipient_configs[ds.replace("datarecipient_", "", 1).lower()] = cookbook.items(ds) + [('name', ds.replace("datarecipient_", "", 1).lower())]
        for ds in [section for section in cookbook.sections() if section.startswith('datasource_')]:
            datasource_configs[ds.replace("datasource_", "", 1).lower()] = cookbook.items(ds) + [('name', ds.replace("datasource_", "", 1).lower())]
        for recipe in [section for section in cookbook.sections() if section.startswith('recipe_')]:
            recipe_configs[recipe.replace("recipe_", "", 1).lower()] = cookbook.items(recipe) + [('name', recipe.replace("recipe_", "", 1).lower())]

        if default_recipe:
            recipes = [r.lower() for r in default_recipe.split(",")]
        else:
            if "defaults" in cookbook.sections() and "recipes" in [c[0] for c in cookbook.items("defaults")]:
                recipes = [recipe.lower() for recipe in dict(cookbook.items("defaults"))["recipes"].split(",")]
            else:
                recipes = filter( lambda r: not r.startswith("_"), recipe_configs.keys())
        if "defaults" in cookbook.sections() and "log_dir" in [c[0] for c in cookbook.items("defaults")]:
            log_dir = dict(cookbook.items("defaults"))["log_dir"]
            log_dir = re.sub('%.*?%', coshsh.util.substenv, log_dir)
        elif 'OMD_ROOT' in os.environ:
            log_dir = os.path.join(os.environ['OMD_ROOT'], "var", "coshsh")
        else:
            log_dir = gettempdir()
        if "defaults" in cookbook.sections() and "pid_dir" in [c[0] for c in cookbook.items("defaults")]:
            pid_dir = dict(cookbook.items("defaults"))["pid_dir"]
            pid_dir = re.sub('%.*?%', coshsh.util.substenv, pid_dir)
        else:
            pid_dir = gettempdir()
        if "defaults" in cookbook.sections() and "backup_count" in [c[0] for c in cookbook.items("defaults")]:
            backup_count = int(dict(cookbook.items("defaults"))["backup_count"])
        else:
            backup_count = 2
        if self.default_log_level and self.default_log_level.lower() == "debug" or "defaults" in cookbook.sections() and "log_level" in [c[0] for c in cookbook.items("defaults")] and cookbook.items("defaults")["log_level"].lower() == "debug":
            coshsh.util.setup_logging(logdir=log_dir, scrnloglevel=DEBUG, backup_count=backup_count)
        else:
            coshsh.util.setup_logging(logdir=log_dir, scrnloglevel=INFO, backup_count=backup_count)
        self.log_dir = log_dir
        logger = getLogger('coshsh')

        for recipe in recipes:
            # WHY: Recipe names in the cookbook can be regex patterns (e.g.
            # ``[recipe_lebensmitteldiscounter_.*_.*]``).  We sort by
            # descending length so that more specific patterns are tried first,
            # giving an exact match priority over a broad wildcard.
            matching_recipes = [r for r in sorted(recipe_configs.keys(), key=lambda x: len(x), reverse=True) if re.match(r, recipe)]
            if recipe in recipe_configs.keys():
                matching_recipes = [recipe]
            elif matching_recipes:
                # [recipe_lebensmitteldiscounter_.*_.*] <- lebensmitteldiscounter_at_hq
                logger.info("no direct hit, but matching recipes found: {}".format(", ".join(matching_recipes)))
                recipe_configs[recipe] = recipe_configs[matching_recipes[0]]
                recipe_configs[recipe] = [('name', recipe) if kv[0] == 'name' else kv for kv in recipe_configs[recipe]]
            if matching_recipes:
                recipe_configs[recipe].append(('force', force))
                if not [v for k, v in recipe_configs[recipe] if k == "safe_output"] or not [v for k, v in recipe_configs[recipe] if k == "safe_output"][0]:
                    # commandline --safe-output has priority
                    recipe_configs[recipe].append(('safe_output', safe_output))
                if not [c for c in recipe_configs[recipe] if c[0] == 'pid_dir']:
                    recipe_configs[recipe].append(('pid_dir', pid_dir))
                recipe_configs[recipe].append(('coshsh_config_mappings', coshsh_config_mappings))
                self.add_recipe(**dict(recipe_configs[recipe]))
                if recipe not in self.recipes:
                    # something went wrong in add_recipe. we should already see
                    # an error message here.
                    continue
                #self.recipes[recipe].update_ds_dr_class_factories()
                vault_problems = False
                for vault in self.recipes[recipe].vault_names:
                    if vault in vault_configs.keys():
                        try:
                            self.recipes[recipe].add_vault(**dict(vault_configs[vault]))
                        except Exception as e:
                            vault_problems = True
                    else:
                        logger.error("Vault %s is unknown" % vault)
                if vault_problems:
                    # other than datasource and recipient, a vault is
                    # not just instantiated and provisioned with the
                    # attributes from the cookbook. in add_vault it is
                    # already opened and the data are read, because we
                    # need the secrets right now. in add_datasource and
                    # add_datarecipients we might need to resolve
                    # passwords which are a pointer to a vault's record.
                    # if anything goes wrong here, we immediately abort by
                    # removing the affected recipe. the generator then
                    # usually calls run() without running a recipe.
                    del self.recipes[recipe]
                    continue
                for ds in self.recipes[recipe].datasource_names:
                    if ds in datasource_configs.keys():
                        datasource_configs[ds].append(('coshsh_config_mappings', coshsh_config_mappings))
                        self.recipes[recipe].add_datasource(**dict(datasource_configs[ds]))
                    else:
                        logger.error("Datasource %s is unknown" % ds)
                for dr in self.recipes[recipe].datarecipient_names:
                    if dr == "datarecipient_coshsh_default":
                        # implicitely added by recipe.__init__
                        pass
                    elif dr in datarecipient_configs.keys():
                        datarecipient_configs[dr].append(('coshsh_config_mappings', coshsh_config_mappings))
                        self.recipes[recipe].add_datarecipient(**dict(datarecipient_configs[dr]))
                    else:
                        logger.error("Datarecipient %s is unknown" % dr)
            else:
                logger.error("Recipe %s is unknown" % recipe)

        if "prometheus_pushgateway" in cookbook.sections() and "address" in [c[0] for c in cookbook.items("prometheus_pushgateway")]:
            self.add_pushgateway(**dict(cookbook.items("prometheus_pushgateway")))

