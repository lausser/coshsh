"""Test suite for output tool functionality.

This module tests the 'for_tool' feature which allows recipes to output
different file formats for different tools (e.g., Nagios cfg files vs JSON
for other monitoring systems).
"""

from __future__ import annotations

import os
import shutil

from tests.common_coshsh_test import CommonCoshshTest


class OutputToolTest(CommonCoshshTest):
    """Test suite for output tool filtering and routing functionality.

    This suite verifies that:
    - Output files can be routed to different directories based on tool
    - Mixed output configurations work correctly
    - Files are placed in the correct locations based on tool configuration
    - Both Nagios .cfg and JSON formats can coexist in different directories

    Test Configuration:
        Uses recipes in tests/recipes/test20*/
        Configuration file: etc/coshsh3.cfg
        Tests recipes: test20, test21
    """

    def tearDown(self) -> None:
        """Clean up test output directories.

        Removes:
            - var/objects/test20se/dynamic/targets directory
            - var/objects/test21/dynamic/targets directory
        """
        super(OutputToolTest, self).tearDown()
        if os.path.exists("var/objects/test20se/dynamic/targets"):
            shutil.rmtree("var/objects/test20se/dynamic/targets", True)
        if os.path.exists("var/objects/test21/dynamic/targets"):
            shutil.rmtree("var/objects/test21/dynamic/targets", True)

    def test_output_routes_files_to_correct_tool_directories(self) -> None:
        """Test that output files are routed to correct directories by tool.

        Verifies that when using the 'for_tool' feature, different output
        formats (JSON vs .cfg) are placed in different directory structures
        based on their target tool.

        Test Setup:
            - Recipe 'test20' configured with separate tool directories
            - Creates targets directory for JSON output
            - Processes switch1 host with both Nagios and JSON outputs

        Expected Behavior:
            - JSON files go to test20se/dynamic/targets/
            - Nagios .cfg files go to test20/dynamic/hosts/
            - Files are NOT placed in wrong directories

        Assertions:
            - JSON file exists in targets directory
            - JSON file does NOT exist in Nagios directory
            - Nagios .cfg file exists in hosts directory
        """
        # Arrange: Set up recipe with tool-specific output directories
        self.setUpConfig("etc/coshsh3.cfg", "test20")
        recipe = self.generator.get_recipe("test20")

        # Act: Run full recipe processing pipeline
        recipe.collect()
        recipe.assemble()
        recipe.render()
        os.makedirs("var/objects/test20se/dynamic/targets", 0o755)
        recipe.output()

        # Assert: Verify files are in correct tool-specific directories
        self.assertTrue(
            os.path.exists('var/objects/test20se/dynamic/targets/snmp_switch1.json'),
            "JSON output should exist in targets directory for external tool"
        )
        self.assertTrue(
            not os.path.exists('var/objects/test20/dynamic/snmp_switch1.json'),
            "JSON output should NOT exist in Nagios directory"
        )
        self.assertTrue(
            os.path.exists('var/objects/test20/dynamic/hosts/switch1/os_ios_default.cfg'),
            "Nagios .cfg output should exist in hosts directory"
        )

    def test_output_handles_mixed_tool_configurations(self) -> None:
        """Test that mixed tool configurations work correctly.

        Verifies that a single recipe can output both Nagios .cfg files
        and JSON files to the same base directory structure when configured
        to do so.

        Test Setup:
            - Recipe 'test21' configured for mixed output
            - Creates targets directory within recipe output
            - Processes switch1 host

        Expected Behavior:
            - Both .cfg and .json files coexist in same directory tree
            - Each file type is in its appropriate subdirectory

        Assertions:
            - Nagios .cfg file exists in hosts subdirectory
            - JSON file exists in targets subdirectory
            - Both under same base directory (test21/dynamic)
        """
        # Arrange: Set up recipe with mixed output configuration
        self.setUpConfig("etc/coshsh3.cfg", "test21")
        recipe = self.generator.get_recipe("test21")

        # Act: Run full recipe processing pipeline
        recipe.collect()
        recipe.assemble()
        recipe.render()
        os.makedirs("var/objects/test21/dynamic/targets", 0o755)
        recipe.output()

        # Assert: Verify both output types exist in their subdirectories
        self.assertTrue(
            os.path.exists('var/objects/test21/dynamic/hosts/switch1/os_ios_default.cfg'),
            "Nagios .cfg output should exist in hosts subdirectory"
        )
        self.assertTrue(
            os.path.exists('var/objects/test21/dynamic/targets/snmp_switch1.json'),
            "JSON output should exist in targets subdirectory"
        )
