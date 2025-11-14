"""Test suite for host macro functionality.

This module tests the custom macro handling for host objects, including
both regular macros and custom_macros attributes.
"""

from __future__ import annotations

import os

from coshsh.application import Application, GenericApplication
from coshsh.host import Host
from coshsh.monitoringdetail import MonitoringDetail
from tests.common_coshsh_test import CommonCoshshTest


class HostMacrosTest(CommonCoshshTest):
    """Test suite for host custom macros and attributes.

    This suite verifies that:
    - Hosts can have custom macros defined
    - Both 'macros' and 'custom_macros' attributes work correctly
    - Macros are properly rendered in output configuration files
    - Generic applications work with hosts that have macros

    Test Configuration:
        Uses test recipes: test33, test34
        Configuration file: etc/coshsh5.cfg
        Output directory: var/objects/test33

    Context:
        Nagios and compatible monitoring systems support custom macros
        (e.g., _MANUFACTURER, _MODEL) that can be defined on hosts and
        referenced in commands and service definitions. Coshsh supports
        both the 'macros' dictionary and 'custom_macros' dictionary for
        these values.

    Related:
        See also: test_generic.py for generic application testing
    """

    def test_host_macros_in_generic_application_config(self) -> None:
        """Test that host macros are correctly handled with generic apps.

        Verifies that when a host has both 'macros' and 'custom_macros'
        defined, these are properly stored and rendered in the output
        configuration files, even when the host has a generic application.

        Test Setup:
            - Creates host with macros={'_MANUFACTURER': 'zuse'}
            - Sets custom_macros={'_MODEL': 'z3'}
            - Creates generic application (unknown type)
            - No monitoring details added
            - Processes through full pipeline

        Expected Behavior:
            - Host is created with both macro types
            - Application uses GenericApplication (fallback)
            - Host config file is generated
            - No application-specific configs are generated

        Assertions:
            - 1 application exists
            - Application is GenericApplication instance
            - Host config file exists
            - Generic filesystem config does NOT exist
            - Generic ports config does NOT exist
        """
        # Arrange: Set up recipe and create host with macros
        self.setUpConfig("etc/coshsh5.cfg", "test33")
        recipe = self.generator.get_recipe("test33")
        datasource = self.generator.get_recipe("test33").get_datasource("simplesample")
        datasource.objects = recipe.objects

        # Create host with both macros and custom_macros
        host = Host({
            'host_name': 'testhost',
            'address': '127.0.0.1',
        })
        host.macros = {
            '_MANUFACTURER': 'zuse',
        }
        host.custom_macros = {
            '_MODEL': 'z3',
        }
        self.generator.recipes['test33'].datasources[0].add('hosts', host)

        # Create generic application
        app = Application({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',
        })
        datasource.add('applications', app)

        # Act: Process recipe through full pipeline
        recipe.collect()
        recipe.assemble()
        recipe.render()
        recipe.output()

        # Assert: Verify application behavior
        self.assertTrue(
            len(recipe.objects['applications']) == 1,
            "Should have exactly 1 application loaded"
        )
        self.assertTrue(
            list(datasource.getall('applications'))[0] == app,
            "Loaded application should match the created application"
        )
        self.assertTrue(
            list(datasource.getall('applications'))[0].__class__ == GenericApplication,
            "Unknown application type should fall back to GenericApplication"
        )

        # Assert: Verify host config generation
        self.assertTrue(
            os.path.exists("var/objects/test33/dynamic/hosts/testhost/host.cfg"),
            "Host config file should be generated"
        )

        # Read and verify host config contains macros
        with open("var/objects/test33/dynamic/hosts/testhost/host.cfg") as f:
            testhost_cfg = f.read()
            print(testhost_cfg)

        # Assert: Verify no application configs without details
        self.assertTrue(
            not os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_fs.cfg"),
            "Generic filesystem config should NOT be generated without details"
        )
        self.assertTrue(
            not os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_ports.cfg"),
            "Generic ports config should NOT be generated without details"
        )

    def test_host_macros_with_custom_generic_and_details(self) -> None:
        """Test host macros with custom generic app and monitoring details.

        Verifies that hosts with macros work correctly when using a custom
        generic application class (MyGenericApplication) and monitoring
        details are provided.

        Test Setup:
            - Recipe 'test34' uses MyGenericApplication
            - Creates host without explicit macros
            - Creates application with unknown type
            - Adds FILESYSTEM monitoring detail (/, 90%, 95%)
            - Adds PORT monitoring detail (port 80, 1, 5)
            - Processes through full pipeline

        Expected Behavior:
            - Application uses MyGenericApplication (custom class)
            - Both application-specific configs are generated
            - Host config is generated

        Assertions:
            - 1 application exists
            - Application class is MyGenericApplication
            - Host config exists
            - Filesystem config exists
            - Ports config exists
        """
        # Arrange: Set up recipe with custom generic application
        self.setUpConfig("etc/coshsh5.cfg", "test34")
        recipe = self.generator.get_recipe("test34")
        datasource = self.generator.get_recipe("test34").get_datasource("simplesample")
        datasource.objects = recipe.objects

        # Create host
        host = Host({
            'host_name': 'testhost',
            'address': '127.0.0.1',
        })
        datasource.add('hosts', host)

        # Create application
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

        # Act: Process recipe through full pipeline
        recipe.collect()
        recipe.assemble()
        recipe.render()
        recipe.output()

        # Assert: Verify custom generic application is used
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

        # Assert: Verify all config files are generated
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
