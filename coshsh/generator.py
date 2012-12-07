#!/usr/bin/env python
# Copyright (C) : Gerhard Lausser, gerhard.lausser@consol.de

import os
import sys
from recipe import Recipe
from log import logger
from util import odict


class Generator(object):

    base_dir = os.path.dirname(os.path.dirname(__file__))
    messages = []

    def __init__(self):
        self.recipes = odict()

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
                if recipe.collect():
                    recipe.render()
                    recipe.output()
            except Exception, exp:
                logger.info("skipping recipe %s (%s)" % (recipe.name, exp))
            else:
                pass

