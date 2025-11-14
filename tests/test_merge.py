"""Test suite for hostname transformation and merging operations.

This module tests the datasource hostname transformation functionality,
including various operations like case conversion, domain stripping, and
DNS/IP resolution.
"""

from __future__ import annotations

import unittest

import coshsh
from tests.common_coshsh_test import CommonCoshshTest


class HostnameTransformationTest(CommonCoshshTest):
    """Test suite for hostname transformation operations in datasources.

    This suite verifies that:
    - Hostname transformation operations are correctly configured
    - Operations like to_lower, to_upper, strip_domain work correctly
    - DNS resolution and IP lookups function properly
    - Multiple transformation operations can be chained

    Test Configuration:
        Uses config file: etc/coshsh_merge.cfg
        Tests various datasource configurations with different transform_ops
    """

    def test_datasource_hostname_transformations_with_various_operations(self) -> None:
        """Test that datasources correctly apply hostname transformation operations.

        This test verifies that various hostname transformation operations work
        correctly, including:
        - Default (no transformations)
        - Case conversion (to_lower, to_upper)
        - Domain stripping (strip_domain)
        - DNS/IP resolution (resolve_ip, resolve_dns)
        - Chained operations

        Setup:
            Loads merge configuration and creates multiple datasources with
            different transformation operations configured.

        Assertions:
            - hostname_transform_ops attribute exists and contains correct operations
            - Transformations produce expected results for test hostnames
        """
        # Arrange: Set up config and recipe
        self.setUpConfig("etc/coshsh_merge.cfg", "merge")
        r_merge = self.generator.get_recipe("merge")

        # Act & Assert: Test default datasource (no transformations)
        self.generator.cookbook.set("datasource_merge", "name", "merge")
        cfg = self.generator.cookbook.items("datasource_merge")
        ds = coshsh.datasource.Datasource(**dict(cfg))

        # Assert: Default datasource has empty transform_ops
        self.assertTrue(
            hasattr(ds, 'hostname_transform_ops'),
            "Datasource should have hostname_transform_ops attribute"
        )
        self.assertFalse(
            ds.hostname_transform_ops,
            "Default datasource should have no hostname transformations"
        )

        # Act & Assert: Test lowercase transformation
        self.generator.cookbook.set("datasource_merge_lower", "name", "merge_lower")
        cfg = self.generator.cookbook.items("datasource_merge_lower")
        ds = coshsh.datasource.Datasource(**dict(cfg))

        # Assert: Lowercase transformation is configured
        self.assertTrue(
            hasattr(ds, 'hostname_transform_ops'),
            "Datasource should have hostname_transform_ops attribute"
        )
        self.assertTrue(
            ds.hostname_transform_ops,
            "Datasource should have transformation operations configured"
        )
        self.assertEqual(
            ds.hostname_transform_ops,
            ["to_lower"],
            "Datasource should have to_lower transformation configured"
        )
        self.assertEqual(
            ds.transform_hostname("TESTHOST0.hihi.de"),
            "testhost0.hihi.de",
            "to_lower should convert hostname to lowercase"
        )

        # Act & Assert: Test lowercase with domain stripping
        self.generator.cookbook.set("datasource_merge_lower_nodomain", "name", "merge_lower_nodomain")
        cfg = self.generator.cookbook.items("datasource_merge_lower_nodomain")
        ds = coshsh.datasource.Datasource(**dict(cfg))

        # Assert: Lowercase and strip_domain transformations are configured
        self.assertTrue(
            hasattr(ds, 'hostname_transform_ops'),
            "Datasource should have hostname_transform_ops attribute"
        )
        self.assertTrue(
            ds.hostname_transform_ops,
            "Datasource should have transformation operations configured"
        )
        self.assertEqual(
            ds.hostname_transform_ops,
            ["to_lower", "strip_domain"],
            "Datasource should have to_lower and strip_domain transformations"
        )
        self.assertEqual(
            ds.transform_hostname("TESTHOST0.hihi.de"),
            "testhost0",
            "Combined transformations should lowercase and strip domain"
        )

        # Act & Assert: Test IP resolution with uppercase
        self.generator.cookbook.set("datasource_merge_lookup_upper", "name", "merge_lookup_upper")
        cfg = self.generator.cookbook.items("datasource_merge_lookup_upper")
        ds = coshsh.datasource.Datasource(**dict(cfg))

        # Assert: IP resolution and uppercase transformations are configured
        self.assertTrue(
            hasattr(ds, 'hostname_transform_ops'),
            "Datasource should have hostname_transform_ops attribute"
        )
        self.assertTrue(
            ds.hostname_transform_ops,
            "Datasource should have transformation operations configured"
        )
        self.assertEqual(
            ds.hostname_transform_ops,
            ["resolve_ip", "to_upper"],
            "Datasource should have resolve_ip and to_upper transformations"
        )
        self.assertEqual(
            ds.transform_hostname("127.0.0.1"),
            "LOCALHOST",
            "IP resolution should resolve to localhost and uppercase it"
        )
        self.assertEqual(
            ds.transform_hostname("94.185.88.1"),
            "DMZ1.CONSOL.NET",
            "IP resolution should resolve to correct hostname and uppercase it"
        )

        # Act & Assert: Test DNS resolution with uppercase and domain stripping
        self.generator.cookbook.set("datasource_merge_lookup_nodomain", "name", "merge_lookup_nodomain")
        cfg = self.generator.cookbook.items("datasource_merge_lookup_nodomain")
        ds = coshsh.datasource.Datasource(**dict(cfg))

        # Assert: DNS resolution, uppercase, and strip_domain are configured
        self.assertTrue(
            hasattr(ds, 'hostname_transform_ops'),
            "Datasource should have hostname_transform_ops attribute"
        )
        self.assertTrue(
            ds.hostname_transform_ops,
            "Datasource should have transformation operations configured"
        )
        self.assertEqual(
            ds.hostname_transform_ops,
            ["resolve_dns", "to_upper", "strip_domain"],
            "Datasource should have resolve_dns, to_upper, and strip_domain transformations"
        )
        self.assertEqual(
            ds.transform_hostname("omd.consol.de"),
            "LABS",
            "DNS resolution should resolve, uppercase, and strip domain"
        )


if __name__ == '__main__':
    unittest.main()
