#!/usr/bin/env python3
"""Test suite for coshsh command-line binary tools.

This module tests the command-line executables:
- coshsh-cook: Main recipe processing command
- coshsh-create-template-tree: Template hierarchy extraction tool

These tests verify that the CLI tools work correctly with various
configuration options and produce expected output files.
"""

from __future__ import annotations

import os
import io
import shutil
import subprocess
from tests.common_coshsh_test import CommonCoshshTest


class BinaryToolsTest(CommonCoshshTest):
    """Test suite for coshsh command-line binary tools.

    This test suite verifies that the coshsh CLI binaries work correctly:
    - coshsh-cook: Processes recipes and generates monitoring configs
    - coshsh-create-template-tree: Extracts template inheritance hierarchy

    These integration tests ensure the command-line interface works correctly
    and produces expected output files in the correct locations.

    Test Configuration:
        Uses test recipe: test4
        Config files: etc/coshsh.cfg, etc/coshsh6.cfg
        Output directory: var/objects/test1/

    Related:
        See bin/coshsh-cook for the main CLI implementation
        See bin/coshsh-create-template-tree for template tree tool
    """

    def tearDown(self) -> None:
        """Clean up test output directories.

        Removes:
            - var/objects/test1/: Main test output directory
            - var/objects/test1_mod/: Modified configuration output directory
        """
        shutil.rmtree("./var/objects/test1", True)
        shutil.rmtree("./var/objects/test1_mod", True)

    def test_coshsh_cook_generates_monitoring_configuration(self) -> None:
        """Test that coshsh-cook binary generates monitoring configuration files.

        The coshsh-cook command-line tool should process a recipe and generate
        all expected Nagios configuration files in the correct directory structure.

        Test Setup:
            1. Run coshsh-cook with cookbook and recipe arguments
            2. Process test4 recipe with simplesample datasource

        Expected Behavior:
            - Output directory structure is created
            - Host configuration directories are created
            - Application configuration files are generated
            - Configuration files contain expected content

        Assertions:
            - Dynamic hosts directory exists
            - test_host_0 directory exists
            - Linux OS configuration file exists
            - Windows OS configuration file exists
            - Windows config contains expected check directive
        """
        # Act: Run coshsh-cook to generate monitoring configuration
        subprocess.call(
            "../bin/coshsh-cook --cookbook etc/coshsh.cfg --recipe test4",
            shell=True
        )

        # Assert: Verify output directory structure
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts"),
            "Dynamic hosts directory should be created by coshsh-cook"
        )

        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"),
            "test_host_0 directory should be created for the test host"
        )

        # Assert: Verify configuration files were generated
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"),
            "Linux OS configuration file should be generated"
        )

        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg"),
            "Windows OS configuration file should be generated"
        )

        # Assert: Verify configuration file content
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()

        self.assertIn(
            'os_windows_default_check_unittest',
            os_windows_default_cfg,
            "Windows config should contain the unittest check directive"
        )

    def test_create_template_tree_extracts_template_hierarchy(self) -> None:
        """Test that coshsh-create-template-tree extracts template inheritance.

        The coshsh-create-template-tree tool should analyze templates and
        extract the complete inheritance hierarchy, creating static template
        definition files.

        This is useful for understanding template relationships and creating
        static Nagios template configuration files.

        Test Setup:
            1. Create static output directory
            2. Run coshsh-create-template-tree for os_windows_fs template
            3. Verify template files are extracted

        Expected Behavior:
            - Static service_templates directory is created
            - Template file for requested template is created
            - Parent template files are also created (inheritance chain)

        Assertions:
            - Static directory exists before running command
            - Binary exists
            - service_templates directory is created
            - os_windows_fs.cfg template file exists
            - os_windows.cfg parent template file exists
        """
        # Arrange: Print test header and create output directory
        self.print_header()
        os.makedirs("./var/objects/test1/static")

        self.assertTrue(
            os.path.exists("var/objects/test1/static"),
            "Static output directory should be created"
        )

        self.assertTrue(
            os.path.exists("../bin/coshsh-create-template-tree"),
            "coshsh-create-template-tree binary should exist"
        )

        # Act: Run template tree extraction
        subprocess.call(
            "../bin/coshsh-create-template-tree --cookbook etc/coshsh.cfg "
            "--recipe test4 --template os_windows_fs",
            shell=True
        )

        # Assert: Verify template hierarchy was extracted
        self.assertTrue(
            os.path.exists("var/objects/test1/static/service_templates"),
            "service_templates directory should be created"
        )

        self.assertTrue(
            os.path.exists("var/objects/test1/static/service_templates/os_windows_fs.cfg"),
            "Template file for os_windows_fs should be created"
        )

        self.assertTrue(
            os.path.exists("var/objects/test1/static/service_templates/os_windows.cfg"),
            "Parent template file os_windows.cfg should also be created (inheritance)"
        )

    def test_create_template_tree_with_multiple_cookbooks(self) -> None:
        """Test template tree extraction with multiple cookbook files.

        The coshsh-create-template-tree tool should support multiple --cookbook
        arguments, merging configuration from multiple files. This allows
        for modular configuration management.

        Test Setup:
            1. Create output directories for both configurations
            2. Run with multiple --cookbook arguments
            3. Verify output in the correct target directory

        Expected Behavior:
            - Tool accepts multiple --cookbook arguments
            - Configuration is merged from all cookbooks
            - Output goes to the target directory from the last cookbook
            - Template files are created correctly

        Assertions:
            - Both output directories exist
            - Binary exists
            - service_templates directory created in modified config output
            - Template files exist in correct location
            - Parent templates are also extracted
        """
        # Arrange: Print test header and create output directories
        self.print_header()
        os.makedirs("./var/objects/test1/static")
        os.makedirs("./var/objects/test1_mod/static")

        self.assertTrue(
            os.path.exists("var/objects/test1/static"),
            "First output directory should exist"
        )

        self.assertTrue(
            os.path.exists("var/objects/test1_mod/static"),
            "Second output directory (modified) should exist"
        )

        self.assertTrue(
            os.path.exists("../bin/coshsh-create-template-tree"),
            "coshsh-create-template-tree binary should exist"
        )

        # Act: Run with multiple cookbooks
        subprocess.call(
            "../bin/coshsh-create-template-tree "
            "--cookbook etc/coshsh.cfg --cookbook etc/coshsh6.cfg "
            "--recipe test4 --template os_windows_fs",
            shell=True
        )

        # Assert: Verify output in the modified configuration directory
        self.assertTrue(
            os.path.exists("var/objects/test1_mod/static/service_templates"),
            "service_templates directory should be created in modified output directory"
        )

        self.assertTrue(
            os.path.exists("var/objects/test1_mod/static/service_templates/os_windows_fs.cfg"),
            "Template file os_windows_fs.cfg should exist in modified output"
        )

        self.assertTrue(
            os.path.exists("var/objects/test1_mod/static/service_templates/os_windows.cfg"),
            "Parent template os_windows.cfg should exist in modified output"
        )


