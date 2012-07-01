import unittest
from optparse import OptionParser
import ConfigParser
import sys
import os

sys.path.append("..")
sys.path.append("../coshsh")
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'sites', 'default', 'classes'))
from generator import Generator
from datasource import Datasource

class CoshshTest(unittest.TestCase):
    def setUp(self):
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
        ds = Datasource(**dict(cfg))
        print ds

if __name__ == '__main__':
    unittest.main()


