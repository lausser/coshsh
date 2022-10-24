#!/usr/bin/env python3

import os
import io
import shutil
import subprocess
import coshsh
from coshsh.generator import Generator
from coshsh.util import setup_logging
from tests.common_coshsh_test import CommonCoshshTest


class CoshshTest(CommonCoshshTest):

    def tearDown(self):
        shutil.rmtree("./var/objects/test1", True)
        shutil.rmtree("./var/objects/test1_mod", True)

    def test_coshsh_cook(self):
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh.cfg --recipe test4", shell=True)
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg"))
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue('os_windows_default_check_unittest' in os_windows_default_cfg)


    def test_create_template_tree(self):
        self.print_header()
        os.makedirs("./var/objects/test1/static")
        self.assertTrue(os.path.exists("var/objects/test1/static"))
        self.assertTrue(os.path.exists("../bin/coshsh-create-template-tree"))
        #subprocess.call(["../bin/coshsh-create-template-tree", "--cookbook", "etc/coshsh.cfg", "--recipe", "test4", "--template", "os_windows_fs"], shell=True)
        subprocess.call("../bin/coshsh-create-template-tree --cookbook etc/coshsh.cfg --recipe test4 --template os_windows_fs", shell=True)
        self.assertTrue(os.path.exists("var/objects/test1/static/service_templates"))
        self.assertTrue(os.path.exists("var/objects/test1/static/service_templates/os_windows_fs.cfg"))
        self.assertTrue(os.path.exists("var/objects/test1/static/service_templates/os_windows.cfg"))

    def test_multiple_cookbooks(self):
        self.print_header()
        os.makedirs("./var/objects/test1/static")
        os.makedirs("./var/objects/test1_mod/static")
        self.assertTrue(os.path.exists("var/objects/test1/static"))
        self.assertTrue(os.path.exists("var/objects/test1_mod/static"))
        self.assertTrue(os.path.exists("../bin/coshsh-create-template-tree"))
        #subprocess.call(["../bin/coshsh-create-template-tree", "--cookbook", "etc/coshsh.cfg", "--recipe", "test4", "--template", "os_windows_fs"], shell=True)
        subprocess.call("../bin/coshsh-create-template-tree --cookbook etc/coshsh.cfg --cookbook etc/coshsh6.cfg --recipe test4 --template os_windows_fs", shell=True)
        self.assertTrue(os.path.exists("var/objects/test1_mod/static/service_templates"))
        self.assertTrue(os.path.exists("var/objects/test1_mod/static/service_templates/os_windows_fs.cfg"))
        self.assertTrue(os.path.exists("var/objects/test1_mod/static/service_templates/os_windows.cfg"))


