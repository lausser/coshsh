import os
import shutil
import subprocess
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def tearDown(self):
        shutil.rmtree("./var/objects/test12", True)

    def test_match1(self):
        shutil.rmtree("./var/objects/test12", True)
        os.makedirs("./var/objects/test12/at-zentrale/dynamic")
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh_regex.cfg --recipe at_zentrale --debug", shell=True)
        self.assertTrue(os.path.exists("var/objects/test12/atzentralezentrale/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test12/atzentralezentrale/dynamic/hosts/test_host_1/os_windows_default.cfg"))

    def test_match2(self):
        shutil.rmtree("./var/objects/test12", True)
        os.makedirs("./var/objects/test12/at-lh2000")
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh_regex.cfg --recipe at_lh2000 --debug", shell=True)
        self.assertTrue(os.path.exists("var/objects/test12/at-lh2000/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test12/at-lh2000/dynamic/hosts/test_host_1/os_windows_default.cfg"))

    def test_pl(self):
        shutil.rmtree("./var/objects/test12", True)
        os.makedirs("./var/objects/test12/plplzentralezentrale")
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh_regex.cfg --recipe pl_zentrale --debug", shell=True)
        self.assertTrue(os.path.exists("var/objects/test12/plplzentralezentrale/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test12/plplzentralezentrale/dynamic/hosts/test_host_1/os_windows_default.cfg"))

    def test_pt(self):
        shutil.rmtree("./var/objects/test12", True)
        os.makedirs("./var/objects/test12/ptptzentralezentrale")
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh_regex.cfg --recipe pt_zentrale --debug", shell=True)
        self.assertTrue(os.path.exists("var/objects/test12/ptptzentralezentrale/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test12/ptptzentralezentrale/dynamic/hosts/test_host_1/os_windows_default.cfg"))



