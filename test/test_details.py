import unittest
import os
import sys
import shutil
import string
from optparse import OptionParser
import ConfigParser
from logging import INFO, DEBUG


sys.dont_write_bytecode = True
sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath(os.path.join("..", "coshsh")))

from log import logger
from generator import Generator
from datasource import Datasource
from application import Application

class CoshshTest(unittest.TestCase):
    def print_header(self):
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def setUp(self):
        logger.handlers[1].setLevel(DEBUG)
        os.makedirs("./var/objects/test6")
        self.config = ConfigParser.ConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = Generator()

    def tearDown(self):
        shutil.rmtree("./var/objects/test6", True)
        print 

    def test_detail_keyvalues(self):
        self.print_header()
        self.generator.add_recipe(name='test6', **dict(self.config.items('recipe_TEST6')))
        self.config.set("datasource_CSVDETAILS", "name", "test6")
        cfg = self.config.items("datasource_CSVDETAILS")
        ds = Datasource(**dict(cfg))
        hosts, applications, contacts, contactgroups, appdetails, dependencies, bps = ds.read()
        applications[0].resolve_monitoring_details()
        # swap threshold via KEYVALUES detail
        self.assert_(applications[0].swap_warning == "15%")
        self.assert_(applications[0].swap_critical == "8%")
        # cron threshold via KEYVALUES detail
        self.assert_(applications[0].cron_warning == "30")
        self.assert_(applications[0].cron_critical == "100")
        # swap threshold via class os_linux
        self.assert_(applications[1].swap_warning == "5%")
        self.assert_(applications[1].swap_critical == "15%")
        # neither class detail nor csv detail
        self.assert_(not hasattr(applications[1], "cron_warning"))
   


if __name__ == '__main__':
    unittest.main()


