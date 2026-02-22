"""Tests for CSV datasource regional filter (EU/AM/ALL) producing correct per-region host output."""

import os
import shutil
from tests.common_coshsh_test import CommonCoshshTest


class CsvFilterTest(CommonCoshshTest):
    _configfile = 'etc/coshsh.cfg'
    _objectsdir = "./var/objects/testcsv"

    def tearDown(self):
        shutil.rmtree("./var/objects/testcsvfilt", True)

    def test_read_eu_filtered(self):
        """Verify EU filter includes EU hosts and excludes AM hosts."""
        self.setUpConfig("etc/coshsh.cfg", "csvfilt_eu")
        r = self.generator.get_recipe("csvfilt_eu")
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        r.assemble()
        r.render()
        r.output()
        self.assertTrue(os.path.exists("var/objects/testcsvfilt/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertFalse(os.path.exists("var/objects/testcsvfilt/dynamic/hosts/test_host_1/os_windows_default.cfg"))

    def test_read_am_filtered(self):
        """Verify AM filter excludes EU hosts and includes AM hosts."""
        self.setUpConfig("etc/coshsh.cfg", "csvfilt_am")
        r = self.generator.get_recipe("csvfilt_am")
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        r.assemble()
        r.render()
        r.output()
        self.assertFalse(os.path.exists("var/objects/testcsvfilt/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/testcsvfilt/dynamic/hosts/test_host_1/os_windows_default.cfg"))

    def test_read_all_unfiltered(self):
        """Verify ALL (no filter) includes both EU and AM hosts."""
        self.setUpConfig("etc/coshsh.cfg", "csvfilt_all")
        r = self.generator.get_recipe("csvfilt_all")
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        r.assemble()
        r.render()
        r.output()
        self.assertTrue(os.path.exists("var/objects/testcsvfilt/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/testcsvfilt/dynamic/hosts/test_host_1/os_windows_default.cfg"))
