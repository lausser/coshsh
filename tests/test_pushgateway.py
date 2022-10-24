import unittest
import os
import sys
import shutil
from optparse import OptionParser
from configparser import RawConfigParser
import logging
import subprocess

import coshsh
from coshsh.generator import Generator
from coshsh.util import setup_logging
from tests.common_coshsh_test import CommonCoshshTest

sys.dont_write_bytecode = True

class CoshshTest(CommonCoshshTest):
    _configfile = 'etc/coshsh.cfg'
    _objectsdir = "./var/objects/test16"

    def print_header(self):
        print("#" * 80 + "\n" + "#" + " " * 78 + "#")
        print("#" + str.center(self.id(), 78) + "#")
        print("#" + " " * 78 + "#\n" + "#" * 80 + "\n")

    def setUp(self):
        shutil.rmtree("./var/objects/test16", True)
        os.makedirs("./var/objects/test16")
        self.config = RawConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = coshsh.generator.Generator()
        setup_logging()

    def tearDown(self):
        #shutil.rmtree("./var/objects/test16", True)
        pass 


    def test_pushgateway(self):
        self.print_header()
        self.assertTrue(os.path.exists("../bin/coshsh-cook"))
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh.cfg --recipe PUSH", shell=True)
        self.assertTrue(os.path.exists("var/objects/test16/dynamic"))

    def test_pushgateway2(self):
        self.print_header()
        import time
        time.sleep(19)
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh.cfg --recipe PUSH2", shell=True)
        self.assertTrue(os.path.exists("var/objects/test16/dynamic"))


if __name__ == '__main__':
    unittest.main()


