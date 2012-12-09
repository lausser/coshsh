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
        self.config = ConfigParser.ConfigParser()
        self.config.read('etc/coshsh.cfg')
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

    def test_create_recipe_multiple_sources(self):
        self.print_header()
        self.generator.add_recipe(name='test10', **dict(self.config.items('recipe_TEST10')))
        self.config.set("datasource_CSV10.1", "name", "csv1")
        self.config.set("datasource_CSV10.2", "name", "csv2")
        self.config.set("datasource_CSV10.3", "name", "csv3")
        cfg = self.config.items("datasource_CSV10.1")
        self.generator.recipes['test10'].add_datasource(**dict(cfg))
        cfg = self.config.items("datasource_CSV10.2")
        self.generator.recipes['test10'].add_datasource(**dict(cfg))
        cfg = self.config.items("datasource_CSV10.3")
        self.generator.recipes['test10'].add_datasource(**dict(cfg))
        exit
        # remove target dir / create empty
        self.generator.recipes['test10'].count_before_objects()
        self.generator.recipes['test10'].cleanup_target_dir()

        self.generator.recipes['test10'].prepare_target_dir()
        # check target

        # read the datasources
        self.generator.recipes['test10'].collect()

        # for each host, application get the corresponding template files
        # get the template files and cache them in a struct owned by the recipe
        # resolve the templates and attach the result as config_files to host/app
        self.generator.recipes['test10'].render()
        self.assert_(hasattr(self.generator.recipes['test10'].objects['hosts']['test_host_0'], 'config_files'))
        self.assert_('host.cfg' in self.generator.recipes['test10'].objects['hosts']['test_host_0'].config_files)

        # write hosts/apps to the filesystem
        self.generator.recipes['test10'].output()
        self.assert_(os.path.exists("var/objects/test10/dynamic/hosts"))
        self.assert_(os.path.exists("var/objects/test10/dynamic/hosts/test_host_0"))
        self.assert_(os.path.exists("var/objects/test10/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assert_(os.path.exists("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg"))
        os_windows_default_cfg = open("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg").read()
        self.assert_('os_windows_default_check_' in os_windows_default_cfg)
        self.assert_(len(self.generator.recipes['test10'].objects['applications']['test_host_1+os+windows2k8r2'].filesystems) == 3)

if __name__ == '__main__':
    unittest.main()


