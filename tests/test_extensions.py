"""Test suite for template extension functionality.

This module tests template extensions and environment variable substitution
in Jinja2 templates, verifying that templates can access OS environment
variables and provide default values.
"""

from __future__ import annotations

import io
import os
import shutil

from tests.common_coshsh_test import CommonCoshshTest


class TemplateExtensionsTest(CommonCoshshTest):
    """Test suite for Jinja2 template extensions and environment variable access.

    This test suite verifies that:
    - Templates can access OS environment variables
    - Templates can provide default values for missing environment variables
    - Environment variable substitution works in template rendering
    - Templates handle conditional logic based on environment variables
    - Multiple environment variables can be used in one template

    Test Configuration:
        Uses test recipe in tests/recipes/test4b/
        Config file: etc/coshsh.cfg
        Output directory: ./var/objects/test1

    Template Extensions Tested:
        - os.environ: Access to OS environment variables
        - Default values: Fallback when environment variable is not set
        - Conditional rendering: if/else based on environment variables
    """

    def test_osenviron_substitution_in_templates(self) -> None:
        """Test that templates can access and substitute OS environment variables.

        This test verifies the template extension that allows Jinja2 templates
        to access OS environment variables through os.environ. It tests both
        reading environment variables and providing default values when they
        are not set.

        The test runs multiple scenarios:
        1. No environment variables set (uses defaults)
        2. Environment variables set (uses actual values)
        3. Conditional rendering based on environment variable values

        Setup:
            - Loads test4b recipe configuration
            - Runs complete recipe pipeline
            - Modifies environment variables between runs
            - Re-renders templates with different environment values

        Expected Behavior:
            - When env var is not set, template uses default value
            - When env var is set, template uses actual value
            - Templates can conditionally render based on env var values
            - Multiple env vars can be used in one template

        Assertions:
            - Host config files are created
            - Config files contain correct environment variable values
            - Config files contain correct default values when vars not set
            - Conditional rendering works based on env var values
        """
        # Arrange: Set up configuration and load recipe
        self.setUpConfig("etc/coshsh.cfg", "test4b")
        recipe = self.generator.get_recipe("test4b")

        # Act: Run complete recipe pipeline without environment variables set
        recipe.count_before_objects()
        recipe.cleanup_target_dir()
        recipe.prepare_target_dir()
        recipe.collect()
        recipe.assemble()
        recipe.render()

        # Assert: Verify host config files were created
        self.assertTrue(
            hasattr(recipe.objects['hosts']['test_host_0'], 'config_files'),
            "Host should have config_files attribute after rendering"
        )
        self.assertTrue(
            'host.cfg' in recipe.objects['hosts']['test_host_0'].config_files["nagios"],
            "Host should have host.cfg in nagios config files"
        )

        # Act: Write rendered configs to filesystem
        recipe.output()

        # Assert: Verify output directories and files exist
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts"),
            "Dynamic hosts directory should exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"),
            "Host directory should exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"),
            "Linux application config should exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg"),
            "Windows application config should exist"
        )

        # Assert: Verify environment variable defaults (no env vars set)
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()

        self.assertTrue(
            'environment variable COSHSHENV1 ()' in os_windows_default_cfg,
            "Config should show COSHSHENV1 as empty when not set"
        )
        self.assertTrue(
            'environment default COSHSHENV1 (schlurz)' in os_windows_default_cfg,
            "Config should use default value 'schlurz' when COSHSHENV1 not set"
        )

        # Act: Clean output and set environment variables
        shutil.rmtree("./var/objects/test1", True)
        os.makedirs("./var/objects/test1")
        os.environ["COSHSHENV1"] = "die nr 1"
        os.environ["COSHSHENV2"] = "die nr 2"

        # Re-render with environment variables set
        recipe.render()
        recipe.output()

        # Assert: Verify environment variable substitution (env vars set)
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()

        self.assertTrue(
            'environment variable COSHSHENV1 (die nr 1)' in os_windows_default_cfg,
            "Config should show COSHSHENV1 actual value 'die nr 1'"
        )
        self.assertTrue(
            'environment variable COSHSHENV2 (die nr 2)' in os_windows_default_cfg,
            "Config should show COSHSHENV2 actual value 'die nr 2'"
        )
        self.assertTrue(
            'environment default COSHSHENV1 (die nr 1)' in os_windows_default_cfg,
            "Config should use actual value 'die nr 1' instead of default"
        )
        self.assertTrue(
            'environment variante die nr 2' in os_windows_default_cfg,
            "Config should show conditional rendering based on COSHSHENV2"
        )

        # Act: Clean output and test conditional rendering (variant 1)
        shutil.rmtree("./var/objects/test1", True)
        os.makedirs("./var/objects/test1")
        os.environ["COSHSHENV1"] = "variante1"

        recipe.render()
        recipe.output()

        # Assert: Verify conditional rendering for variant1
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()

        self.assertTrue(
            'environment variable COSHSHENV1 (variante1)' in os_windows_default_cfg,
            "Config should show COSHSHENV1 value 'variante1'"
        )
        self.assertTrue(
            'environment variable COSHSHENV2 (die nr 2)' in os_windows_default_cfg,
            "Config should still show COSHSHENV2 value from previous setting"
        )
        self.assertTrue(
            'environment variante variante1' in os_windows_default_cfg,
            "Config should show conditional content for variante1"
        )

        # Act: Clean output and test conditional rendering (variant x)
        shutil.rmtree("./var/objects/test1", True)
        os.makedirs("./var/objects/test1")
        os.environ["COSHSHENV1"] = "variantex"

        recipe.render()
        recipe.output()

        # Assert: Verify conditional rendering for variantex
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()

        self.assertTrue(
            'environment variable COSHSHENV1 (variantex)' in os_windows_default_cfg,
            "Config should show COSHSHENV1 value 'variantex'"
        )
        self.assertTrue(
            'environment variable COSHSHENV2 (die nr 2)' in os_windows_default_cfg,
            "Config should still show COSHSHENV2 value"
        )
        self.assertTrue(
            'environment variante die nr 2' in os_windows_default_cfg,
            "Config should show fallback conditional content (uses COSHSHENV2)"
        )
