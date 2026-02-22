"""Tests for datasource_filter regex pattern matching in recipe configuration."""

import os
from tests.common_coshsh_test import CommonCoshshTest


class RegexFiltersTest(CommonCoshshTest):

    def test_filters(self):
        """Verify datasource_filter values are parsed correctly for multiple recipes."""
        self.setUpConfig("etc/coshsh7.cfg", None)
        r1 = self.generator.get_recipe("test1")
        r2 = self.generator.get_recipe("test2")
        r3 = self.generator.get_recipe("test3")
        r4 = self.generator.get_recipe("test4")
        r5 = self.generator.get_recipe("test5")
        self.assertEqual(r1.datasource_filters.get("ds1"), "kaas,koos")
        self.assertEqual(r1.datasource_filters.get("ds2"), "kees,kiis")

        self.assertEqual(r2.datasource_filters.get("ds1"), "kaas,koos")
        self.assertIsNone(r2.datasource_filters.get("ds2"))
        self.assertEqual(r2.datasource_filters.get("dsa"), "alnuma")

        self.assertEqual(r3.datasource_filters.get("ds1"), "kaas,koos")
        self.assertEqual(r3.datasource_filters.get("ds2"), "numro")
        self.assertEqual(r3.datasource_filters.get("dsa"), "alnuma")
        self.assertEqual(r3.datasource_filters.get("ds3"), "numro")
        self.assertIsNone(r3.datasource_filters.get("ds4"))

        self.assertEqual(r4.datasource_filters.get("ds1"), "kaas,koos")
        self.assertEqual(r4.datasource_filters.get("ds2"), "all*")
        self.assertEqual(r4.datasource_filters.get("dsa"), "all*")
        self.assertEqual(r4.datasource_filters.get("ds3"), "all*")
        self.assertEqual(r4.datasource_filters.get("ds4"), "all*")
        self.assertEqual(r4.datasource_filters.get("ds5"), "all*")

        self.assertEqual(r5.datasource_filters.get("ds1"), "kaas,koos")
        self.assertEqual(r5.datasource_filters.get("ds2"), "numro")
        self.assertEqual(r5.datasource_filters.get("dsa"), "alnuma")
        self.assertEqual(r5.datasource_filters.get("ds3"), "numro")
        self.assertEqual(r5.datasource_filters.get("ds4"), "all*")
        self.assertEqual(r5.datasource_filters.get("ds5"), "all*")
