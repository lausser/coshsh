import os
import subprocess
import shutil
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def tearDown(self):
        shutil.rmtree("var/objects/test16")

    def test_pushgateway(self):
        self.assertTrue(os.path.exists("../bin/coshsh-cook"))
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh.cfg --recipe PUSH", shell=True)
        self.assertTrue(os.path.exists("var/objects/test16/dynamic"))

    def test_pushgateway2(self):
        import time
        time.sleep(19)
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh.cfg --recipe PUSH2", shell=True)
        self.assertTrue(os.path.exists("var/objects/test16/dynamic"))

