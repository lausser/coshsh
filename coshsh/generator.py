#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import os
import re
import logging
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
        except Exception, e:
            logger.error("exception creating a recipe: %s" % e)
        pass

    def run(self):
        for recipe in self.recipes.values():
            try:
	        switch_logging(logfile=recipe.log_file)
                if recipe.pid_protect():
                    if recipe.collect():
                        recipe.assemble()
                        recipe.render()
                        recipe.output()
                    recipe.pid_remove()
            except coshsh.recipe.RecipePidAlreadyRunning:
                logger.info("skipping recipe %s. already running" % (recipe.name))
            except coshsh.recipe.RecipePidNotWritable:
                logger.error("skipping recipe %s. cannot write pid file to %s" % (recipe.name, recipe.pid_dir))
            except coshsh.recipe.RecipePidGarbage:
                logger.error("skipping recipe %s. pid file %s contains garbage" % (recipe.name, recipe.pid_file))
            except Exception, exp:
                logger.error("skipping recipe %s (%s)" % (recipe.name, exp))
            else:
                pass
            restore_logging()
