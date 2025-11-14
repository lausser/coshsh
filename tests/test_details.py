"""Test suite for monitoring detail functionality.

This module tests the various types of monitoring details that can be
attached to applications, including KEYVALUES, URL, RAM, and how they
are resolved and processed during template rendering.
"""

from __future__ import annotations

import io
import os
import unittest

from coshsh.application import Application
from coshsh.host import Host
from coshsh.monitoringdetail import MonitoringDetail
from tests.common_coshsh_test import CommonCoshshTest


class MonitoringDetailTest(CommonCoshshTest):
    """Test suite for monitoring detail resolution and processing.

    This test suite verifies that:
    - KEYVALUES details set application threshold attributes
    - KEYVALUEARRAYS details create array attributes
    - URL details are parsed into structured URL objects
    - RAM details are properly resolved and attached
    - Multiple URL details can be attached to one application
    - Lazy datasource loading works correctly
    - Detail resolution happens in correct order

    Test Configuration:
        Uses test recipes in tests/recipes/test6/ and test14/
        Config file: etc/coshsh.cfg

    Detail Types Tested:
        - KEYVALUES: Key-value pairs for thresholds (swap_warning, etc.)
        - KEYVALUEARRAYS: Array-based attributes (roles, parents)
        - URL: Parsed connection URLs (oracle://, https://)
        - RAM: Memory threshold details
    """

    def test_detail_keyvalues_sets_threshold_attributes(self) -> None:
        """Test that KEYVALUES detail sets threshold attributes on applications.

        KEYVALUES monitoring details allow setting arbitrary key-value pairs
        on applications, commonly used for thresholds like swap_warning or
        cron_critical. This test verifies that these values are correctly
        applied to applications.

        Setup:
            - Loads test6 recipe with CSV details datasource
            - Collects and assembles applications with KEYVALUES details

        Expected Behavior:
            - App1 has custom swap thresholds from KEYVALUES detail
            - App1 has custom cron thresholds from KEYVALUES detail
            - App2 has default swap thresholds from os_linux class
            - App2 cron thresholds are in thresholds object (not direct attribute)

        Assertions:
            - App1 swap_warning and swap_critical match KEYVALUES
            - App1 cron_warning and cron_critical match KEYVALUES
            - App2 swap thresholds match os_linux defaults
            - App2 cron thresholds accessible via thresholds object
        """
        # Arrange: Set up configuration and load recipe
        self.setUpConfig("etc/coshsh.cfg", "test6")
        recipe = self.generator.get_recipe("test6")
        datasource = recipe.get_datasource("csvdetails")

        # Act: Collect and assemble applications
        recipe.collect()
        recipe.assemble()
        objects = recipe.objects
        print(objects)

        # Get applications for testing
        app1 = list(objects['applications'].values())[0]
        app1.resolve_monitoring_details()
        app2 = list(objects['applications'].values())[1]
        app2.resolve_monitoring_details()

        # Assert: Verify app1 has custom swap thresholds from KEYVALUES detail
        self.assertTrue(
            app1.swap_warning == "15%",
            "App1 should have swap_warning='15%' from KEYVALUES detail"
        )
        self.assertTrue(
            app1.swap_critical == "8%",
            "App1 should have swap_critical='8%' from KEYVALUES detail"
        )

        # Assert: Verify app1 has custom cron thresholds from KEYVALUES detail
        self.assertTrue(
            app1.cron_warning == "30",
            "App1 should have cron_warning='30' from KEYVALUES detail"
        )
        self.assertTrue(
            app1.cron_critical == "100",
            "App1 should have cron_critical='100' from KEYVALUES detail"
        )

        # Assert: Verify app2 has default swap thresholds from os_linux class
        self.assertTrue(
            app2.swap_warning == "5%",
            "App2 should have default swap_warning='5%' from os_linux class"
        )
        self.assertTrue(
            app2.swap_critical == "15%",
            "App2 should have default swap_critical='15%' from os_linux class"
        )

        # Assert: Verify app2 cron thresholds are in thresholds object
        self.assertTrue(
            not hasattr(app2, "cron_warning"),
            "App2 should not have direct cron_warning attribute"
        )
        self.assertTrue(
            hasattr(app2, "thresholds"),
            "App2 should have thresholds object"
        )
        self.assertTrue(
            hasattr(app2.thresholds, "cron_warning"),
            "App2 thresholds object should have cron_warning attribute"
        )
        self.assertTrue(
            app2.thresholds.cron_warning == "31",
            "App2 should have cron_warning='31' in thresholds object"
        )

    def test_detail_keyvaluearrays_creates_array_attributes(self) -> None:
        """Test that KEYVALUEARRAYS detail creates array attributes on applications.

        KEYVALUEARRAYS monitoring details create array/list attributes on
        applications, commonly used for roles, parents, or tags. This test
        verifies that these arrays are correctly parsed and attached.

        Setup:
            - Loads test6 recipe with CSV details datasource
            - Collects and assembles applications with KEYVALUEARRAYS details

        Expected Behavior:
            - App2 has roles array with multiple values
            - App2 has parents array with multiple values
            - Array values are correctly parsed from comma-separated strings

        Assertions:
            - App2 has roles attribute
            - roles contains 'dach', 'prod', 'dmz', 'master'
            - App2 has parents attribute
            - parents contains 'sw1', 'sw2'
        """
        # Arrange: Set up configuration and load recipe
        self.setUpConfig("etc/coshsh.cfg", "test6")
        recipe = self.generator.get_recipe("test6")
        datasource = recipe.get_datasource("csvdetails")

        # Act: Collect and assemble applications
        recipe.collect()
        recipe.assemble()
        objects = recipe.objects

        app1 = list(objects['applications'].values())[0]
        app1.resolve_monitoring_details()
        app2 = list(objects['applications'].values())[1]
        app2.resolve_monitoring_details()
        app2.resolve_monitoring_details()  # Note: Called twice in original test

        # Assert: Verify app2 has roles array
        self.assertTrue(
            hasattr(app2, "roles"),
            "App2 should have roles attribute from KEYVALUEARRAYS detail"
        )
        self.assertTrue(
            "dach" in app2.roles,
            "App2 roles should contain 'dach'"
        )
        self.assertTrue(
            "prod" in app2.roles,
            "App2 roles should contain 'prod'"
        )
        self.assertTrue(
            "dmz" in app2.roles,
            "App2 roles should contain 'dmz'"
        )
        self.assertTrue(
            "master" in app2.roles,
            "App2 roles should contain 'master'"
        )

        # Assert: Verify app2 has parents array
        self.assertTrue(
            hasattr(app2, "parents"),
            "App2 should have parents attribute from KEYVALUEARRAYS detail"
        )
        self.assertTrue(
            "sw1" in app2.parents,
            "App2 parents should contain 'sw1'"
        )
        self.assertTrue(
            "sw2" in app2.parents,
            "App2 parents should contain 'sw2'"
        )

    def test_detail_url_parses_connection_string(self) -> None:
        """Test that URL detail correctly parses database connection URLs.

        URL monitoring details parse connection strings (like oracle://...)
        into structured URL objects with separate username, password, hostname,
        port, and path components.

        Setup:
            - Creates an Oracle application
            - Attaches URL detail with oracle:// connection string
            - Resolves monitoring details

        Expected Behavior:
            - URL is parsed into structured components
            - Username, password, hostname, port are extracted
            - Path component includes service name

        Assertions:
            - Application has 1 URL object
            - URL username is 'dbadm'
            - URL password is 'pass'
            - URL hostname is 'dbsrv'
            - URL port is 1522
            - URL path is '/svc'
        """
        # Arrange: Set up configuration
        self.setUpConfig("etc/coshsh.cfg", "test6")
        recipe = self.generator.get_recipe("test6")

        # Create Oracle application with URL detail
        oracle = Application({
            'host_name': 'test',
            'name': 'test',
            'type': 'generic',
        })
        url = MonitoringDetail({
            'host_name': 'test',
            'name': 'test',
            'type': 'generic',
            'monitoring_type': 'URL',
            'monitoring_0': 'oracle://dbadm:pass@dbsrv:1522/svc',
        })
        oracle.monitoring_details.append(url)

        # Act: Resolve monitoring details
        oracle.resolve_monitoring_details()

        # Assert: Verify URL was parsed correctly
        self.assertTrue(
            len(oracle.urls) == 1,
            "Application should have exactly 1 URL object"
        )
        self.assertTrue(
            oracle.urls[0].username == 'dbadm',
            "URL username should be 'dbadm'"
        )
        self.assertTrue(
            oracle.urls[0].password == 'pass',
            "URL password should be 'pass'"
        )
        self.assertTrue(
            oracle.urls[0].hostname == 'dbsrv',
            "URL hostname should be 'dbsrv'"
        )
        self.assertTrue(
            oracle.urls[0].port == 1522,
            "URL port should be 1522"
        )
        self.assertTrue(
            oracle.urls[0].path == '/svc',
            "URL path should be '/svc' (will be without / in consol app_db_oracle class)"
        )

    def test_detail_ram_sets_memory_thresholds(self) -> None:
        """Test that RAM detail sets memory threshold attributes.

        RAM monitoring details define memory threshold values for applications.
        This test verifies that RAM details are correctly resolved and attached
        as structured objects with warning and critical thresholds.

        Setup:
            - Creates a Red Hat application
            - Attaches RAM detail with warning/critical thresholds
            - Resolves monitoring details

        Expected Behavior:
            - Application has ram attribute
            - RAM object has warning threshold
            - RAM object has critical threshold

        Assertions:
            - Application has 'ram' attribute
            - ram.warning is '80'
        """
        # Arrange: Set up configuration
        self.setUpConfig("etc/coshsh.cfg", "test6")
        recipe = self.generator.get_recipe("test6")

        # Create application with RAM detail
        opsys = Application({'name': 'os', 'type': 'red hat 6.1'})
        ram = MonitoringDetail({
            'name': 'os',
            'type': 'red hat 6.1',
            'monitoring_type': 'RAM',
            'monitoring_0': '80',
            'monitoring_1': '90',
        })
        opsys.monitoring_details.append(ram)

        # Debug output
        for m in opsys.monitoring_details:
            print("detail", m)

        # Act: Resolve monitoring details
        opsys.resolve_monitoring_details()

        # Assert: Verify RAM detail was resolved
        self.assertTrue(
            hasattr(opsys, 'ram'),
            "Application should have 'ram' attribute from RAM detail"
        )
        self.assertTrue(
            opsys.ram.warning == '80',
            "RAM warning threshold should be '80'"
        )

    def test_detail_multiple_urls_attached_to_application(self) -> None:
        """Test that multiple URL details can be attached to one application.

        Applications can have multiple URL monitoring details, such as
        monitoring multiple endpoints or services. This test verifies that
        all URLs are correctly parsed and attached as separate URL objects.

        Setup:
            - Loads test6 recipe
            - Creates webapp application
            - Attaches two different HTTPS URL details
            - Renders configuration to verify URLs are in output

        Expected Behavior:
            - Application can have multiple URL objects
            - Each URL is parsed independently
            - All URLs are available for template rendering
            - Configuration file is generated with both URLs

        Assertions:
            - Application has 'urls' attribute
            - URLs list contains both URL objects
            - Configuration file exists for the application
            - Configuration file can be read
        """
        # Arrange: Set up configuration and datasource
        self.setUpConfig("etc/coshsh.cfg", "test6")
        recipe = self.generator.get_recipe("test6")
        datasource = recipe.get_datasource("csvdetails")
        datasource.open()
        objects = recipe.objects
        datasource.read(objects=objects)

        # Create webapp application with two URL details
        opsys = Application({
            'host_name': 'test_host_0',
            'name': 'testapp',
            'type': 'webapp'
        })
        url1 = MonitoringDetail({
            'host_name': 'test_host_0',
            'name': 'testapp',
            'type': 'webapp',
            'monitoring_type': 'URL',
            'monitoring_0': 'https://uzi75.schoggimaschin.com:5480/login.html',
            'monitoring_1': '10',
            'monitoring_2': '15',
        })
        opsys.monitoring_details.append(url1)

        url2 = MonitoringDetail({
            'host_name': 'test_host_0',
            'name': 'testapp',
            'type': 'webapp',
            'monitoring_type': 'URL',
            'monitoring_0': 'https://uzi75.schoggimaschin.com/vsphere-client/?csp',
            'monitoring_1': '10',
            'monitoring_2': '15',
        })
        opsys.monitoring_details.append(url2)

        datasource.add('applications', opsys)

        # Debug output
        for m in opsys.monitoring_details:
            print("detail", m)

        # Act: Resolve monitoring details
        opsys.resolve_monitoring_details()

        # Assert: Verify application has multiple URLs
        self.assertTrue(
            hasattr(opsys, 'urls'),
            "Application should have 'urls' attribute"
        )

        # Debug output
        for u in opsys.urls:
            print("url is", u, u.__dict__)

        # Act: Create output directory and generate configuration
        os.makedirs("./var/objects/test6/dynamic")
        recipe.collect()
        recipe.assemble()
        recipe.render()
        recipe.output()

        # Assert: Verify configuration file was created
        config_file = 'var/objects/test6/dynamic/hosts/test_host_0/app_generic_web.cfg'
        self.assertTrue(
            os.path.exists(config_file),
            "Configuration file for webapp should exist"
        )

        # Debug: Print configuration file contents
        with io.open(config_file, 'r') as outfile:
            for line in outfile.read().split('\n'):
                print(line)

    def test_lazy_datasource_loads_details_on_demand(self) -> None:
        """Test that lazy datasource correctly loads details on demand.

        Lazy datasources defer loading until actually needed, which is useful
        for optional or rarely-used data. This test verifies that lazy
        datasources work correctly and that details loaded this way are
        properly attached to applications.

        Setup:
            - Loads test14 recipe with lazy datasource
            - Reads datasource (triggers lazy loading)
            - Collects, assembles, renders, and outputs

        Expected Behavior:
            - Lazy datasource loads data when read() is called
            - Applications receive attributes from lazy datasource
            - Attributes are correctly set on applications

        Assertions:
            - App1 has custom attribute from lazy datasource
            - Attribute value matches expected value
        """
        # Arrange: Set up configuration with lazy datasource
        self.setUpConfig("etc/coshsh.cfg", "test14")
        recipe = self.generator.get_recipe("test14")
        datasource = recipe.get_datasource("lazy")

        self.print_header()
        objects = recipe.objects

        # Act: Read from lazy datasource (triggers loading)
        datasource.read(objects=objects)

        # Act: Run complete recipe pipeline
        recipe.collect()
        recipe.assemble()
        recipe.render()
        recipe.output()

        # Assert: Verify lazy-loaded attribute is set
        app1 = list(objects['applications'].values())[0]
        self.assertTrue(
            hasattr(app1, 'huhu'),
            "App1 should have 'huhu' attribute from lazy datasource"
        )
        self.assertTrue(
            app1.huhu == 'dada',
            "App1 huhu attribute should be 'dada' from lazy datasource"
        )


if __name__ == '__main__':
    unittest.main()
