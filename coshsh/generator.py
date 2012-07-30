#!/usr/bin/env python
# Copyright (C) : Gerhard Lausser, gerhard.lausser@consol.de

import os
import sys
from recipe import Recipe
from log import logger


class Generator(object):

    base_dir = os.path.dirname(os.path.dirname(__file__))
    messages = []

    def __init__(self):
        self.recipes = {}

    def add_recipe(self, *args, **kwargs):
        try:
            recipe = Recipe(**kwargs)
            self.recipes[kwargs["name"]] = recipe
        except Exception, e:
            logger.info("exception creating a recipe: %s" % e)
            print e
        pass

    def run(self):
        for recipe in self.recipes.values():
            try:
                recipe.count_before_objects()
                recipe.cleanup_target_dir()
            except Exception, e:
                print e
                logger.info("skipping recipe %s" % recipe.name)
            else:
                recipe.prepare_target_dir()
                if recipe.collect():
                    recipe.render()
                    recipe.output()

