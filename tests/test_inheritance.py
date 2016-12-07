import unittest
import os
import sys
import shutil
import string
from optparse import OptionParser
import ConfigParser
import logging
import pprint


sys.dont_write_bytecode = True

import coshsh
from coshsh.configparser import CoshshConfigParser
from coshsh.generator import Generator
from coshsh.datasource import Datasource
from coshsh.application import Application

class CoshshTest(unittest.TestCase):
    def print_header(self):
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def setUp(self):
        self.config = CoshshConfigParser()
        self.config.read('etc/coshsh2.cfg')
        print "CONF", self.config._sections
        pp = pprint.PrettyPrinter(indent=4)
        print "-------------------------"
        pp.pprint(self.config._sections.values())
                
        self.generator = coshsh.generator.Generator()
        self.generator.setup_logging()

    def tearDown(self):
        pass

    def test_inheritance(self):
        self.print_header()
        recipe = {'classes_dir': '/tmp', 'objects_dir': '/tmp', 'templates_dir': '/tmp', 'datasources': 'datasource' }
        self.generator.add_recipe(name='cust3', *self.config._sections["recipe_cust3"])
        print self.generator.recipes['cust3']
        self.assert_(self.generator.recipes['cust3'].datasources == "CSV10.1,CSV10.2,CSV10.3")


if __name__ == '__main__':
    unittest.main()


