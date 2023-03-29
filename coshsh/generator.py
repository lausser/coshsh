#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import os
import re
import logging
import time
import sys
import getpass
from tempfile import gettempdir
import coshsh
from logging import INFO, DEBUG, getLogger

logger = logging.getLogger('coshsh')


class Generator(object):

    base_dir = os.path.dirname(os.path.dirname(__file__))
    messages = []

    def __init__(self):
        self.recipes = coshsh.util.odict()

    def add_recipe(self, *args, **kwargs):
        try:
            recipe = coshsh.recipe.Recipe(**kwargs)
            self.recipes[kwargs["name"]] = recipe
        except Exception as e:
            logger.error("exception creating a recipe: %s" % e)

    def get_recipe(self, name):
        return self.recipes.get(name, None)

    def add_pushgateway(self, *args, **kwargs):
        self.pg_job = kwargs.get("job", "coshsh")
        self.pg_address = kwargs.get("address", "127.0.0.1:9091")
        self.pg_username = kwargs.get("username", None)
        self.pg_password = kwargs.get("password", None)

    def run(self):
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
            coshsh.util.restore_logging()

    def read_cookbook(self, cookbook_files, default_recipe, default_log_level, force, safe_output):
        self.cookbook_files = '___'.join(map(lambda cf: os.path.basename(os.path.abspath(cf)), cookbook_files))
        recipe_configs = {}
        datasource_configs = {}
        datarecipient_configs = {}
        coshsh_config_mappings = {}
        recipes = []
        cookbook = coshsh.configparser.CoshshConfigParser()
        self.cookbook = cookbook
        cookbook.read(cookbook_files)
        if cookbook._sections == {}:
            print("Bad or missing cookbook files : %s " % ', '.join(cookbook_files))
            sys.exit(2)
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
        if default_log_level and default_log_level.lower() == "debug" or "defaults" in cookbook.sections() and "log_level" in [c[0] for c in cookbook.items("defaults")] and cookbook.items("defaults")["log_level"].lower() == "debug":
            coshsh.util.setup_logging(logdir=log_dir, scrnloglevel=DEBUG, backup_count=backup_count)
        else:
            coshsh.util.setup_logging(logdir=log_dir, scrnloglevel=INFO, backup_count=backup_count)
        self.log_dir = log_dir
        logger = getLogger('coshsh')

        for recipe in recipes:
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
                for ds in self.recipes[recipe].datasource_names:
                    if ds in datasource_configs.keys():
                        self.recipes[recipe].add_datasource(**dict(datasource_configs[ds]))
                    else:
                        logger.error("Datasource %s is unknown" % ds)
                for dr in self.recipes[recipe].datarecipient_names:
                    if dr == "datarecipient_coshsh_default":
                        # implicitely added by recipe.__init__
                        pass
                    elif dr in datarecipient_configs.keys():
                        self.recipes[recipe].add_datarecipient(**dict(datarecipient_configs[dr]))
                    else:
                        logger.error("Datarecipient %s is unknown" % dr)
            else:
                logger.error("Recipe %s is unknown" % recipe)

        if "prometheus_pushgateway" in cookbook.sections() and "address" in [c[0] for c in cookbook.items("prometheus_pushgateway")]:
            self.add_pushgateway(**dict(cookbook.items("prometheus_pushgateway")))

