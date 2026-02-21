"""Tests for for_tool/want_tool routing producing tool-specific output (Nagios + Prometheus)."""

import os
import shutil
from tests.common_coshsh_test import CommonCoshshTest


class ForToolTest(CommonCoshshTest):

    def tearDown(self):
        super(ForToolTest, self).tearDown()
        if os.path.exists("var/objects/test20se/dynamic/targets"):
            shutil.rmtree("var/objects/test20se/dynamic/targets", True)
        if os.path.exists("var/objects/test21/dynamic/targets"):
            shutil.rmtree("var/objects/test21/dynamic/targets", True)

    def test_output(self):
        """Verify for_tool routing writes JSON targets separately from Nagios host config."""
        self.setUpConfig("etc/coshsh3.cfg", "test20")
        r = self.generator.get_recipe("test20")
        r.collect()
        r.assemble()
        r.render()
        os.makedirs("var/objects/test20se/dynamic/targets", 0o755)
        r.output()
        self.assertTrue(os.path.exists('var/objects/test20se/dynamic/targets/snmp_switch1.json'))
        self.assertFalse(os.path.exists('var/objects/test20/dynamic/snmp_switch1.json'))
        self.assertTrue(os.path.exists('var/objects/test20/dynamic/hosts/switch1/os_ios_default.cfg'))

    def test_output_mixed(self):
        """Verify mixed recipe produces both Nagios host config and Prometheus target JSON."""
        self.setUpConfig("etc/coshsh3.cfg", "test21")
        r = self.generator.get_recipe("test21")
        r.collect()
        r.assemble()
        r.render()
        os.makedirs("var/objects/test21/dynamic/targets", 0o755)
        r.output()
        self.assertTrue(os.path.exists('var/objects/test21/dynamic/hosts/switch1/os_ios_default.cfg'))
        self.assertTrue(os.path.exists('var/objects/test21/dynamic/targets/snmp_switch1.json'))
