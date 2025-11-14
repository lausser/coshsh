"""Test suite for Pushgateway integration functionality.

This module tests the Pushgateway integration, which enables pushing
monitoring configurations to a Pushgateway instance. Tests verify that
the coshsh-cook command correctly generates and outputs configurations
when configured with Pushgateway recipes.
"""

from __future__ import annotations

import os
import shutil
import subprocess

from tests.common_coshsh_test import CommonCoshshTest


class PushgatewayIntegrationTest(CommonCoshshTest):
    """Test suite for Pushgateway integration.

    This suite verifies that:
    - Pushgateway recipe can be cooked successfully
    - Dynamic configuration directories are created
    - Multiple Pushgateway configurations work correctly

    Test Configuration:
        Uses recipes: PUSH and PUSH2
        Config file: etc/coshsh.cfg
        Output directory: var/objects/test16/dynamic
    """

    def tearDown(self) -> None:
        """Clean up test artifacts.

        Removes:
            - Test output directory (var/objects/test16)
        """
        shutil.rmtree("var/objects/test16")

    def test_pushgateway_recipe_creates_dynamic_directory(self) -> None:
        """Test that Pushgateway recipe creates dynamic configuration directory.

        This test verifies that running coshsh-cook with the PUSH recipe
        successfully creates the expected dynamic configuration directory.
        This is the basic functionality required for Pushgateway integration.

        Test Setup:
            1. Verify coshsh-cook binary exists
            2. Execute coshsh-cook with PUSH recipe
            3. Check for dynamic directory creation

        Expected Behavior:
            - coshsh-cook binary should exist
            - Command should complete successfully
            - Dynamic directory should be created at var/objects/test16/dynamic
        """
        # Arrange: Verify coshsh-cook binary exists
        self.assertTrue(
            os.path.exists("../bin/coshsh-cook"),
            "coshsh-cook binary should exist at ../bin/coshsh-cook"
        )

        # Act: Execute coshsh-cook with PUSH recipe
        subprocess.call(
            "../bin/coshsh-cook --cookbook etc/coshsh.cfg --recipe PUSH",
            shell=True
        )

        # Assert: Verify dynamic directory was created
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic"),
            "Dynamic configuration directory should be created at var/objects/test16/dynamic"
        )

    def test_pushgateway_second_recipe_creates_dynamic_directory(self) -> None:
        """Test that second Pushgateway recipe creates dynamic directory.

        This test verifies that a second Pushgateway recipe (PUSH2) also
        works correctly. The test includes a delay to simulate real-world
        timing scenarios.

        Test Setup:
            1. Wait 19 seconds (simulates timing scenarios)
            2. Execute coshsh-cook with PUSH2 recipe
            3. Check for dynamic directory creation

        Expected Behavior:
            - Command should complete successfully after delay
            - Dynamic directory should be created at var/objects/test16/dynamic

        Note:
            The 19-second delay may be testing timing-related behavior
            or ensuring clean separation between recipe executions.
        """
        # Arrange: Wait for timing requirement
        import time
        time.sleep(19)

        # Act: Execute coshsh-cook with PUSH2 recipe
        subprocess.call(
            "../bin/coshsh-cook --cookbook etc/coshsh.cfg --recipe PUSH2",
            shell=True
        )

        # Assert: Verify dynamic directory was created
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic"),
            "Dynamic configuration directory should be created at var/objects/test16/dynamic"
        )
