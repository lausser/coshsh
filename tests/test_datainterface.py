import unittest
import os
import io
import sys
import shutil
from optparse import OptionParser
from configparser import RawConfigParser
import logging

import coshsh
from coshsh.generator import Generator
from coshsh.util import setup_logging
from tests.common_coshsh_test import CommonCoshshTest

sys.dont_write_bytecode = True

class CoshshTest(CommonCoshshTest):
    _configfile = 'etc/coshsh.cfg'
    _objectsdir = "./var/objects/test4"
    default_recipe = "test4"

    def print_header(self):
        print("#" * 80 + "\n" + "#" + " " * 78 + "#")
        print("#" + str.center(self.id(), 78) + "#")
        print("#" + " " * 78 + "#\n" + "#" * 80 + "\n")


    def test_create_recipe_check_factories(self):
        self.print_header()
        import pprint
        print("GENERATOR.RUN")
        self.generator.run()
        pprint.pprint(self.generator.__dict__)
        self.assertTrue(self.generator.recipes['test4'].datasources[0].only_the_test_simplesample == True)
        #self.assertTrue(ds.dir == "./recipes/test4/data")

