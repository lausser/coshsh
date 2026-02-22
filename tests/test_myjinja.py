"""Tests for custom Jinja2 filter and test extensions in rendered templates."""
import os
import io
from tests.common_coshsh_test import CommonCoshshTest


class MyJinjaTest(CommonCoshshTest):

    def test_jinja2_neighbor_and_type_filters_in_template(self):
        """Verify neighbor/type Jinja2 filters produce correct output in rendered config files."""
        self.setUpConfig("etc/coshsh.cfg", "testjinja")
        r = self.generator.get_recipe("testjinja")
        self.generator.run()
        self.assertTrue(os.path.exists('var/objects/test4/dynamic/hosts/test_host_0/os_linux_default.cfg'))
        self.assertTrue(os.path.exists('var/objects/test4/dynamic/hosts/test_host_0/os_windows_default.cfg'))
        with io.open("var/objects/test4/dynamic/hosts/test_host_0/os_windows_kaas.cfg") as f:
            os_windows_kaas_cfg = f.read()
            self.assertIn('os_linux.Linux', os_windows_kaas_cfg)
            self.assertIn('# type is red hat', os_windows_kaas_cfg)
            self.assertIn('# class is Linux', os_windows_kaas_cfg)
            self.assertIn('os_windows.Windows', os_windows_kaas_cfg)
            self.assertIn('# type is windows', os_windows_kaas_cfg)
            self.assertIn('# class is Windows', os_windows_kaas_cfg)
            self.assertIn("# ('red hat', 'os', 'linux')", os_windows_kaas_cfg)
            self.assertIn('ttype is red hat', os_windows_kaas_cfg)
            self.assertIn("# ('windows', 'os', 'windows')", os_windows_kaas_cfg)
            self.assertIn('ttype is windows', os_windows_kaas_cfg)
