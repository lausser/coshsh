import os
import sys
import re
import shutil
import coshsh
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):
    _configfile = 'etc/coshsh.cfg'
    _objectsdir = "./var/objects/testcsv"

    def tearDown(self):
        shutil.rmtree("./var/objects/testcsvfilt", True)

    def test_read_unfiltered_am(self):
        self.setUpConfig("etc/coshsh.cfg", "csvfilt_eu")
        r = self.generator.get_recipe("csvfilt_eu")
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        r.assemble()
        r.render()
        r.output()
        for root,d_names,f_names in os.walk("var/objects/testcsvfilt/dynamic/hosts"):
            print("WALKEU {}: d->{}, f->{}".format(root, d_names, f_names))
        self.assertTrue(os.path.exists("var/objects/testcsvfilt/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertFalse(os.path.exists("var/objects/testcsvfilt/dynamic/hosts/test_host_1/os_windows_default.cfg"))


    def test_read_unfiltered_am(self):
        self.setUpConfig("etc/coshsh.cfg", "csvfilt_am")
        r = self.generator.get_recipe("csvfilt_am")
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        r.assemble()
        r.render()
        r.output()
        for root,d_names,f_names in os.walk("var/objects/testcsvfilt/dynamic/hosts"):
            print("WALKAM {}: d->{}, f->{}".format(root, d_names, f_names))
        self.assertFalse(os.path.exists("var/objects/testcsvfilt/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/testcsvfilt/dynamic/hosts/test_host_1/os_windows_default.cfg"))


    def test_read_unfiltered_all(self):
        self.setUpConfig("etc/coshsh.cfg", "csvfilt_all")
        r = self.generator.get_recipe("csvfilt_all")
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        r.assemble()
        r.render()
        r.output()
        for root,d_names,f_names in os.walk("var/objects/testcsvfilt/dynamic/hosts"):
            print("WALKALL {}: d->{}, f->{}".format(root, d_names, f_names))
        self.assertTrue(os.path.exists("var/objects/testcsvfilt/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/testcsvfilt/dynamic/hosts/test_host_1/os_windows_default.cfg"))


