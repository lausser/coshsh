"""Unit tests for Datarecipient helper methods: too_much_delta(), count_objects()."""

import os
import shutil
import unittest
from coshsh.datarecipient import Datarecipient
from tests.common_coshsh_test import CommonCoshshTest


class DatarecipientUnitTest(CommonCoshshTest):

    def _make_dr(self):
        """Return a datarecipient from test1 recipe."""
        self.setUpConfig("etc/coshsh.cfg", "test1")
        r = self.generator.get_recipe("test1")
        return r.datarecipients[0]

    def test_too_much_delta_below_threshold(self):
        """too_much_delta returns False when change is below threshold."""
        dr = self._make_dr()
        dr.old_objects = (100, 200)
        dr.new_objects = (105, 210)
        dr.max_delta = (20, 20)
        self.assertFalse(dr.too_much_delta())

    def test_too_much_delta_above_threshold(self):
        """too_much_delta returns True when change exceeds threshold."""
        dr = self._make_dr()
        dr.old_objects = (100, 200)
        dr.new_objects = (150, 200)
        dr.max_delta = (20, 20)
        self.assertTrue(dr.too_much_delta())

    def test_too_much_delta_zero_threshold_disabled(self):
        """too_much_delta returns False when max_delta is empty (no limit)."""
        dr = self._make_dr()
        dr.old_objects = (100, 200)
        dr.new_objects = (200, 400)
        dr.max_delta = ()
        self.assertFalse(dr.too_much_delta())

    def test_too_much_delta_negative_threshold_accepts_growth(self):
        """Negative max_delta only guards against shrinkage, accepts growth."""
        dr = self._make_dr()
        dr.old_objects = (100, 200)
        dr.new_objects = (200, 400)
        dr.max_delta = (-20, -20)
        self.assertFalse(dr.too_much_delta())

    def test_too_much_delta_negative_threshold_blocks_shrinkage(self):
        """Negative max_delta blocks excessive shrinkage."""
        dr = self._make_dr()
        dr.old_objects = (100, 200)
        dr.new_objects = (50, 200)
        dr.max_delta = (-20, -20)
        self.assertTrue(dr.too_much_delta())

    def test_too_much_delta_from_zero_baseline(self):
        """Starting from zero hosts does not trigger delta."""
        dr = self._make_dr()
        dr.old_objects = (0, 0)
        dr.new_objects = (10, 20)
        dr.max_delta = (20, 20)
        self.assertFalse(dr.too_much_delta())

    def test_count_objects_empty_dir(self):
        """count_objects returns (0, 0) when the dynamic dir does not exist."""
        dr = self._make_dr()
        dr.dynamic_dir = '/tmp/nonexistent_coshsh_test_dir_xyz'
        self.assertEqual(dr.count_objects(), (0, 0))

    def test_count_objects_with_hosts(self):
        """count_objects counts host directories and app files on disk."""
        dr = self._make_dr()
        test_dir = '/tmp/coshsh_dr_count_test'
        shutil.rmtree(test_dir, True)
        hosts_dir = os.path.join(test_dir, 'hosts', 'h1')
        os.makedirs(hosts_dir)
        with open(os.path.join(hosts_dir, 'host.cfg'), 'w') as f:
            f.write('define host { }')
        with open(os.path.join(hosts_dir, 'app_test.cfg'), 'w') as f:
            f.write('define service { }')
        dr.dynamic_dir = test_dir
        hosts, apps = dr.count_objects()
        self.assertEqual(hosts, 1)
        self.assertEqual(apps, 1)
        shutil.rmtree(test_dir, True)
