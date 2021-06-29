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
import getpass
import coshsh
from coshsh.recipe import Recipe, RecipePidAlreadyRunning, RecipePidNotWritable, RecipePidGarbage
from coshsh.util import odict, switch_logging, restore_logging

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
        pass

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
            cookbook = self.cookbook
            if hasattr(self, "pg_username"):
                pg_auth_handler = lambda url, method, timeout, headers, data: basic_auth_handler(url, method, timeout, headers, data, self.pg_username, self.pg_password)
            else:
                pg_auth_handler = default_handler
        except Exception as e:
            if hasattr(self, "pg_job"):
                logger.critical("problem with prometheus modules: %s" % e)
            has_prometheus = False
        if has_prometheus and not hasattr(self, "pg_address"):
            has_prometheus = False
        for recipe in self.recipes.values():
            recipe_completed = False
            try:
                switch_logging(logfile=recipe.log_file)
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
                    if has_prometheus:
                        g = Gauge("coshsh_recipe_last_success",
                            "The timestamp when the recipe successfully ran last time",
                            registry=registry)
                        g.set_to_current_time()
                        try:
                            pushadd_to_gateway(self.pg_address, grouping_key={
                                'hostname': hostname,
                                'username': coshshuser,
                                'cookbook': cookbook,
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
                    logger.info("recipe {} completed".format(recipe.name))
            restore_logging()
