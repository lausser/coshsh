"""Test suite for class and template priority ordering.

This module tests that user-defined classes and templates take priority
over default ones when multiple class/template directories are configured,
following the left-to-right priority order.
"""

from __future__ import annotations

import io
import os

from tests.common_coshsh_test import CommonCoshshTest


class ClassPriorityTest(CommonCoshshTest):
    """Test suite for class and template loading priority.

    This suite verifies that:
    - Classes and templates are loaded with correct priority order
    - User/department classes override corporate/default classes
    - User/department templates override corporate/default templates
    - Multiple class directories work correctly (left takes priority)
    - Classes from higher-priority directories have custom markers

    Directory Priority (left to right):
        classes_dir = ./recipes/test13d/classes,./recipes/test13c/classes
        templates_dir = ./recipes/test13d/templates,./recipes/test13c/templates

        department (highest)  corporate (medium)    default (lowest)
        os_linux.py           os_linux.py           os_linux.py
        os_beos.py
        os_aix.py             os_aix.py
                              os_dos.py

        department (highest)  corporate (medium)    default (lowest)
        os_linux_default.tpl  os_linux_default.tpl  os_linux_default.tpl
                              os_beos_default.tpl
        os_aix_default.tpl    os_aix_default.tpl
        os_dos_default.tpl

    Expected Priority Resolution:
        - Linux: department class & template (leftmost)
        - BeOS: department class, corporate template
        - AIX: department class & template (leftmost)
        - DOS: corporate class & template (middle)
        - Windows: default class & template (rightmost)

    Test Configuration:
        Uses config file: etc/coshsh.cfg
        Recipe: test13
        Multiple class/template directories with different priorities
    """

    def test_classes_and_templates_respect_priority_order(self) -> None:
        """Test that classes and templates are loaded with correct priority.

        This test verifies the complete priority system for loading classes
        and templates from multiple directories. This is critical for allowing
        users to override default classes and templates with custom versions.

        Priority Rules:
            1. Classes: Leftmost directory wins
            2. Templates: Leftmost directory wins
            3. Custom classes can have 'marker' attribute to identify source

        Test Scenario:
            Configure multiple class/template directories:
            - department (highest priority)
            - corporate (medium priority)
            - default (lowest priority)

            Test that each OS type loads the correct class and template
            based on priority.

        Setup:
            Loads test13 recipe with multiple class/template directories
            configured in priority order.

        Expected Behavior:
            Classes:
            - linux_host: department class (has 'marker' = 'department')
            - beos_host: department class (has 'marker' = 'department')
            - aix_host: department class (has 'marker' = 'department')
            - dos_host: corporate class (has 'marker' = 'corporate')
            - windows_host: default class (no 'marker' attribute)

            Templates:
            - linux_host: department template (contains 'department')
            - beos_host: corporate template (contains 'corporate')
            - aix_host: department template (contains 'department')
            - dos_host: department template (contains 'department')
            - windows_host: default template (contains 'define')

        Assertions:
            - Config files exist for all hosts
            - Applications have correct 'marker' attribute
            - Generated configs contain expected priority markers
        """
        # Arrange: Set up config and recipe
        self.setUpConfig("etc/coshsh.cfg", "test13")
        r = self.generator.get_recipe("test13")

        # Act: Run complete recipe workflow
        self.generator.run()

        # Assert: Verify host has config_files attribute
        self.assertTrue(
            hasattr(self.generator.recipes['test13'].objects['hosts']['linux_host'], 'config_files'),
            "Host should have config_files attribute after rendering"
        )
        self.assertIn(
            'host.cfg',
            self.generator.recipes['test13'].objects['hosts']['linux_host'].config_files['nagios'],
            "Host should have host.cfg in nagios config files"
        )

        # Assert: Verify output directory structure
        self.assertTrue(
            os.path.exists("var/objects/test13/dynamic/hosts"),
            "Dynamic hosts directory should be created"
        )
        self.assertTrue(
            os.path.exists("var/objects/test13/dynamic/hosts/linux_host"),
            "linux_host directory should be created"
        )

        # Assert: Verify config files exist for all OS types
        self.assertTrue(
            os.path.exists("var/objects/test13/dynamic/hosts/linux_host/os_linux_default.cfg"),
            "Linux config file should be created"
        )
        self.assertTrue(
            os.path.exists("var/objects/test13/dynamic/hosts/aix_host/os_aix_default.cfg"),
            "AIX config file should be created"
        )
        self.assertTrue(
            os.path.exists("var/objects/test13/dynamic/hosts/beos_host/os_beos_default.cfg"),
            "BeOS config file should be created"
        )
        self.assertTrue(
            os.path.exists("var/objects/test13/dynamic/hosts/dos_host/os_dos_default.cfg"),
            "DOS config file should be created"
        )
        self.assertTrue(
            os.path.exists("var/objects/test13/dynamic/hosts/windows_host/os_windows_default.cfg"),
            "Windows config file should be created"
        )

        # Assert: Verify class priority (marker attribute indicates source)
        print(self.generator.recipes['test13'].objects['applications'])

        self.assertEqual(
            self.generator.recipes['test13'].objects['applications']['linux_host+os+red hat'].marker,
            'department',
            "Linux application should use department class (highest priority)"
        )
        self.assertEqual(
            self.generator.recipes['test13'].objects['applications']['beos_host+os+beos'].marker,
            'department',
            "BeOS application should use department class (highest priority)"
        )
        self.assertEqual(
            self.generator.recipes['test13'].objects['applications']['aix_host+os+aix'].marker,
            'department',
            "AIX application should use department class (highest priority)"
        )
        self.assertEqual(
            self.generator.recipes['test13'].objects['applications']['dos_host+os+dos'].marker,
            'corporate',
            "DOS application should use corporate class (medium priority)"
        )
        self.assertFalse(
            hasattr(self.generator.recipes['test13'].objects['applications']['windows_host+os+windows'], 'marker'),
            "Windows application should use default class (no marker attribute)"
        )

        # Assert: Verify template priority (content indicates source)
        with io.open("var/objects/test13/dynamic/hosts/linux_host/os_linux_default.cfg") as f:
            os_linux_default_cfg = f.read()
        self.assertIn(
            'department',
            os_linux_default_cfg,
            "Linux config should use department template (highest priority)"
        )

        with io.open("var/objects/test13/dynamic/hosts/beos_host/os_beos_default.cfg") as f:
            os_beos_default_cfg = f.read()
        self.assertIn(
            'corporate',
            os_beos_default_cfg,
            "BeOS config should use corporate template (no department template exists)"
        )

        with io.open("var/objects/test13/dynamic/hosts/aix_host/os_aix_default.cfg") as f:
            os_aix_default_cfg = f.read()
        self.assertIn(
            'department',
            os_aix_default_cfg,
            "AIX config should use department template (highest priority)"
        )

        with io.open("var/objects/test13/dynamic/hosts/dos_host/os_dos_default.cfg") as f:
            os_dos_default_cfg = f.read()
        self.assertIn(
            'department',
            os_dos_default_cfg,
            "DOS config should use department template (highest priority)"
        )

        with io.open("var/objects/test13/dynamic/hosts/windows_host/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertIn(
            'define',
            os_windows_default_cfg,
            "Windows config should use default template (lowest priority)"
        )

        with io.open("var/objects/test13/dynamic/hosts/windows_host/host.cfg") as f:
            host_cfg = f.read()
        self.assertIn(
            'corporate host',
            host_cfg,
            "Windows host config should contain 'corporate host' from template"
        )


