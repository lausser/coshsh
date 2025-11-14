"""Test suite for recipe execution with regex-based filtering.

This module tests the execution of recipes with regex-based naming and
filtering. Tests verify that recipes with regex patterns in their names
can be executed correctly and generate the expected configuration files.
"""

from __future__ import annotations

import os
import shutil
import subprocess

from tests.common_coshsh_test import CommonCoshshTest


class RecipeRegexExecutionTest(CommonCoshshTest):
    """Test suite for recipe execution with regex patterns.

    This suite verifies that:
    - Recipes with regex patterns in names execute correctly
    - Different country/location prefixes work (at-, pl-, pt-)
    - Output directories are created with correct naming
    - Host configurations are generated in the right locations

    Test Configuration:
        Uses recipes: at_zentrale, at_lh2000, pl_zentrale, pt_zentrale
        Config file: etc/coshsh_regex.cfg
        Output directory: ./var/objects/test12/

    Test Data:
        Each recipe generates Windows host configurations with
        os_windows_default.cfg files.

    Related:
        See also: test_regex_filters.py for datasource filtering tests
    """

    def tearDown(self) -> None:
        """Clean up test artifacts.

        Removes:
            - Test output directory (./var/objects/test12)
        """
        shutil.rmtree("./var/objects/test12", True)

    def test_at_zentrale_recipe_generates_host_configurations(self) -> None:
        """Test that at_zentrale recipe generates host configurations.

        This test verifies that a recipe with 'at_zentrale' naming pattern
        executes correctly and generates host configurations in the expected
        directory structure.

        Test Setup:
            1. Clean existing test output directory
            2. Create directory for at-zentrale recipe output
            3. Execute coshsh-cook with at_zentrale recipe
            4. Verify host configurations are created

        Expected Behavior:
            - Dynamic hosts directory should be created
            - Host configuration file should be generated
            - Directory name uses modified recipe name (atzentralezentrale)
        """
        # Arrange: Clean and prepare output directory
        shutil.rmtree("./var/objects/test12", True)
        os.makedirs("./var/objects/test12/at-zentrale/dynamic")

        # Act: Execute recipe
        subprocess.call(
            "../bin/coshsh-cook --cookbook etc/coshsh_regex.cfg --recipe at_zentrale --debug",
            shell=True
        )

        # Assert: Verify output was created
        self.assertTrue(
            os.path.exists("var/objects/test12/atzentralezentrale/dynamic/hosts"),
            "Dynamic hosts directory should be created at var/objects/test12/atzentralezentrale/dynamic/hosts"
        )
        self.assertTrue(
            os.path.exists("var/objects/test12/atzentralezentrale/dynamic/hosts/test_host_1/os_windows_default.cfg"),
            "Windows host configuration should be created for test_host_1"
        )

    def test_at_lh2000_recipe_generates_host_configurations(self) -> None:
        """Test that at_lh2000 recipe generates host configurations.

        This test verifies that a recipe with 'at_lh2000' naming pattern
        executes correctly with a different subdirectory structure.

        Test Setup:
            1. Clean existing test output directory
            2. Create directory for at-lh2000 recipe output
            3. Execute coshsh-cook with at_lh2000 recipe
            4. Verify host configurations are created

        Expected Behavior:
            - Dynamic hosts directory should be created
            - Host configuration file should be generated
            - Directory name preserves recipe name (at-lh2000)
        """
        # Arrange: Clean and prepare output directory
        shutil.rmtree("./var/objects/test12", True)
        os.makedirs("./var/objects/test12/at-lh2000")

        # Act: Execute recipe
        subprocess.call(
            "../bin/coshsh-cook --cookbook etc/coshsh_regex.cfg --recipe at_lh2000 --debug",
            shell=True
        )

        # Assert: Verify output was created
        self.assertTrue(
            os.path.exists("var/objects/test12/at-lh2000/dynamic/hosts"),
            "Dynamic hosts directory should be created at var/objects/test12/at-lh2000/dynamic/hosts"
        )
        self.assertTrue(
            os.path.exists("var/objects/test12/at-lh2000/dynamic/hosts/test_host_1/os_windows_default.cfg"),
            "Windows host configuration should be created for test_host_1"
        )

    def test_pl_zentrale_recipe_generates_host_configurations(self) -> None:
        """Test that pl_zentrale recipe generates host configurations.

        This test verifies that recipes with Polish country prefix (pl_)
        execute correctly and generate configurations.

        Test Setup:
            1. Clean existing test output directory
            2. Create directory for pl_zentrale recipe output
            3. Execute coshsh-cook with pl_zentrale recipe
            4. Verify host configurations are created

        Expected Behavior:
            - Dynamic hosts directory should be created
            - Host configuration file should be generated
            - Directory name uses modified recipe name (plplzentralezentrale)
        """
        # Arrange: Clean and prepare output directory
        shutil.rmtree("./var/objects/test12", True)
        os.makedirs("./var/objects/test12/plplzentralezentrale")

        # Act: Execute recipe
        subprocess.call(
            "../bin/coshsh-cook --cookbook etc/coshsh_regex.cfg --recipe pl_zentrale --debug",
            shell=True
        )

        # Assert: Verify output was created
        self.assertTrue(
            os.path.exists("var/objects/test12/plplzentralezentrale/dynamic/hosts"),
            "Dynamic hosts directory should be created at var/objects/test12/plplzentralezentrale/dynamic/hosts"
        )
        self.assertTrue(
            os.path.exists("var/objects/test12/plplzentralezentrale/dynamic/hosts/test_host_1/os_windows_default.cfg"),
            "Windows host configuration should be created for test_host_1"
        )

    def test_pt_zentrale_recipe_generates_host_configurations(self) -> None:
        """Test that pt_zentrale recipe generates host configurations.

        This test verifies that recipes with Portuguese country prefix (pt_)
        execute correctly and generate configurations.

        Test Setup:
            1. Clean existing test output directory
            2. Create directory for pt_zentrale recipe output
            3. Execute coshsh-cook with pt_zentrale recipe
            4. Verify host configurations are created

        Expected Behavior:
            - Dynamic hosts directory should be created
            - Host configuration file should be generated
            - Directory name uses modified recipe name (ptptzentralezentrale)
        """
        # Arrange: Clean and prepare output directory
        shutil.rmtree("./var/objects/test12", True)
        os.makedirs("./var/objects/test12/ptptzentralezentrale")

        # Act: Execute recipe
        subprocess.call(
            "../bin/coshsh-cook --cookbook etc/coshsh_regex.cfg --recipe pt_zentrale --debug",
            shell=True
        )

        # Assert: Verify output was created
        self.assertTrue(
            os.path.exists("var/objects/test12/ptptzentralezentrale/dynamic/hosts"),
            "Dynamic hosts directory should be created at var/objects/test12/ptptzentralezentrale/dynamic/hosts"
        )
        self.assertTrue(
            os.path.exists("var/objects/test12/ptptzentralezentrale/dynamic/hosts/test_host_1/os_windows_default.cfg"),
            "Windows host configuration should be created for test_host_1"
        )
