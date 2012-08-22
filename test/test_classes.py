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
        os.makedirs("./var/objects/test1")
        self.config = ConfigParser.ConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = Generator()

    def tearDown(self):
        shutil.rmtree("./var/objects/test1", True)
        print 

    def test_create_recipe_check_paths(self):
        self.print_header()
        self.generator.add_recipe(name='test4', **dict(self.config.items('recipe_TEST4')))
        self.assert_(os.path.abspath(self.generator.recipes['test4'].dynamic_dir) == os.path.abspath('./var/objects/test1/dynamic'))
        self.assert_(os.path.abspath(self.generator.recipes['test4'].classes_path[0]) == os.path.abspath('./recipes/test4/classes'))
        self.assert_(os.path.abspath(self.generator.recipes['test4'].templates_path[0]) == os.path.abspath('recipes/test4/templates'))
        self.assert_(os.path.abspath(self.generator.recipes['test4'].jinja2.loader.searchpath[0]) == os.path.abspath('recipes/test4/templates'))
  
        self.generator.add_recipe(name='test5', **dict(self.config.items('recipe_TEST5')))
        self.assert_(os.path.abspath(self.generator.recipes['test5'].classes_path[0]) == os.path.abspath('./recipes/test5/classes'))
        self.assert_(os.path.abspath(self.generator.recipes['test5'].templates_path[0]) == os.path.abspath('./recipes/test5/templates'))
        self.assert_(os.path.abspath(self.generator.recipes['test5'].jinja2.loader.searchpath[0]) == os.path.abspath('./recipes/test5/templates'))
  
        # did the jinja2 object get the self-written filters?
        self.assert_('re_match' in self.generator.recipes['test5'].jinja2.env.tests)
        self.assert_('service' in self.generator.recipes['test5'].jinja2.env.filters)

    def test_create_recipe_check_factories(self):
        self.print_header()
        self.generator.add_recipe(name='test4', **dict(self.config.items('recipe_TEST4')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        ds = Datasource(**dict(cfg))
        self.assert_(hasattr(ds, 'only_the_test_simplesample'))
        self.config.set("datasource_CSVSAMPLE", "name", "csvsample")
        cfg = self.config.items("datasource_CSVSAMPLE")
        ds = Datasource(**dict(cfg))
        self.assert_(ds.dir == "./recipes/test1/data")

    def test_create_recipe_check_factories_read(self):
        self.print_header()
        self.generator.add_recipe(name='test4', **dict(self.config.items('recipe_TEST4')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        ds = Datasource(**dict(cfg))
        self.assert_(hasattr(ds, 'only_the_test_simplesample'))
        hosts, applications, contacts, contactgroups, appdetails, dependencies, bps = ds.read()
        self.assert_(hosts[0].my_host == True)
        self.assert_(applications[0].test4_linux == True)
        self.assert_(applications[1].test4_windows == True)


    def test_create_recipe_check_3factories_read(self):
        self.print_header()
        self.generator.add_recipe(name='test4a', **dict(self.config.items('recipe_TEST4A')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        ds = Datasource(**dict(cfg))
        self.assert_(hasattr(ds, 'only_the_test_simplesample'))
        hosts, applications, contacts, contactgroups, appdetails, dependencies, bps = ds.read()
        self.assert_(hosts[0].my_host == True)
        self.assert_(applications[0].mycorp_linux == True)
        self.assert_(applications[1].test4_windows == True)


    def test_create_recipe_check_factories_write(self):
        self.print_header()
        self.generator.add_recipe(name='test4', **dict(self.config.items('recipe_TEST4')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        self.generator.recipes['test4'].add_datasource(**dict(cfg))

        # remove target dir / create empty
        self.generator.recipes['test4'].count_before_objects()
        self.generator.recipes['test4'].cleanup_target_dir()

        self.generator.recipes['test4'].prepare_target_dir()
        # check target

        # read the datasources
        self.generator.recipes['test4'].collect()
        
        # for each host, application get the corresponging template files
        # get the template files and cache them in a struct owned by the recipe
        # resolve the templates and attach the result as config_files to host/app
        self.generator.recipes['test4'].render()
        self.assert_(hasattr(self.generator.recipes['test4'].hosts['test_host_0'], 'config_files'))
        self.assert_('host.cfg' in self.generator.recipes['test4'].hosts['test_host_0'].config_files)

        # write hosts/apps to the filesystem
        self.generator.recipes['test4'].output()
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"))
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg"))
        os_windows_default_cfg = open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg").read()
        self.assert_('os_windows_default_check_unittest' in os_windows_default_cfg)

    def xtest_rebless_class(self):
        self.print_header()
        self.generator.add_recipe(name='test1', **dict(self.config.items('recipe_TEST1')))

        af = ApplicationFactory()
        print af.class_cache
        self.generator.recipes['test1'].init_class_cache()
        print "tete", Application.class_factory
        row = ['gms1', 'gearman-server', '', '', '', 'nagioscop001', '7x24']
        final_row = { }
        for (index, value) in enumerate(['name', 'type', 'component', 'version', 'patchlevel', 'host_name', 'check_period']):
            final_row[value] = [None if row[index] == "" else row[index]][0]
        a = Application(final_row)
        print a


if __name__ == '__main__':
    unittest.main()


