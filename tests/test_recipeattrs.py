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
from coshsh.datasource import Datasource
from coshsh.datarecipient import Datarecipient
from coshsh.application import Application

class CoshshTest(unittest.TestCase):
    def print_header(self):
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def setUp(self):
        shutil.rmtree("./var/objects/test12", True)
        os.makedirs("./var/objects/test12")
        self.config = ConfigParser.ConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = coshsh.generator.Generator()
        self.generator.setup_logging()

    def tearDown(self):
        shutil.rmtree("./var/objects/test12", True)
        print 

    def test_create_recipe_collect(self):
        self.print_header()
        self.generator.add_recipe(name='test12', **dict(self.config.items('recipe_TEST12')))

        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        self.generator.recipes['test12'].add_datasource(**dict(cfg))

        self.config.set("datasource_CSVSAMPLE", "name", "csvsample")
        cfg = self.config.items("datasource_CSVSAMPLE")
        self.generator.recipes['test12'].add_datasource(**dict(cfg))

        self.config.set("datarecipient_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datarecipient_SIMPLESAMPLE")
        self.generator.recipes['test12'].add_datarecipient(**dict(cfg))

        self.config.set("datarecipient_SIMPLESAMPLE2", "name", "simplesample2")
        cfg = self.config.items("datarecipient_SIMPLESAMPLE2")
        self.generator.recipes['test12'].add_datarecipient(**dict(cfg))

        self.generator.run()
        #self.generator.recipes['test12'].render()
        #self.generator.recipes['test12'].output()
        #self.assert_(os.path.exists('var/objects/test12/dynamic/hosts/test_host_0/nrpe_os_windows_fs.conf'))
        #self.assert_(os.path.exists('var/objects/test12/dynamic/hosts/test_host_0/os_windows_fs.cfg'))


if __name__ == '__main__':
    unittest.main()

