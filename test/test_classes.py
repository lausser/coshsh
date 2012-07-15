import unittest
import os
import sys
from optparse import OptionParser
import ConfigParser
import logging


sys.path.insert(0, "..")
#sys.path.append("../coshsh")

from coshsh import Generator
from coshsh import logger
from coshsh import Host
from coshsh import Datasource
from coshsh import Application

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
        print "after site built", Datasource.class_factory
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        print sys.path
        print "cfg is", dict(cfg)
        ds = Datasource(**dict(cfg))
        self.assert_(hasattr(ds, 'only_the_test_simplesample'))
        print "datasource is ok"
        print ds
        print ds.__dict__
        print ds.hosts
        print ds.only_the_test_simplesample
        print "now i read"
        hosts, applications, contacts, contactgroups, appdetails, dependencies, bps = ds.read()
        print "now i have read"
        print hosts




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


