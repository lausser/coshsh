import unittest
import os
import sys
import shutil
import string
from optparse import OptionParser
import ConfigParser
import logging
import subprocess


sys.dont_write_bytecode = True

import coshsh
from coshsh.generator import Generator
from coshsh.util import setup_logging

class CoshshTest(unittest.TestCase):
    def print_header(self):
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def setUp(self):
        shutil.rmtree("./var/objects/test1", True)
        os.makedirs("./var/objects/test1")
        shutil.rmtree("./var/objects/test4", True)
        os.makedirs("./var/objects/test4")
        self.config = ConfigParser.ConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = coshsh.generator.Generator()
        setup_logging()

    def tearDown(self):
        #shutil.rmtree("./var/objects/test1", True)
        pass 


    def test_coshsh_cook(self):
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh.cfg --recipe test4", shell=True)
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"))
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg"))
        os_windows_default_cfg = open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg").read()
        self.assert_('os_windows_default_check_unittest' in os_windows_default_cfg)


    def test_create_template_tree(self):
        self.print_header()
        os.makedirs("./var/objects/test1/static")
        self.assert_(os.path.exists("var/objects/test1/static"))
        self.assert_(os.path.exists("../bin/coshsh-create-template-tree"))
        #subprocess.call(["../bin/coshsh-create-template-tree", "--cookbook", "etc/coshsh.cfg", "--recipe", "test4", "--template", "os_windows_fs"], shell=True)
        subprocess.call("../bin/coshsh-create-template-tree --cookbook etc/coshsh.cfg --recipe test4 --template os_windows_fs", shell=True)
        self.assert_(os.path.exists("var/objects/test1/static/service_templates"))
        self.assert_(os.path.exists("var/objects/test1/static/service_templates/os_windows_fs.cfg"))
        self.assert_(os.path.exists("var/objects/test1/static/service_templates/os_windows.cfg"))



if __name__ == '__main__':
    unittest.main()


