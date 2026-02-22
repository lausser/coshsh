"""Tests for timeperiod object collection and output."""

import os
from tests.common_coshsh_test import CommonCoshshTest


class TimeperiodTest(CommonCoshshTest):
    _configfile = 'etc/timeperiods.cfg'
    _objectsdir = "./var/objects/tp"
    default_recipe = "test10"

    def test_create_recipe_multiple_sources(self):
        """Verify timeperiod host objects are collected, assembled, rendered, and written."""
        self.setUpConfig("etc/timeperiods.cfg", "test10")
        r = self.generator.get_recipe("test10")
        # remove target dir / create empty
        r.count_before_objects()
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        r.assemble()
        r.render()
        self.assertTrue(hasattr(r.objects['hosts']['monops_tp_cmd_dummy_host'], 'config_files'))
        self.assertIn('host.cfg', r.objects['hosts']['monops_tp_cmd_dummy_host'].config_files['nagios'])

        # write hosts/apps to the filesystem
        self.generator.recipes['test10'].output()
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/monops_tp_cmd_dummy_host"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts//monops_tp_cmd_dummy_host/timeperiods_monops.cfg"))
