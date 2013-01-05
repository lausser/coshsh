#!/usr/bin/env python
# Copyright (C) : Gerhard Lausser, gerhard.lausser@consol.de

import os
import sys
from recipe import Recipe
#from log import logger
import logging
from logging.handlers import RotatingFileHandler
from util import odict


class Generator(object):

    base_dir = os.path.dirname(os.path.dirname(__file__))
    messages = []

    def __init__(self):
        self.recipes = odict()
        self._logging_on = False

    def add_recipe(self, *args, **kwargs):
        try:
            recipe = Recipe(**kwargs)
            self.recipes[kwargs["name"]] = recipe
        except Exception, e:
            logger.info("exception creating a recipe: %s" % e)
            print e
        pass

    def run(self):
        if not self._logging_on:
            self.setup_logging(logdir=".")
        for recipe in self.recipes.values():
            try:
                if recipe.collect():
                    recipe.render()
                    recipe.output()
            except Exception, exp:
                logger.info("skipping recipe %s (%s)" % (recipe.name, exp))
            else:
                pass

    def setup_logging(self, logdir=".", logfile="coshsh.log", scrnloglevel=logging.INFO, txtloglevel=logging.INFO):
        logdir = os.path.abspath(logdir)
        if not os.path.exists(logdir):
            os.mkdir(logdir)
    
        log = logging.getLogger('coshsh')
        if log.handlers:
            # this method can be called multiple times in the unittests
            log.handlers = []
        log.setLevel(logging.DEBUG)
        log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    
        txt_handler = RotatingFileHandler(os.path.join(logdir, logfile), backupCount=2, maxBytes=20*1024*1024)
        #txt_handler.doRollover()
        txt_handler.setFormatter(log_formatter)
        txt_handler.setLevel(txtloglevel)
        log.addHandler(txt_handler)
        log.info("Logger initialised.")

        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(log_formatter)
        console_handler.setLevel(scrnloglevel)
        log.addHandler(console_handler)

        self._logging_on = True
