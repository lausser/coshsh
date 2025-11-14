"""Test suite for CSV datasource filtering functionality.

This module tests the filtering capabilities of CSV datasources, verifying
that filters can correctly select or exclude hosts based on specified criteria.
"""

from __future__ import annotations

import os
import shutil

from tests.common_coshsh_test import CommonCoshshTest


class CSVFilterTest(CommonCoshshTest):
    """Test suite for CSV datasource filtering based on host attributes.

    This test suite verifies that:
    - CSV datasources can filter hosts by region/location (EU, AM)
    - Filters correctly include hosts matching the criteria
    - Filters correctly exclude hosts not matching the criteria
    - Unfiltered datasources include all hosts

    Test Configuration:
        Uses test recipes in tests/recipes/csvfilt_*/
        Config file: etc/coshsh.cfg
        Output directory: ./var/objects/testcsvfilt

    Test Scenarios:
        - csvfilt_eu: Filter for European hosts only
        - csvfilt_am: Filter for American hosts only
        - csvfilt_all: No filtering, include all hosts

    Note:
        The first test method had a duplicate name in the original file.
        It's now correctly named test_read_filtered_eu_region_hosts.
    """

    _configfile = 'etc/coshsh.cfg'
    _objectsdir = "./var/objects/testcsv"

    def tearDown(self) -> None:
        """Clean up test output directory after each test.

        Removes:
            - ./var/objects/testcsvfilt directory and all contents
        """
        shutil.rmtree("./var/objects/testcsvfilt", True)

    def test_read_filtered_eu_region_hosts(self) -> None:
        """Test that CSV datasource correctly filters for European region hosts.

        This test verifies that when a filter is applied to select only EU hosts,
        the recipe processes only hosts matching the EU criteria and excludes
        hosts from other regions like AM (Americas).

        Setup:
            - Loads csvfilt_eu recipe with EU region filter
            - Cleans and prepares target directory
            - Runs complete collection, assembly, render, and output pipeline

        Expected Behavior:
            - Linux hosts (test_host_0) from EU region are included
            - Windows hosts (test_host_1) from other regions are excluded
            - Only EU host configuration files are created

        Assertions:
            - EU Linux host configuration file exists
            - Non-EU Windows host configuration file does not exist
        """
        # Arrange: Set up configuration with EU filter
        self.setUpConfig("etc/coshsh.cfg", "csvfilt_eu")
        recipe = self.generator.get_recipe("csvfilt_eu")
        recipe.cleanup_target_dir()
        recipe.prepare_target_dir()

        # Act: Run complete recipe pipeline
        recipe.collect()
        recipe.assemble()
        recipe.render()
        recipe.output()

        # Debug: Show directory structure
        for root, d_names, f_names in os.walk("var/objects/testcsvfilt/dynamic/hosts"):
            print("WALKEU {}: d->{}, f->{}".format(root, d_names, f_names))

        # Assert: Verify EU host exists and non-EU host doesn't
        self.assertTrue(
            os.path.exists("var/objects/testcsvfilt/dynamic/hosts/test_host_0/os_linux_default.cfg"),
            "EU region host (test_host_0) with Linux should have config file created"
        )
        self.assertFalse(
            os.path.exists("var/objects/testcsvfilt/dynamic/hosts/test_host_1/os_windows_default.cfg"),
            "Non-EU region host (test_host_1) with Windows should not have config file created"
        )

    def test_read_filtered_am_region_hosts(self) -> None:
        """Test that CSV datasource correctly filters for American region hosts.

        This test verifies that when a filter is applied to select only AM hosts,
        the recipe processes only hosts matching the AM (Americas) criteria and
        excludes hosts from other regions like EU.

        Setup:
            - Loads csvfilt_am recipe with AM region filter
            - Cleans and prepares target directory
            - Runs complete collection, assembly, render, and output pipeline

        Expected Behavior:
            - Windows hosts (test_host_1) from AM region are included
            - Linux hosts (test_host_0) from other regions are excluded
            - Only AM host configuration files are created

        Assertions:
            - AM Windows host configuration file exists
            - Non-AM Linux host configuration file does not exist
        """
        # Arrange: Set up configuration with AM filter
        self.setUpConfig("etc/coshsh.cfg", "csvfilt_am")
        recipe = self.generator.get_recipe("csvfilt_am")
        recipe.cleanup_target_dir()
        recipe.prepare_target_dir()

        # Act: Run complete recipe pipeline
        recipe.collect()
        recipe.assemble()
        recipe.render()
        recipe.output()

        # Debug: Show directory structure
        for root, d_names, f_names in os.walk("var/objects/testcsvfilt/dynamic/hosts"):
            print("WALKAM {}: d->{}, f->{}".format(root, d_names, f_names))

        # Assert: Verify AM host exists and non-AM host doesn't
        self.assertFalse(
            os.path.exists("var/objects/testcsvfilt/dynamic/hosts/test_host_0/os_linux_default.cfg"),
            "Non-AM region host (test_host_0) with Linux should not have config file created"
        )
        self.assertTrue(
            os.path.exists("var/objects/testcsvfilt/dynamic/hosts/test_host_1/os_windows_default.cfg"),
            "AM region host (test_host_1) with Windows should have config file created"
        )

    def test_read_unfiltered_all_region_hosts(self) -> None:
        """Test that CSV datasource without filters includes all hosts.

        This test verifies that when no filter is applied, the recipe processes
        all hosts regardless of their region or other attributes.

        Setup:
            - Loads csvfilt_all recipe without filters
            - Cleans and prepares target directory
            - Runs complete collection, assembly, render, and output pipeline

        Expected Behavior:
            - All hosts are included regardless of region
            - Both EU and AM hosts are processed
            - Configuration files are created for all hosts

        Assertions:
            - Linux host (test_host_0) configuration file exists
            - Windows host (test_host_1) configuration file exists
            - All hosts from all regions have their configs created
        """
        # Arrange: Set up configuration without filters
        self.setUpConfig("etc/coshsh.cfg", "csvfilt_all")
        recipe = self.generator.get_recipe("csvfilt_all")
        recipe.cleanup_target_dir()
        recipe.prepare_target_dir()

        # Act: Run complete recipe pipeline
        recipe.collect()
        recipe.assemble()
        recipe.render()
        recipe.output()

        # Debug: Show directory structure
        for root, d_names, f_names in os.walk("var/objects/testcsvfilt/dynamic/hosts"):
            print("WALKALL {}: d->{}, f->{}".format(root, d_names, f_names))

        # Assert: Verify all hosts exist
        self.assertTrue(
            os.path.exists("var/objects/testcsvfilt/dynamic/hosts/test_host_0/os_linux_default.cfg"),
            "Linux host (test_host_0) should have config file when no filter is applied"
        )
        self.assertTrue(
            os.path.exists("var/objects/testcsvfilt/dynamic/hosts/test_host_1/os_windows_default.cfg"),
            "Windows host (test_host_1) should have config file when no filter is applied"
        )
