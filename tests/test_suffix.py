"""Test suite for file suffix handling in recipes.

This module tests that recipes generate configuration files with the correct
suffixes. Tests verify that different data recipient types create files with
their expected extensions (e.g., .conf for NRPE, .cfg for Nagios).
"""

from __future__ import annotations

import os

from tests.common_coshsh_test import CommonCoshshTest


class FileSuffixConfigurationTest(CommonCoshshTest):
    """Test suite for file suffix handling in recipe output.

    This suite verifies that:
    - Different data recipients use correct file suffixes
    - NRPE configurations use .conf suffix
    - Nagios configurations use .cfg suffix
    - Suffix configuration is respected in output files

    Test Configuration:
        Uses recipe: test11
        Config file: etc/coshsh.cfg
        Output directory: var/objects/test11/dynamic/

    File Suffix Conventions:
        - NRPE files: .conf (e.g., nrpe_os_windows_fs.conf)
        - Nagios files: .cfg (e.g., os_windows_fs.cfg)

    Related:
        See also: test_recipes.py for general recipe execution tests
    """

    def test_recipe_generates_files_with_correct_suffixes(self) -> None:
        """Test that recipe generates configuration files with correct suffixes.

        This test verifies that when a recipe is executed, the output files
        are created with the appropriate suffixes based on their type. NRPE
        configurations should use .conf and Nagios configurations should
        use .cfg.

        Test Setup:
            1. Load recipe test11
            2. Execute complete recipe pipeline
            3. Verify output files exist with correct suffixes

        Expected Behavior:
            - NRPE configuration file created with .conf suffix
            - Nagios configuration file created with .cfg suffix
            - Both files in same host directory

        Output Files:
            - nrpe_os_windows_fs.conf: NRPE-specific Windows filesystem config
            - os_windows_fs.cfg: Nagios Windows filesystem config

        Assertions:
            - NRPE .conf file exists
            - Nagios .cfg file exists
        """
        # Arrange: Load recipe
        self.setUpConfig("etc/coshsh.cfg", "test11")
        r = self.generator.get_recipe("test11")

        # Act: Execute complete recipe pipeline
        self.generator.run()

        # Assert: Verify NRPE configuration file with .conf suffix
        self.assertTrue(
            os.path.exists('var/objects/test11/dynamic/hosts/test_host_0/nrpe_os_windows_fs.conf'),
            "NRPE configuration file should be created with .conf suffix"
        )

        # Assert: Verify Nagios configuration file with .cfg suffix
        self.assertTrue(
            os.path.exists('var/objects/test11/dynamic/hosts/test_host_0/os_windows_fs.cfg'),
            "Nagios configuration file should be created with .cfg suffix"
        )
