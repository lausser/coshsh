import unittest
import os
import sys
import shutil
import string
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
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def setUp(self):
        self.config = coshsh.configparser.CoshshConfigParser()
        self.config.read('etc/coshsh2.cfg')
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(self.config._sections.values())
                
        self.generator = coshsh.generator.Generator()
        setup_logging()
        recipe_configs = {}
        for recipe in [section for section in self.config.sections() if section.startswith('recipe_')]:
            recipe_configs[recipe.replace("recipe_", "", 1).lower()] = self.config.items(recipe) + [('name', recipe.replace("recipe_", "", 1).lower())]
            print "-->", recipe
        recipes = filter( lambda r: not r.startswith("_"), recipe_configs.keys())
        print "recipes", recipes
        self.assert_("_cust2" not in recipes and "cust2" not in recipes)

    def tearDown(self):
        pass

    def test_templates(self):
        self.print_header()


    def test_inheritance(self):
        self.print_header()
        recipe = {'classes_dir': '/tmp', 'objects_dir': '/tmp', 'templates_dir': '/tmp', 'datasources': 'datasource' }
        self.generator.add_recipe(name='cust', **dict(self.config.items("recipe_cust")))
        self.generator.add_recipe(name='cust1', **dict(self.config.items("recipe_cust1")))
        #self.generator.add_recipe(name='cust2', **dict(self.config.items("recipe_cust2")))
        self.generator.add_recipe(name='cust3', **dict(self.config.items("recipe_cust3")))
        self.assert_(self.generator.recipes['cust'].datasource_names == ['csv10.1', 'csv10.2', 'csv10.3'])
        self.assert_(self.generator.recipes['cust'].datasource_filters['simplesample'] == 'fff')
        self.assert_(self.generator.recipes['cust1'].datasource_names == ['csv10.1', 'csv10.2', 'csv10.3'])
        self.assert_(self.generator.recipes['cust1'].datasource_filters['simplesample'] == 'fff1')
        #self.assert_(self.generator.recipes['cust2'].datasource_names == ['csv10.1', 'csv10.2', 'csv10.3'])
        #self.assert_(self.generator.recipes['cust2'].datasource_filters['simplesample'] == 'fff2')
        self.assert_(self.generator.recipes['cust3'].datasource_names == ['csv10.1', 'csv10.2', 'csv10.3'])
        self.assert_(self.generator.recipes['cust3'].datasource_filters['simplesample'] == 'fff3')
        self.assert_('./recipes/test12/classes' in self.generator.recipes['cust3'].classes_path)


if __name__ == '__main__':
    unittest.main()


