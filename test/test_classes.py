import unittest
import sys
from optparse import OptionParser
import ConfigParser


sys.path.append("..")
sys.path.append("../coshsh")

from generator import Generator
from host import Host
from application import Application

class CoshshTest(unittest.TestCase):
    def setUp(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = Generator()

    def test_rebless_class(self):
        self.generator.add_site(name='test1', **dict(self.config.items('site_TEST1')))
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


