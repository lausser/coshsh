import unittest
import os
import sys
import shutil
from optparse import OptionParser
import logging
import pprint


sys.dont_write_bytecode = True

import coshsh
from coshsh.configparser import CoshshConfigParser
from coshsh.generator import Generator
from coshsh.datasource import Datasource
from coshsh.application import Application
from coshsh.util import setup_logging

class CoshshTest(unittest.TestCase):
    def print_header(self):
        print("#" * 80 + "\n" + "#" + " " * 78 + "#")
        print("#" + str.center(self.id(), 78) + "#")
        print("#" + " " * 78 + "#\n" + "#" * 80 + "\n")

    def setUp(self):
        cookbook = coshsh.configparser.CoshshConfigParser()
        cookbook.read('etc/coshsh7.cfg')
        self.pp = pprint.PrettyPrinter(indent=4)
        #pp.pprint(self.config._sections.values())
                
        self.generator = coshsh.generator.Generator()
        setup_logging()

        recipe_configs = {}
        datasource_configs = {}
        for ds in [section for section in cookbook.sections() if section.startswith('datasource_')]:
            datasource_configs[ds.replace("datasource_", "", 1).lower()] = cookbook.items(ds) + [('name', ds.replace("datasource_", "", 1).lower())]
        for recipe in [section for section in cookbook.sections() if section.startswith('recipe_')]:
            recipe_configs[recipe.replace("recipe_", "", 1).lower()] = cookbook.items(recipe) + [('name', recipe.replace("recipe_", "", 1).lower())]
        recipes = filter( lambda r: not r.startswith("_"), recipe_configs.keys())
        for recipe in recipes:
            if recipe in recipe_configs.keys():
                self.generator.add_recipe(**dict(recipe_configs[recipe]))
                for ds in self.generator.recipes[recipe].datasource_names:
                    if ds in datasource_configs.keys():
                        self.generator.recipes[recipe].add_datasource(**dict(datasource_configs[ds]))

    def tearDown(self):
        pass

    def test_filters(self):
        self.print_header()
        self.assertTrue(self.generator.recipes["test1"].datasource_filters.get("ds1") == "kaas,koos")
        self.assertTrue(self.generator.recipes["test1"].datasource_filters.get("ds2") == "kees,kiis")

        self.assertTrue(self.generator.recipes["test2"].datasource_filters.get("ds1") == "kaas,koos")
        self.assertTrue(self.generator.recipes["test2"].datasource_filters.get("ds2") == None)
        self.assertTrue(self.generator.recipes["test2"].datasource_filters.get("dsa") == "alnuma")

        self.assertTrue(self.generator.recipes["test3"].datasource_filters.get("ds1") == "kaas,koos")
        self.assertTrue(self.generator.recipes["test3"].datasource_filters.get("ds2") == "numro")
        self.assertTrue(self.generator.recipes["test3"].datasource_filters.get("dsa") == "alnuma")
        self.assertTrue(self.generator.recipes["test3"].datasource_filters.get("ds3") == "numro")
        self.assertTrue(self.generator.recipes["test3"].datasource_filters.get("ds4") == None)

        self.assertTrue(self.generator.recipes["test4"].datasource_filters.get("ds1") == "kaas,koos")
        self.assertTrue(self.generator.recipes["test4"].datasource_filters.get("ds2") == "all*")
        self.assertTrue(self.generator.recipes["test4"].datasource_filters.get("dsa") == "all*")
        self.assertTrue(self.generator.recipes["test4"].datasource_filters.get("ds3") == "all*")
        self.assertTrue(self.generator.recipes["test4"].datasource_filters.get("ds4") == "all*")
        self.assertTrue(self.generator.recipes["test4"].datasource_filters.get("ds5") == "all*")

        self.assertTrue(self.generator.recipes["test5"].datasource_filters.get("ds1") == "kaas,koos")
        self.assertTrue(self.generator.recipes["test5"].datasource_filters.get("ds2") == "numro")
        self.assertTrue(self.generator.recipes["test5"].datasource_filters.get("dsa") == "alnuma")
        self.assertTrue(self.generator.recipes["test5"].datasource_filters.get("ds3") == "numro")
        self.assertTrue(self.generator.recipes["test5"].datasource_filters.get("ds4") == "all*")
        self.assertTrue(self.generator.recipes["test5"].datasource_filters.get("ds5") == "all*")

if __name__ == '__main__':
    unittest.main()


