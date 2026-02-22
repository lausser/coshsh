"""Tests for recipe output path regex substitution patterns."""
import os
import shutil
import subprocess
from tests.common_coshsh_test import CommonCoshshTest


class RecexTest(CommonCoshshTest):

    def tearDown(self):
        shutil.rmtree("./var/objects/test12", True)

    def test_match1(self):
        """at_zentrale recipe substitutes path to atzentralezentrale output directory."""
        shutil.rmtree("./var/objects/test12", True)
        os.makedirs("./var/objects/test12/at-zentrale/dynamic")
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh_regex.cfg --recipe at_zentrale --debug", shell=True)
        self.assertTrue(os.path.exists("var/objects/test12/atzentralezentrale/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test12/atzentralezentrale/dynamic/hosts/test_host_1/os_windows_default.cfg"))

    def test_match2(self):
        """at_lh2000 recipe uses a literal path without regex substitution."""
        shutil.rmtree("./var/objects/test12", True)
        os.makedirs("./var/objects/test12/at-lh2000")
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh_regex.cfg --recipe at_lh2000 --debug", shell=True)
        self.assertTrue(os.path.exists("var/objects/test12/at-lh2000/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test12/at-lh2000/dynamic/hosts/test_host_1/os_windows_default.cfg"))

    def test_pl(self):
        """pl_zentrale recipe applies country-prefix doubling substitution."""
        shutil.rmtree("./var/objects/test12", True)
        os.makedirs("./var/objects/test12/plplzentralezentrale")
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh_regex.cfg --recipe pl_zentrale --debug", shell=True)
        self.assertTrue(os.path.exists("var/objects/test12/plplzentralezentrale/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test12/plplzentralezentrale/dynamic/hosts/test_host_1/os_windows_default.cfg"))

    def test_pt(self):
        """pt_zentrale recipe applies country-prefix doubling substitution."""
        shutil.rmtree("./var/objects/test12", True)
        os.makedirs("./var/objects/test12/ptptzentralezentrale")
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh_regex.cfg --recipe pt_zentrale --debug", shell=True)
        self.assertTrue(os.path.exists("var/objects/test12/ptptzentralezentrale/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test12/ptptzentralezentrale/dynamic/hosts/test_host_1/os_windows_default.cfg"))
