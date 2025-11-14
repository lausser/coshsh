"""Test suite for generic catch-all application functionality.

This module tests the generic application catch-all feature, which handles
applications that don't have specific plugin implementations. Tests verify:
- Generic application plugin loading for unknown types
- Multiple monitoring detail types (FILESYSTEM, PORT, custom)
- Configuration file generation for generic applications
- Custom log file configuration
"""

from __future__ import annotations

import os
import shutil
import coshsh
from coshsh.host import Host
from coshsh.application import Application
from coshsh.monitoringdetail import MonitoringDetail
from tests.common_coshsh_test import CommonCoshshTest


class CatchallApplicationTest(CommonCoshshTest):
    """Test suite for generic catch-all application handling.

    This test suite verifies that coshsh can handle applications without
    specific plugin implementations using a generic catch-all mechanism.
    This is important for flexibility when monitoring custom or unusual
    application types.

    The generic application handler should:
    - Load for any application type without a specific plugin
    - Accept various monitoring detail types (FILESYSTEM, PORT, custom types)
    - Generate appropriate configuration files for each monitoring type
    - Support custom logging configuration

    Test Configuration:
        Uses test recipe: test34
        Config file: etc/coshsh5.cfg
        Custom application plugin: MyGenericApplication
        Log file: /tmp/coshsh_test34.log
        Output directory: var/objects/test33/

    Related:
        See coshsh/application.py for application plugin loading
        See recipes/test34/classes/ for MyGenericApplication implementation
    """

    def test_generic_application_handles_multiple_monitoring_detail_types(self) -> None:
        """Test that generic application handles multiple monitoring detail types.

        When an application type doesn't have a specific plugin, coshsh should
        fall back to a generic application handler that can process various
        monitoring detail types and generate appropriate configuration files.

        This test verifies the complete workflow:
        1. Generic plugin loading for unknown application type
        2. Processing multiple monitoring detail types
        3. Configuration file generation for each detail type

        Test Setup:
            1. Remove old log file if exists
            2. Load config with custom log file setting
            3. Create host and generic application (type 'arschknarsch')
            4. Add three monitoring details:
               - FILESYSTEM: Root filesystem with warn/crit thresholds
               - PORT: HTTP port 80 with connection parameters
               - BLINKENLIGHT: Custom monitoring type
            5. Process through collect -> assemble -> render -> output

        Expected Behavior:
            - Log file is created during initialization
            - Application is loaded with MyGenericApplication class
            - Recipe processes without errors
            - Configuration files are generated for each monitoring type:
              * host.cfg: Base host configuration
              * app_my_generic_fs.cfg: Filesystem monitoring
              * app_my_generic_ports.cfg: Port monitoring
              * app_my_generic_blinkenlights.cfg: Custom monitoring

        Assertions:
            - Log file exists
            - Exactly 1 application is created
            - Application is correct instance
            - Application class is MyGenericApplication
            - All expected configuration files exist
        """
        # Arrange: Clean up old log file and set up configuration
        shutil.rmtree("/tmp/coshsh_test34.log", True)
        self.setUpConfig("etc/coshsh5.cfg", "test34")

        # Verify log file was created during initialization
        self.assertTrue(
            os.path.exists("/tmp/coshsh_test34.log"),
            "Recipe initialization should create custom log file"
        )

        # Get recipe and update class factories
        recipe = self.generator.get_recipe("test34")
        recipe.update_item_class_factories()

        datasource = recipe.get_datasource("simplesample")
        datasource.objects = recipe.objects

        # Create host
        host = Host({
            'host_name': 'testhost',
            'address': '127.0.0.1',
        })
        datasource.add('hosts', host)

        # Create generic application with unknown type
        app = Application({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',  # Unknown type -> should use generic handler
        })
        datasource.add('applications', app)

        # Add FILESYSTEM monitoring detail
        datasource.add('details', MonitoringDetail({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',
            'monitoring_type': 'FILESYSTEM',
            'monitoring_0': '/',        # Filesystem path
            'monitoring_1': 90,         # Warning threshold
            'monitoring_2': 95,         # Critical threshold
        }))

        # Add PORT monitoring detail
        datasource.add('details', MonitoringDetail({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',
            'monitoring_type': 'PORT',
            'monitoring_0': 80,         # Port number
            'monitoring_1': 1,          # Connection timeout
            'monitoring_2': 5,          # Max retries
        }))

        # Add custom BLINKENLIGHT monitoring detail
        datasource.add('details', MonitoringDetail({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',
            'monitoring_type': 'BLINKENLIGHT',
            'monitoring_0': 'red',
        }))

        # Act: Process recipe through complete workflow
        recipe.collect()
        recipe.assemble()
        recipe.render()

        # Assert: Verify application was created correctly
        self.assertEqual(
            len(recipe.objects['applications']), 1,
            "Should have exactly 1 application created"
        )

        applications = recipe.datasources[0].getall('applications')
        first_app = applications[0]

        self.assertIs(
            first_app, app,
            "Retrieved application should be the same instance as created"
        )

        self.assertEqual(
            first_app.__class__.__name__, "MyGenericApplication",
            "Unknown application type should be handled by MyGenericApplication class"
        )

        # Act: Write configuration files
        recipe.output()

        # Assert: Verify all configuration files were generated
        self.assertTrue(
            os.path.exists("var/objects/test33/dynamic/hosts/testhost/host.cfg"),
            "Base host configuration file should be generated"
        )

        self.assertTrue(
            os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_fs.cfg"),
            "Filesystem monitoring configuration should be generated for FILESYSTEM detail"
        )

        self.assertTrue(
            os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_ports.cfg"),
            "Port monitoring configuration should be generated for PORT detail"
        )

        self.assertTrue(
            os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_blinkenlights.cfg"),
            "Custom monitoring configuration should be generated for BLINKENLIGHT detail"
        )


