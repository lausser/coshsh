import unittest
import os
import sys
from optparse import OptionParser
import ConfigParser
import logging


sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath(os.path.join("..", "coshsh")))

from generator import Generator
from datasource import Datasource
from application import Application

class CoshshTest(unittest.TestCase):
    def setUp(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = Generator()

    def xtest_create_site_check_paths(self):
        self.generator.add_site(name='test4', **dict(self.config.items('site_TEST4')))
        self.assert_(os.path.abspath(self.generator.sites['test4'].dynamic_dir) == os.path.abspath('./var/objects/test1/dynamic'))
        self.assert_(os.path.abspath(self.generator.sites['test4'].classes_path[0]) == os.path.abspath('./sites/test4/classes'))
        self.assert_(os.path.abspath(self.generator.sites['test4'].templates_path[0]) == os.path.abspath('../sites/default/templates'))
        self.assert_(os.path.abspath(self.generator.sites['test4'].jinja2.loader.searchpath[0]) == os.path.abspath('../sites/default/templates'))
  
        print self.generator.sites['test4'].jinja2.loader.searchpath

        self.generator.add_site(name='test5', **dict(self.config.items('site_TEST5')))
        self.assert_(os.path.abspath(self.generator.sites['test5'].classes_path[0]) == os.path.abspath('./sites/test5/classes'))
        self.assert_(os.path.abspath(self.generator.sites['test5'].templates_path[0]) == os.path.abspath('./sites/test5/templates'))
        self.assert_(os.path.abspath(self.generator.sites['test5'].jinja2.loader.searchpath[0]) == os.path.abspath('./sites/test5/templates'))
  
        # did the jinja2 object get the self-written filters?
        self.assert_('re_match' in self.generator.sites['test5'].jinja2.env.tests)
        self.assert_('service' in self.generator.sites['test5'].jinja2.env.filters)

    def test_create_site_check_factories(self):
        self.generator.add_site(name='test4', **dict(self.config.items('site_TEST4')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        ds = Datasource(**dict(cfg))
        self.assert_(hasattr(ds, 'only_the_test_simplesample'))
        self.config.set("datasource_CSVSAMPLE", "name", "csvsample")
        cfg = self.config.items("datasource_CSVSAMPLE")
        ds = Datasource(**dict(cfg))
        self.assert_(ds.dir == "./etc/sites/test1/data")

    def test_create_site_check_factories_read(self):
        self.generator.add_site(name='test4', **dict(self.config.items('site_TEST4')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        ds = Datasource(**dict(cfg))
        print "module name", Datasource
        print "module name", Application
        self.assert_(hasattr(ds, 'only_the_test_simplesample'))
        hosts, applications, contacts, contactgroups, appdetails, dependencies, bps = ds.read()
        print "now i have read"
        print hosts
        self.assert_(hosts[0].my_host == True)
        self.assert_(applications[0].test4_linux == True)


    def test_create_site_check_factories_write(self):
        self.generator.add_site(name='test4', **dict(self.config.items('site_TEST4')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        self.generator.sites['test4'].add_datasource(**dict(cfg))

        # remove target dir / create empty
        self.generator.sites['test4'].count_before_objects()
        self.generator.sites['test4'].cleanup_target_dir()
        print "before", self.generator.sites['test4'].old_objects

        self.generator.sites['test4'].prepare_target_dir()
        # check target

        self.generator.sites['test4'].collect()
        print self.generator.sites['test4'].applications
        
        self.generator.sites['test4'].render()

    def xtest_rebless_class(self):
        self.generator.add_site(name='test1', **dict(self.config.items('site_TEST1')))

        af = ApplicationFactory()
        print af.class_cache
        self.generator.sites['test1'].init_class_cache()
        print "tete", Application.class_factory
        row = ['gms1', 'gearman-server', '', '', '', 'nagioscop001', '7x24']
        final_row = { }
        for (index, value) in enumerate(['name', 'type', 'component', 'version', 'patchlevel', 'host_name', 'check_period']):
            final_row[value] = [None if row[index] == "" else row[index]][0]
        a = Application(final_row)
        print a


if __name__ == '__main__':
    unittest.main()


