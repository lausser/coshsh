import unittest
import os
import sys
import shutil
import string
from optparse import OptionParser
import ConfigParser
import logging


sys.dont_write_bytecode = True

import coshsh
from coshsh.generator import Generator
from coshsh.util import setup_logging


class CoshshTest(unittest.TestCase):
    def print_header(self):
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def setUp(self):
        shutil.rmtree("./var/objects/test1", True)
        os.makedirs("./var/objects/test1")
        self.config = ConfigParser.ConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = coshsh.generator.Generator()
        setup_logging(scrnloglevel=logging.DEBUG)

    def tearDown(self):
        #shutil.rmtree("./var/objects/test1", True)
        print 

    def test_create_recipe_check_paths(self):
        self.print_header()
        self.generator.add_recipe(name='test4', **dict(self.config.items('recipe_TEST4')))
        return
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
        ds = coshsh.datasource.Datasource(**dict(cfg))
        self.assert_(hasattr(ds, 'only_the_test_simplesample'))
        self.config.set("datasource_CSVSAMPLE", "name", "csvsample")
        cfg = self.config.items("datasource_CSVSAMPLE")
        ds = coshsh.datasource.Datasource(**dict(cfg))
        self.assert_(ds.dir == "./recipes/test1/data")

    def test_create_recipe_check_factories_env(self):
        self.print_header()
        os.environ['COSHSHDIR'] = '/opt/coshsh'
        os.environ['ZISSSSSSCHDIR'] = '/opt/zisch'
        self.generator.add_recipe(name='test7', **dict(self.config.items('recipe_TEST7')))
        self.config.set("datasource_ENVDIRDS", "name", "envdirds")
        cfg = self.config.items("datasource_ENVDIRDS")
        ds = coshsh.datasource.Datasource(**dict(cfg))
        self.assert_(ds.dir == "/opt/coshsh/recipes/test7/data")
        self.assert_(self.generator.recipes['test7'].classes_path[0:2] == ['/opt/coshsh/recipes/test7/classes', '/opt/zisch/tmp'])

    def test_create_recipe_check_factories_read(self):
        self.print_header()
        self.generator.add_recipe(name='test4', **dict(self.config.items('recipe_TEST4')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        ds = coshsh.datasource.Datasource(**dict(cfg))
        self.assert_(hasattr(ds, 'only_the_test_simplesample'))
        objects = self.generator.recipes['test4'].objects
        ds.read(objects=objects)
        self.assert_(objects['hosts']['test_host_0'].my_host == True)
        self.assert_(objects['applications'].values()[0].test4_linux == True)
        self.assert_(objects['applications'].values()[1].test4_windows == True)


    def test_create_recipe_check_3factories_read(self):
        self.print_header()
        self.generator.add_recipe(name='test4a', **dict(self.config.items('recipe_TEST4A')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        ds = coshsh.datasource.Datasource(**dict(cfg))
        self.assert_(hasattr(ds, 'only_the_test_simplesample'))
        objects = self.generator.recipes['test4a'].objects
        ds.read(objects=objects)
        self.assert_(objects['hosts']['test_host_0'].my_host == True)
        self.assert_(objects['applications']['test_host_0+os+windows'].test4_windows == True)
        self.assert_(objects['applications']['test_host_0+os+red hat'].mycorp_linux == True)

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
        self.generator.recipes['test4'].assemble()

        # for each host, application get the corresponding template files
        # get the template files and cache them in a struct owned by the recipe
        # resolve the templates and attach the result as config_files to host/app
        self.generator.recipes['test4'].render()
        self.assert_(hasattr(self.generator.recipes['test4'].objects['hosts']['test_host_0'], 'config_files'))
        self.assert_('host.cfg' in self.generator.recipes['test4'].objects['hosts']['test_host_0'].config_files['nagios'])

        # write hosts/apps to the filesystem
        self.generator.recipes['test4'].output()
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"))
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg"))
        os_windows_default_cfg = open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg").read()
        self.assert_('os_windows_default_check_unittest' in os_windows_default_cfg)


    def test_create_recipe_check_factories_write2(self):
        self.print_header()
        self.generator.add_recipe(name='test4', **dict(self.config.items('recipe_TEST4B')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        self.generator.recipes['test4'].add_datasource(**dict(cfg))
        self.config.set("datarecipient_SIMPLESAMPLE2", "name", "simplesample")
        cfg = self.config.items("datarecipient_SIMPLESAMPLE2")
        self.generator.recipes['test4'].add_datarecipient(**dict(cfg))


        # remove target dir / create empty
        self.generator.recipes['test4'].count_before_objects()
        self.generator.recipes['test4'].cleanup_target_dir()

        self.generator.recipes['test4'].prepare_target_dir()
        # check target

        # read the datasources
        self.generator.recipes['test4'].collect()
        self.generator.recipes['test4'].assemble()
        
        # for each host, application get the corresponding template files
        # get the template files and cache them in a struct owned by the recipe
        # resolve the templates and attach the result as config_files to host/app
        self.generator.recipes['test4'].render()
        self.assert_(hasattr(self.generator.recipes['test4'].objects['hosts']['test_host_0'], 'config_files'))
        self.assert_('host.cfg' in self.generator.recipes['test4'].objects['hosts']['test_host_0'].config_files["nagios"])

        # write hosts/apps to the filesystem
        self.generator.recipes['test4'].output()
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"))
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg"))
        os_windows_default_cfg = open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg").read()
        self.assert_('os_windows_default_check_unittest' in os_windows_default_cfg)

    def test_ds_handshake(self):
        self.print_header()
        self.generator.add_recipe(name='test8', **dict(self.config.items('recipe_TEST8')))
        self.config.set("datasource_HANDSH", "name", "handshake")
        cfg = self.config.items("datasource_HANDSH")
        ds = coshsh.datasource.Datasource(**dict(cfg))
        try:
            hosts, applications, contacts, contactgroups, appdetails, dependencies, bps = ds.read()
        except Exception, exp:
            pass
        self.assert_(exp.__class__.__name__ == "DatasourceNotCurrent")
        cfg = self.config.items("datasource_HANDSH")
        self.generator.recipes['test8'].add_datasource(**dict(cfg))
        coll_success = self.generator.recipes['test8'].collect()
        self.assert_(coll_success == False)
        self.generator.recipes['test8'].assemble()

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


