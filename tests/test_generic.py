"""Test suite for generic application handling.

This module tests the GenericApplication functionality which provides
fallback handling for applications that don't have specific plugin
implementations.
"""

from __future__ import annotations

import os

from coshsh.application import Application, GenericApplication
from coshsh.host import Host
from coshsh.monitoringdetail import MonitoringDetail
from tests.common_coshsh_test import CommonCoshshTest


class GenericApplicationTest(CommonCoshshTest):
    """Test suite for generic application plugin loading and behavior.

    This suite verifies that:
    - Applications without specific plugins fall back to GenericApplication
    - Custom generic applications (MyGenericApplication) are loaded correctly
    - Generic applications don't generate config files without details
    - Custom generic applications generate config files when details are present
    - MonitoringDetails are properly associated with generic applications

    Test Configuration:
        Uses test recipes: test33, test34
        Configuration file: etc/coshsh5.cfg
        Output directory: var/objects/test33

    Related:
        See also: test_applications.py for specific application plugin tests
    """

    _configfile = 'etc/coshsh5.cfg'
    _objectsdir = "./var/objects/test33"

    def test_generic_application_fallback_for_unknown_type(self) -> None:
        """Test that unknown application types fall back to GenericApplication.

        When an application type doesn't have a specific plugin implementation,
        it should automatically use the GenericApplication class as a fallback.
        Generic applications without monitoring details should NOT generate
        application-specific config files.

        Test Setup:
            - Creates a host manually
            - Creates an application with unknown type 'arschknarsch'
            - No monitoring details are added
            - Processes through full recipe pipeline

        Expected Behavior:
            - Application is created successfully
            - Application class is GenericApplication (fallback)
            - Host config file is generated
            - NO application-specific config files are generated

        Assertions:
            - 1 application exists in recipe.objects
            - Application instance is GenericApplication
            - Host config exists
            - Generic filesystem config does NOT exist
            - Generic ports config does NOT exist
        """
        # Arrange: Set up recipe and manually create host and application
        self.setUpConfig("etc/coshsh5.cfg", "test33")
        recipe = self.generator.get_recipe("test33")
        datasource = self.generator.get_recipe("test33").get_datasource("simplesample")
        datasource.objects = recipe.objects

        host = Host({
            'host_name': 'testhost',
            'address': '127.0.0.1',
        })
        datasource.add('hosts', host)

        app = Application({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',
        })
        datasource.add('applications', app)

        # Act: Process recipe
        recipe.collect()
        recipe.assemble()
        recipe.render()
        recipe.output()

        # Assert: Verify GenericApplication is used and no app configs generated
        self.assertTrue(
            len(recipe.objects['applications']) == 1,
            "Should have exactly 1 application loaded"
        )
        self.assertTrue(
            datasource.getall('applications')[0] == app,
            "Loaded application should match the created application"
        )
        self.assertTrue(
            datasource.getall('applications')[0].__class__ == GenericApplication,
            "Unknown application type should fall back to GenericApplication"
        )
        self.assertTrue(
            os.path.exists("var/objects/test33/dynamic/hosts/testhost/host.cfg"),
            "Host config file should be generated"
        )
        self.assertTrue(
            not os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_fs.cfg"),
            "Generic filesystem config should NOT be generated without details"
        )
        self.assertTrue(
            not os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_ports.cfg"),
            "Generic ports config should NOT be generated without details"
        )

    def test_custom_generic_application_with_monitoring_details(self) -> None:
        """Test that custom generic applications generate configs with details.

        When a custom GenericApplication subclass (MyGenericApplication) is
        available and monitoring details are provided, it should generate
        application-specific configuration files.

        Test Setup:
            - Recipe 'test34' uses custom MyGenericApplication
            - Creates host and application manually
            - Adds FILESYSTEM monitoring detail (/, 90%, 95%)
            - Adds PORT monitoring detail (port 80, 1, 5)
            - Processes through full recipe pipeline

        Expected Behavior:
            - Application uses MyGenericApplication class
            - Application-specific config files are generated for:
              * Filesystem monitoring
              * Port monitoring

        Assertions:
            - 1 application exists in recipe.objects
            - Application class is MyGenericApplication (not base GenericApplication)
            - Host config exists
            - Filesystem config exists
            - Ports config exists
        """
        # Arrange: Set up recipe with custom generic application
        self.setUpConfig("etc/coshsh5.cfg", "test34")
        recipe = self.generator.get_recipe("test34")
        datasource = self.generator.get_recipe("test34").get_datasource("simplesample")
        datasource.objects = recipe.objects

        host = Host({
            'host_name': 'testhost',
            'address': '127.0.0.1',
        })
        datasource.add('hosts', host)

        app = Application({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',
        })
        datasource.add('applications', app)

        # Add filesystem monitoring detail
        datasource.add('details', MonitoringDetail({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',
            'monitoring_type': 'FILESYSTEM',
            'monitoring_0': '/',
            'monitoring_1': 90,
            'monitoring_2': 95,
        }))

        # Add port monitoring detail
        datasource.add('details', MonitoringDetail({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',
            'monitoring_type': 'PORT',
            'monitoring_0': 80,
            'monitoring_1': 1,
            'monitoring_2': 5,
        }))

        # Act: Process recipe
        recipe.collect()
        recipe.assemble()
        recipe.render()
        recipe.output()

        # Assert: Verify custom generic application and config generation
        self.assertTrue(
            len(recipe.objects['applications']) == 1,
            "Should have exactly 1 application loaded"
        )
        self.assertTrue(
            datasource.getall('applications')[0] == app,
            "Loaded application should match the created application"
        )
        self.assertTrue(
            datasource.getall('applications')[0].__class__.__name__ == "MyGenericApplication",
            "Application should use custom MyGenericApplication class"
        )
        self.assertTrue(
            os.path.exists("var/objects/test33/dynamic/hosts/testhost/host.cfg"),
            "Host config file should be generated"
        )
        self.assertTrue(
            os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_fs.cfg"),
            "Filesystem config should be generated for application with FILESYSTEM detail"
        )
        self.assertTrue(
            os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_ports.cfg"),
            "Ports config should be generated for application with PORT detail"
        )
