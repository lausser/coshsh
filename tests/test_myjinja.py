"""Test suite for Jinja2 template rendering functionality.

This module tests the Jinja2 template rendering system in coshsh,
verifying that templates are correctly processed and application
objects are accessible within template contexts.
"""

from __future__ import annotations

import io
import os

from tests.common_coshsh_test import CommonCoshshTest


class JinjaTemplateTest(CommonCoshshTest):
    """Test suite for Jinja2 template rendering.

    This suite verifies that:
    - Jinja2 templates are correctly rendered
    - Multiple application types can be rendered for the same host
    - Template context includes application type, class, and tuple information
    - Generated configuration files contain expected content

    Test Configuration:
        Uses config file: etc/coshsh.cfg
        Recipe: testjinja
        Test data: recipes/test4/
    """

    def test_jinja_templates_render_multiple_application_types_correctly(self) -> None:
        """Test that Jinja2 templates correctly render multiple application types.

        This test verifies that a single host can have multiple application
        configurations rendered from Jinja2 templates, and that the template
        context correctly exposes application metadata (type, class, tuple).

        This is critical because:
        - Templates need access to application attributes
        - Multiple applications on one host must be rendered independently
        - Template comments should include diagnostic information

        Setup:
            Loads testjinja recipe which has templates using Jinja2 syntax
            to access application metadata.

        Expected Behavior:
            - Multiple config files are generated per host
            - os_linux_default.cfg contains Linux application data
            - os_windows_default.cfg contains Windows application data
            - os_windows_kaas.cfg contains both Linux and Windows data with
              type, class, and tuple information in comments

        Assertions:
            - Configuration files exist in expected locations
            - File contents include application class names
            - File contents include type comments
            - File contents include tuple representations
        """
        # Arrange: Set up config and get recipe
        self.setUpConfig("etc/coshsh.cfg", "testjinja")
        r = self.generator.get_recipe("testjinja")

        # Act: Run the complete recipe workflow
        self.generator.run()

        # Assert: Verify output files exist
        self.assertTrue(
            os.path.exists('var/objects/test4/dynamic/hosts/test_host_0/os_linux_default.cfg'),
            "Linux default config file should be generated"
        )
        self.assertTrue(
            os.path.exists('var/objects/test4/dynamic/hosts/test_host_0/os_windows_default.cfg'),
            "Windows default config file should be generated"
        )

        # Assert: Verify template rendering with application metadata
        with io.open("var/objects/test4/dynamic/hosts/test_host_0/os_windows_kaas.cfg") as f:
            os_windows_kaas_cfg = f.read()

            # Verify Linux application metadata in template
            self.assertIn(
                'os_linux.Linux',
                os_windows_kaas_cfg,
                "Template should contain Linux application class name"
            )
            self.assertIn(
                '# type is red hat',
                os_windows_kaas_cfg,
                "Template should contain Linux application type comment"
            )
            self.assertIn(
                '# class is Linux',
                os_windows_kaas_cfg,
                "Template should contain Linux class comment"
            )
            self.assertIn(
                "# ('red hat', 'os', 'linux')",
                os_windows_kaas_cfg,
                "Template should contain Linux application tuple representation"
            )
            self.assertIn(
                'ttype is red hat',
                os_windows_kaas_cfg,
                "Template should contain Linux type variable output"
            )

            # Verify Windows application metadata in template
            self.assertIn(
                'os_windows.Windows',
                os_windows_kaas_cfg,
                "Template should contain Windows application class name"
            )
            self.assertIn(
                '# type is windows',
                os_windows_kaas_cfg,
                "Template should contain Windows application type comment"
            )
            self.assertIn(
                '# class is Windows',
                os_windows_kaas_cfg,
                "Template should contain Windows class comment"
            )
            self.assertIn(
                "# ('windows', 'os', 'windows')",
                os_windows_kaas_cfg,
                "Template should contain Windows application tuple representation"
            )
            self.assertIn(
                'ttype is windows',
                os_windows_kaas_cfg,
                "Template should contain Windows type variable output"
            )

