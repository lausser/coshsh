import unittest
from optparse import OptionParser
import ConfigParser
import sys
import os
import shutil

sys.path.append("..")
sys.path.append("../coshsh")
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'sites', 'default', 'classes'))
from generator import Generator
from datasource import Datasource

class CoshshTest(unittest.TestCase):
    def setUp(self):
        #shutil.rmtree('var/objects/test1')
        self.config = ConfigParser.ConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = Generator()


    def test_create_site(self):
        self.assert_(self.config._sections != {})
        print self.config._sections
        print [section for section in self.config.sections() if section.startswith('site_')]
        site = 'site_TEST1'
        self.generator.add_site(name=site.replace("site_", "", 1).lower(), **dict(self.config.items(site)))
        print self.generator.sites
        self.assert_(len(self.generator.sites) == 1)
        self.assert_('test1' in self.generator.sites)
        self.assert_(self.generator.sites['test1'].name == 'test1')
        print self.generator.sites['test1'].datasources
        self.generator.sites['test1'].init_class_cache()

    def test_create_datasource(self):
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        self.generator.add_site(name='test1', **dict(self.config.items('site_TEST1')))
        self.generator.sites['test1'].add_datasource(**dict(cfg))
        print self.generator.sites['test1'].datasources

    def test_custom_create_datasource(self):
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        print "add site test2"
        self.generator.add_site(name='test2', **dict(self.config.items('site_TEST2')))
        print "add site test2 ds simplesample"
        self.generator.sites['test2'].add_datasource(**dict(cfg))
        ds2 = self.generator.sites['test2'].datasources[0]
        print "add site test3"
        self.generator.add_site(name='test3', **dict(self.config.items('site_TEST3')))
        print "add site test3 ds simplesample"
        self.generator.sites['test3'].add_datasource(**dict(cfg))
        ds3 = self.generator.sites['test3'].datasources[0]
        self.assert_(not hasattr(ds2, "only_the_test_simplesample"))
        self.assert_(hasattr(ds3, "only_the_test_simplesample"))

    def test_create_config(self):
        self.generator.add_site(name='test3', **dict(self.config.items('site_TEST3')))
        self.generator.sites['test3'].add_datasource(**dict(self.config.items("datasource_SIMPLESAMPLE") + [('name', 'simplesample')]))
        self.generator.run()

if __name__ == '__main__':
    unittest.main()


