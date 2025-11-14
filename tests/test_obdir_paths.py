"""Test suite for output directory paths and hostgroup name handling.

This module tests that output directories and files are created correctly,
and that special characters (like '/') in hostgroup names are handled
properly without breaking filesystem paths.
"""

from __future__ import annotations

import io
import os

from coshsh.application import Application, GenericApplication
from coshsh.host import Host
from tests.common_coshsh_test import CommonCoshshTest


class OutputDirectoryPathTest(CommonCoshshTest):
    """Test suite for output directory paths and special character handling.

    This suite verifies that:
    - Generic applications are correctly identified and instantiated
    - Hostgroups with special characters (e.g., '/') are handled correctly
    - Hostgroup filenames are sanitized but aliases preserve original names
    - Output directories and files are created in expected locations

    Special Focus:
        Hostgroup names with '/' should have sanitized filenames but preserve
        the original name in the hostgroup alias.

    Test Configuration:
        Uses config file: etc/coshsh5.cfg
        Recipe: test33
        Objects directory: ./var/objects/test33
    """

    _configfile = 'etc/coshsh5.cfg'
    _objectsdir = "./var/objects/test33"

    def tearDown(self) -> None:
        """Clean up after test.

        Note: Currently empty but preserved for future cleanup needs.
        """
        pass

    def test_generic_application_with_sanitized_hostgroup_names(self) -> None:
        """Test generic application handling and hostgroup name sanitization.

        This test verifies that:
        1. Unknown application types fall back to GenericApplication class
        2. Hostgroups with special characters (like '/') are sanitized in filenames
        3. Original hostgroup names are preserved in configuration content
        4. Output directories and files are created correctly

        This is critical because:
        - Not all application types have custom classes (fallback needed)
        - Filesystem paths cannot contain '/' in filenames
        - Nagios config should use original hostgroup names for consistency

        Test Scenario:
            Create a host with hostgroups "servers" and "08/15"
            Add an unknown application type "arschknarsch"
            Verify it becomes GenericApplication
            Verify hostgroup files are created with sanitized names
            Verify hostgroup configs contain original names

        Setup:
            Creates a test host and generic application manually
            Adds hostgroups with special characters

        Expected Behavior:
            - Application is GenericApplication instance
            - Hostgroup "servers" → file: hostgroup_servers.cfg
            - Hostgroup "08/15" → file: hostgroup_08_15_5641.cfg
            - File content contains "08/15" (original name)
            - Generic application templates are NOT rendered

        Assertions:
            - Application count is correct
            - Application is GenericApplication class
            - Host config file exists
            - Hostgroup files exist with sanitized names
            - Hostgroup configs contain original names
        """
        # Arrange: Set up config and recipe
        self.setUpConfig("etc/coshsh5.cfg", "test33")
        r = self.generator.get_recipe("test33")
        ds = self.generator.get_recipe("test33").get_datasource("simplesample")
        ds.objects = r.objects

        # Arrange: Create host with special hostgroups
        host = Host({
            'host_name': 'testhost',
            'address': '127.0.0.1',
        })
        ds.add('hosts', host)
        host.hostgroups.append("servers")
        host.hostgroups.append("08/15")  # Hostgroup with '/' character

        # Arrange: Create application with unknown type
        app = Application({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',  # Unknown type should become GenericApplication
        })
        ds.add('applications', app)

        # Act: Run recipe workflow
        r.collect()
        r.assemble()
        r.render()

        # Assert: Verify application is GenericApplication
        self.assertEqual(
            len(r.objects['applications']),
            1,
            "Should have exactly one application"
        )
        self.assertEqual(
            ds.getall('applications')[0],
            app,
            "Datasource should return the same application object"
        )
        self.assertEqual(
            ds.getall('applications')[0].__class__,
            GenericApplication,
            "Unknown application type should become GenericApplication"
        )

        # Act: Write output files
        r.output()

        # Assert: Verify host config exists
        self.assertTrue(
            os.path.exists("var/objects/test33/dynamic/hosts/testhost/host.cfg"),
            "Host config file should be created"
        )

        # Assert: Verify hostgroup files with sanitized names
        self.assertTrue(
            os.path.exists("var/objects/test33/dynamic/hostgroups/hostgroup_servers.cfg"),
            "Hostgroup file should be created for 'servers'"
        )
        self.assertTrue(
            os.path.exists("var/objects/test33/dynamic/hostgroups/hostgroup_08_15_5641.cfg"),
            "Hostgroup file should be created with sanitized name for '08/15'"
        )

        # Assert: Verify hostgroup content preserves original name
        with io.open("var/objects/test33/dynamic/hostgroups/hostgroup_servers.cfg") as f:
            hg = f.read()
        self.assertIn(
            'servers',
            hg,
            "Hostgroup config should contain original 'servers' name"
        )

        with io.open("var/objects/test33/dynamic/hostgroups/hostgroup_08_15_5641.cfg") as f:
            hg = f.read()
        self.assertIn(
            '08/15',
            hg,
            "Hostgroup config should contain original '08/15' name (not sanitized)"
        )
        self.assertNotIn(
            '08_15',
            hg,
            "Hostgroup config should NOT contain sanitized name '08_15' in alias"
        )

        # Assert: Verify generic application templates are NOT rendered
        self.assertFalse(
            os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_fs.cfg"),
            "Generic application should not render my_generic_fs template"
        )
        self.assertFalse(
            os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_ports.cfg"),
            "Generic application should not render my_generic_ports template"
        )

