#!/usr/bin/env python3

import unittest
import os
import io
import sys
import shutil
from optparse import OptionParser
from configparser import RawConfigParser
import logging
import subprocess


sys.dont_write_bytecode = True

import coshsh
from coshsh.generator import Generator
from coshsh.util import setup_logging

class CoshshTest(unittest.TestCase):
    def print_header(self):
        print("#" * 80 + "\n" + "#" + " " * 78 + "#")
        print("#" + str.center(self.id(), 78) + "#")
        print("#" + " " * 78 + "#\n" + "#" * 80 + "\n")

    def setUp(self):
        shutil.rmtree("./var/objects/test12", True)
        os.makedirs("./var/objects/test12")
        self.config = RawConfigParser()
        self.config.read('etc/coshsh_regex.cfg')
        self.generator = coshsh.generator.Generator()
        setup_logging()

    def tearDown(self):
        shutil.rmtree("./var/objects/test12", True)
        pass 


    def test_match1(self):
        os.makedirs("./var/objects/test12/at-hq")
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh_regex.cfg --recipe at_hq --debug", shell=True)
        self.assertTrue(os.path.exists("var/objects/test12/at-hq/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test12/at-hq/dynamic/hosts/test_host_1/os_windows_default.cfg"))

    def test_match2(self):
        os.makedirs("./var/objects/test12/at-wh005")
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh_regex.cfg --recipe at_wh005 --debug", shell=True)
        self.assertTrue(os.path.exists("var/objects/test12/at-wh005/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test12/at-wh005/dynamic/hosts/test_host_1/os_windows_default.cfg"))

    def test_pl(self):
        os.makedirs("./var/objects/test12/plplhqhq")
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh_regex.cfg --recipe pl_hq --debug", shell=True)
        self.assertTrue(os.path.exists("var/objects/test12/plplhqhq/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test12/plplhqhq/dynamic/hosts/test_host_1/os_windows_default.cfg"))

    def test_pt(self):
        os.makedirs("./var/objects/test12/ptpthqhq")
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh_regex.cfg --recipe pt_hq --debug", shell=True)
        self.assertTrue(os.path.exists("var/objects/test12/ptpthqhq/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test12/ptpthqhq/dynamic/hosts/test_host_1/os_windows_default.cfg"))


if __name__ == '__main__':
    unittest.main()


