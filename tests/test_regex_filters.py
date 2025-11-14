"""Test suite for datasource regex filter functionality.

This module tests the regex-based filtering system for datasources in recipes.
Tests verify that datasource filters can be defined globally, overridden per
datasource, and combined with wildcard patterns to control which data is
processed by each datasource.
"""

from __future__ import annotations

import os

from tests.common_coshsh_test import CommonCoshshTest


class DatasourceRegexFiltersTest(CommonCoshshTest):
    """Test suite for datasource regex filtering.

    This suite verifies that:
    - Datasource filters can be defined globally for all datasources
    - Individual datasources can override global filters
    - Filters can be combined and inherited
    - Wildcard filters (all*) work correctly
    - Unspecified datasources inherit appropriate defaults

    Test Configuration:
        Uses recipes: test1, test2, test3, test4, test5
        Config file: etc/coshsh7.cfg

    Filter Patterns:
        - Comma-separated values: "kaas,koos"
        - Single values: "numro"
        - Wildcards: "all*"
        - None: None (no filter)

    Related:
        See also: test_recex.py for recipe regex execution tests
    """

    def test_datasource_filters_configuration(self) -> None:
        """Test that datasource filters are configured correctly across recipes.

        This comprehensive test verifies multiple filter configuration scenarios
        across five different recipes to ensure all filter inheritance and
        override patterns work correctly.

        Test Setup:
            1. Load configuration with 5 recipes
            2. Each recipe has different filter configurations
            3. Verify filter values for each datasource in each recipe

        Recipe Configurations:
            test1: Basic filters (ds1: kaas,koos, ds2: kees,kiis)
            test2: Mixed filters (ds1: kaas,koos, dsa: alnuma, ds2: None)
            test3: Override filters (ds1: kaas,koos, ds2: numro, dsa: alnuma, ds3: numro, ds4: None)
            test4: Wildcard filters (ds1: kaas,koos, all others: all*)
            test5: Combined filters (specific + wildcard)

        Expected Behavior:
            - Explicitly defined filters are used
            - Global filters can be overridden
            - Wildcard patterns apply to all datasources
            - None means no filter applied

        Assertions:
            Tests filter values for all datasources across all recipes
        """
        # Arrange & Act: Load configuration with multiple recipes
        self.setUpConfig("etc/coshsh7.cfg", None)
        r1 = self.generator.get_recipe("test1")
        r2 = self.generator.get_recipe("test2")
        r3 = self.generator.get_recipe("test3")
        r4 = self.generator.get_recipe("test4")
        r5 = self.generator.get_recipe("test5")

        print(self.generator.recipes.keys())

        # Assert: Verify test1 datasource filters
        self.assertTrue(
            r1.datasource_filters.get("ds1") == "kaas,koos",
            "test1 recipe ds1 should have filter 'kaas,koos'"
        )
        self.assertTrue(
            r1.datasource_filters.get("ds2") == "kees,kiis",
            "test1 recipe ds2 should have filter 'kees,kiis'"
        )

        # Assert: Verify test2 datasource filters
        self.assertTrue(
            r2.datasource_filters.get("ds1") == "kaas,koos",
            "test2 recipe ds1 should have filter 'kaas,koos'"
        )
        self.assertTrue(
            r2.datasource_filters.get("ds2") == None,
            "test2 recipe ds2 should have no filter (None)"
        )
        self.assertTrue(
            r2.datasource_filters.get("dsa") == "alnuma",
            "test2 recipe dsa should have filter 'alnuma'"
        )

        # Assert: Verify test3 datasource filters
        self.assertTrue(
            r3.datasource_filters.get("ds1") == "kaas,koos",
            "test3 recipe ds1 should have filter 'kaas,koos'"
        )
        self.assertTrue(
            r3.datasource_filters.get("ds2") == "numro",
            "test3 recipe ds2 should have filter 'numro' (overridden)"
        )
        self.assertTrue(
            r3.datasource_filters.get("dsa") == "alnuma",
            "test3 recipe dsa should have filter 'alnuma'"
        )
        self.assertTrue(
            r3.datasource_filters.get("ds3") == "numro",
            "test3 recipe ds3 should have filter 'numro'"
        )
        self.assertTrue(
            r3.datasource_filters.get("ds4") == None,
            "test3 recipe ds4 should have no filter (None)"
        )

        # Assert: Verify test4 datasource filters with wildcards
        self.assertTrue(
            r4.datasource_filters.get("ds1") == "kaas,koos",
            "test4 recipe ds1 should have filter 'kaas,koos' (explicitly set)"
        )
        self.assertTrue(
            r4.datasource_filters.get("ds2") == "all*",
            "test4 recipe ds2 should have wildcard filter 'all*'"
        )
        self.assertTrue(
            r4.datasource_filters.get("dsa") == "all*",
            "test4 recipe dsa should have wildcard filter 'all*'"
        )
        self.assertTrue(
            r4.datasource_filters.get("ds3") == "all*",
            "test4 recipe ds3 should have wildcard filter 'all*'"
        )
        self.assertTrue(
            r4.datasource_filters.get("ds4") == "all*",
            "test4 recipe ds4 should have wildcard filter 'all*'"
        )
        self.assertTrue(
            r4.datasource_filters.get("ds5") == "all*",
            "test4 recipe ds5 should have wildcard filter 'all*'"
        )

        # Assert: Verify test5 datasource filters with mixed configuration
        self.assertTrue(
            r5.datasource_filters.get("ds1") == "kaas,koos",
            "test5 recipe ds1 should have filter 'kaas,koos' (explicitly set)"
        )
        self.assertTrue(
            r5.datasource_filters.get("ds2") == "numro",
            "test5 recipe ds2 should have filter 'numro' (explicitly set)"
        )
        self.assertTrue(
            r5.datasource_filters.get("dsa") == "alnuma",
            "test5 recipe dsa should have filter 'alnuma' (explicitly set)"
        )
        self.assertTrue(
            r5.datasource_filters.get("ds3") == "numro",
            "test5 recipe ds3 should have filter 'numro' (explicitly set)"
        )
        self.assertTrue(
            r5.datasource_filters.get("ds4") == "all*",
            "test5 recipe ds4 should have wildcard filter 'all*' (from wildcard pattern)"
        )
        self.assertTrue(
            r5.datasource_filters.get("ds5") == "all*",
            "test5 recipe ds5 should have wildcard filter 'all*' (from wildcard pattern)"
        )
