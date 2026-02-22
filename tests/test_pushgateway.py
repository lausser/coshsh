"""Tests for Pushgateway datarecipient output (requires running pushgateway; may be slow)."""

import os
import time
import subprocess
import shutil
from tests.common_coshsh_test import CommonCoshshTest


class PushgatewayTest(CommonCoshshTest):

    def tearDown(self):
        shutil.rmtree("var/objects/test16")

    def test_pushgateway(self):
        """Verify that coshsh-cook with the PUSH recipe creates the expected dynamic output directory."""
        self.assertTrue(os.path.exists("../bin/coshsh-cook"))
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh.cfg --recipe PUSH", shell=True)
        self.assertTrue(os.path.exists("var/objects/test16/dynamic"))

    def test_pushgateway2(self):
        """Verify that PUSH2 recipe output appears after a delay (simulates slow pushgateway upload)."""
        time.sleep(19)
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh.cfg --recipe PUSH2", shell=True)
        self.assertTrue(os.path.exists("var/objects/test16/dynamic"))
