import unittest
import os
import sys
import shutil
import string
from optparse import OptionParser
import ConfigParser
import logging


sys.dont_write_bytecode = True
sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath(os.path.join("..", "coshsh")))

from generator import Generator
from datasource import Datasource
from application import Application

class CoshshTest(unittest.TestCase):
    def print_header(self):
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def setUp(self):
        self.generator = Generator()

    def tearDown(self):
        pass

    def test_recipe_max_deltas_default(self):
        self.print_header()
        recipe = {'classes_dir': '/tmp', 'objects_dir': '/tmp', 'templates_dir': '/tmp', 'datasources': 'datasource' }
        datasource = {'name': 'datasource', 'type': 'simplesample'}
        self.generator.add_recipe(name='recp', **recipe)
        self.generator.recipes['recp'].add_datasource(**datasource)
        self.assert_(self.generator.recipes['recp'].max_delta == ())

    def test_recipe_max_deltas_simple(self):
        self.print_header()
        recipe = {'classes_dir': '/tmp', 'objects_dir': '/tmp', 'templates_dir': '/tmp', 'datasources': 'datasource', 'max_delta': '101' }
        datasource = {'name': 'datasource', 'type': 'simplesample'}
        self.generator.add_recipe(name='recp', **recipe)
        self.generator.recipes['recp'].add_datasource(**datasource)
        self.assert_(self.generator.recipes['recp'].max_delta == (101, 101))

    def test_recipe_max_deltas_double(self):
        self.print_header()
        recipe = {'classes_dir': '/tmp', 'objects_dir': '/tmp', 'templates_dir': '/tmp', 'datasources': 'datasource', 'max_delta': '101:202' }
        datasource = {'name': 'datasource', 'type': 'simplesample'}
        self.generator.add_recipe(name='recp', **recipe)
        self.generator.recipes['recp'].add_datasource(**datasource)
        self.assert_(self.generator.recipes['recp'].max_delta == (101, 202))


if __name__ == '__main__':
    unittest.main()


