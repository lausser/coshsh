"""Tests for class and template search order across multiple classes_dir paths."""

import os
import io
from tests.common_coshsh_test import CommonCoshshTest


class OrderTest(CommonCoshshTest):

    def test_check_class_order(self):
        """
        classes_dir = ./recipes/test13d/classes,./recipes/test13c/classes
        templates_dir = ./recipes/test13d/templates,./recipes/test13c/templates

        department		corporate		default
	os_linux.py		os_linux.py		os_linux.py
	os_beos.py
	os_aix.py		os_aix.py
			os_dos.py

        department		corporate		default
	os_linux_default.tpl	os_linux_default.tpl	os_linux_default.tpl
			os_beos_default.tpl
	os_aix_default.tpl	os_aix_default.tpl
	os_dos_default.tpl
	
        """
        self.setUpConfig("etc/coshsh.cfg", "test13")
        r = self.generator.get_recipe("test13")
        self.generator.run()
        self.assertTrue(hasattr(self.generator.recipes['test13'].objects['hosts']['linux_host'], 'config_files'))
        self.assertIn('host.cfg', self.generator.recipes['test13'].objects['hosts']['linux_host'].config_files['nagios'])
        self.assertTrue(os.path.exists("var/objects/test13/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test13/dynamic/hosts/linux_host"))
        self.assertTrue(os.path.exists("var/objects/test13/dynamic/hosts/linux_host/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test13/dynamic/hosts/aix_host/os_aix_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test13/dynamic/hosts/beos_host/os_beos_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test13/dynamic/hosts/dos_host/os_dos_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test13/dynamic/hosts/windows_host/os_windows_default.cfg"))

        # test classes
        self.assertEqual(self.generator.recipes['test13'].objects['applications']['linux_host+os+red hat'].marker, 'department')
        self.assertEqual(self.generator.recipes['test13'].objects['applications']['beos_host+os+beos'].marker, 'department')
        self.assertEqual(self.generator.recipes['test13'].objects['applications']['aix_host+os+aix'].marker, 'department')
        self.assertEqual(self.generator.recipes['test13'].objects['applications']['dos_host+os+dos'].marker, 'corporate')
        self.assertFalse(hasattr(self.generator.recipes['test13'].objects['applications']['windows_host+os+windows'], 'marker'))
        # test templates
        with io.open("var/objects/test13/dynamic/hosts/linux_host/os_linux_default.cfg") as f:
            os_linux_default_cfg = f.read()
        self.assertIn('department', os_linux_default_cfg)
        with io.open("var/objects/test13/dynamic/hosts/beos_host/os_beos_default.cfg") as f:
            os_beos_default_cfg = f.read()
        self.assertIn('corporate', os_beos_default_cfg)
        with io.open("var/objects/test13/dynamic/hosts/aix_host/os_aix_default.cfg") as f:
            os_aix_default_cfg = f.read()
        self.assertIn('department', os_aix_default_cfg)
        with io.open("var/objects/test13/dynamic/hosts/dos_host/os_dos_default.cfg") as f:
            os_dos_default_cfg = f.read()
        self.assertIn('department', os_dos_default_cfg)
        with io.open("var/objects/test13/dynamic/hosts/windows_host/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertIn('define', os_windows_default_cfg)
        with io.open("var/objects/test13/dynamic/hosts/windows_host/host.cfg") as f:
            host_cfg = f.read()
        self.assertIn('corporate host', host_cfg)
