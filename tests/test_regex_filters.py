import unittest
import os
import sys
import shutil
from optparse import OptionParser
import logging
import pprint

import coshsh
from coshsh.configparser import CoshshConfigParser
from coshsh.generator import Generator
from coshsh.datasource import Datasource
from coshsh.application import Application
from coshsh.util import setup_logging
from tests.common_coshsh_test import CommonCoshshTest

sys.dont_write_bytecode = True

class CoshshTest(CommonCoshshTest):
    _configfile = 'etc/coshsh7.cfg'
    _objectsdir = "./var/objects/test1"

    def print_header(self):
        print("#" * 80 + "\n" + "#" + " " * 78 + "#")
        print("#" + str.center(self.id(), 78) + "#")
        print("#" + " " * 78 + "#\n" + "#" * 80 + "\n")

    def setUp(self):
        super(CoshshTest, self).setUp()

    def tearDowns(self):
        shutil.rmtree(self._objectsdir, True)
        pass

    def test_filters(self):
        self.print_header()
        print(self.generator.recipes.keys())
        self.assertTrue(self.generator.recipes["test1"].datasource_filters.get("ds1") == "kaas,koos")
        self.assertTrue(self.generator.recipes["test1"].datasource_filters.get("ds2") == "kees,kiis")

        self.assertTrue(self.generator.recipes["test2"].datasource_filters.get("ds1") == "kaas,koos")
        self.assertTrue(self.generator.recipes["test2"].datasource_filters.get("ds2") == None)
        self.assertTrue(self.generator.recipes["test2"].datasource_filters.get("dsa") == "alnuma")

        self.assertTrue(self.generator.recipes["test3"].datasource_filters.get("ds1") == "kaas,koos")
        self.assertTrue(self.generator.recipes["test3"].datasource_filters.get("ds2") == "numro")
        self.assertTrue(self.generator.recipes["test3"].datasource_filters.get("dsa") == "alnuma")
        self.assertTrue(self.generator.recipes["test3"].datasource_filters.get("ds3") == "numro")
        self.assertTrue(self.generator.recipes["test3"].datasource_filters.get("ds4") == None)

        self.assertTrue(self.generator.recipes["test4"].datasource_filters.get("ds1") == "kaas,koos")
        self.assertTrue(self.generator.recipes["test4"].datasource_filters.get("ds2") == "all*")
        self.assertTrue(self.generator.recipes["test4"].datasource_filters.get("dsa") == "all*")
        self.assertTrue(self.generator.recipes["test4"].datasource_filters.get("ds3") == "all*")
        self.assertTrue(self.generator.recipes["test4"].datasource_filters.get("ds4") == "all*")
        self.assertTrue(self.generator.recipes["test4"].datasource_filters.get("ds5") == "all*")

        self.assertTrue(self.generator.recipes["test5"].datasource_filters.get("ds1") == "kaas,koos")
        self.assertTrue(self.generator.recipes["test5"].datasource_filters.get("ds2") == "numro")
        self.assertTrue(self.generator.recipes["test5"].datasource_filters.get("dsa") == "alnuma")
        self.assertTrue(self.generator.recipes["test5"].datasource_filters.get("ds3") == "numro")
        self.assertTrue(self.generator.recipes["test5"].datasource_filters.get("ds4") == "all*")
        self.assertTrue(self.generator.recipes["test5"].datasource_filters.get("ds5") == "all*")

if __name__ == '__main__':
    unittest.main()


