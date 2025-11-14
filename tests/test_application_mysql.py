"""Test suite for MySQL application plugin functionality.

This module tests the MySQL application plugin, including:
- Default port configuration (3306)
- Custom port configuration via monitoring details
- Hostgroup assignment from host attributes
- Automatic hostgroup assignment for cluster hosts
"""

from __future__ import annotations

import os
import coshsh
from tests.common_coshsh_test import CommonCoshshTest


class MysqlApplicationTest(CommonCoshshTest):
    """Test suite for MySQL application plugin.

    This test suite verifies that the MySQL application plugin correctly:
    - Assigns default port 3306 when no PORT monitoring detail exists
    - Overrides port when PORT monitoring detail is provided
    - Preserves hostgroups assigned directly to hosts
    - Automatically adds cluster-specific hostgroups for cluster hosts

    Test Configuration:
        Uses test recipe: test10
        Datasource: csv10.1
        Application type: mysql

    Related:
        See coshsh/application.py for application plugin loading
        See recipes/test10/ for MySQL plugin implementation
    """

    def test_mysql_application_uses_default_port_3306(self) -> None:
        """Test that MySQL application defaults to port 3306.

        When a MySQL application is created without a PORT monitoring detail,
        the MySQL plugin should automatically assign port 3306 as the default.

        Test Setup:
            1. Create a host 'drivelsrv'
            2. Add MySQL application without port specification
            3. Assemble the recipe to apply plugin logic

        Expected Behavior:
            - Host is created successfully
            - Application is created with key 'drivelsrv+drivel+mysql'
            - Application has 'port' attribute
            - Port value is 3306 (MySQL default)

        Assertions:
            - Host exists in recipe objects
            - Application exists in recipe objects
            - Application has port attribute
            - Port equals 3306
        """
        # Arrange: Set up recipe and datasource
        self.setUpConfig("etc/coshsh.cfg", "test10")
        recipe = self.generator.get_recipe("test10")
        ds = recipe.get_datasource("csv10.1")
        ds.objects = recipe.objects

        # Add host
        ds.add("hosts", coshsh.host.Host({
            'host_name': 'drivelsrv', 'address': '11.120.9.10', 'type': 'Server',
            'os': 'Red Hat 6.0', 'hardware': '', 'virtual': 'vs',
            'notification_period': '7x24', 'location': '2nd floor', 'department': 'ps'
        }))

        # Add MySQL application without port specification
        ds.add("applications", coshsh.application.Application({
            'name': 'drivel', 'type': 'mysql', 'component': '', 'version': '',
            'patchlevel': '', 'host_name': 'drivelsrv', 'check_period': '7x24'
        }))

        # Verify objects were added
        self.assertIn(
            "drivelsrv", recipe.objects["hosts"],
            "Host 'drivelsrv' should be added to recipe objects"
        )
        self.assertIn(
            "drivelsrv+drivel+mysql", recipe.objects["applications"],
            "MySQL application should be added with key 'drivelsrv+drivel+mysql'"
        )

        # Act: Assemble recipe to apply plugin logic
        recipe.assemble()

        # Assert: Verify default port is set
        host = recipe.objects["hosts"]["drivelsrv"]
        application = host.applications[0]

        self.assertTrue(
            hasattr(application, "port"),
            "MySQL application should have 'port' attribute"
        )
        self.assertEqual(
            application.port, 3306,
            "MySQL application should default to port 3306"
        )

    def test_mysql_application_uses_custom_port_from_monitoring_detail(self) -> None:
        """Test that MySQL application uses custom port from monitoring detail.

        When a PORT monitoring detail is provided, the MySQL plugin should
        use that port instead of the default 3306.

        Test Setup:
            1. Create a host 'drivelsrv'
            2. Add MySQL application
            3. Add PORT monitoring detail with custom port 10000
            4. Assemble the recipe

        Expected Behavior:
            - Application port is set to 10000 (from monitoring detail)
            - Default port 3306 is not used

        Assertions:
            - Application has port attribute
            - Port equals 10000 (custom value from monitoring detail)
        """
        # Arrange: Set up recipe and datasource
        self.setUpConfig("etc/coshsh.cfg", "test10")
        recipe = self.generator.get_recipe("test10")
        ds = recipe.get_datasource("csv10.1")
        ds.objects = recipe.objects

        # Add host
        ds.add("hosts", coshsh.host.Host({
            'host_name': 'drivelsrv', 'address': '11.120.9.10', 'type': 'Server',
            'os': 'Red Hat 6.0', 'hardware': '', 'virtual': 'vs',
            'notification_period': '7x24', 'location': '2nd floor', 'department': 'ps'
        }))

        # Add MySQL application
        ds.add("applications", coshsh.application.Application({
            'name': 'drivel', 'type': 'mysql', 'component': '', 'version': '',
            'patchlevel': '', 'host_name': 'drivelsrv', 'check_period': '7x24'
        }))

        # Add PORT monitoring detail with custom port
        ds.add("details", coshsh.monitoringdetail.MonitoringDetail({
            'host_name': 'drivelsrv',
            'name': 'drivel',
            'type': 'mysql',
            'monitoring_type': 'PORT',
            'monitoring_0': 10000
        }))

        # Act: Assemble recipe to apply monitoring details
        recipe.assemble()

        # Assert: Verify custom port is set
        host = recipe.objects["hosts"]["drivelsrv"]
        application = host.applications[0]

        self.assertTrue(
            hasattr(application, "port"),
            "MySQL application should have 'port' attribute"
        )
        self.assertEqual(
            application.port, 10000,
            "MySQL application should use custom port 10000 from monitoring detail"
        )

    def test_mysql_hostgroup_assignment_from_host_attribute(self) -> None:
        """Test that hostgroups assigned to host are preserved.

        When a host has hostgroups assigned directly (not from application),
        those hostgroups should be preserved and not modified.

        Test Setup:
            1. Create host with 'mysql' hostgroup assigned directly
            2. Add MySQL application
            3. Add monitoring detail
            4. Assemble recipe

        Expected Behavior:
            - Host retains exactly the hostgroup assigned to it
            - No additional hostgroups are added
            - Hostgroups list contains only 'mysql'

        Assertions:
            - Host has hostgroups ['mysql']
            - Hostgroups list length is 1
        """
        # Arrange: Set up recipe and datasource
        self.setUpConfig("etc/coshsh.cfg", "test10")
        recipe = self.generator.get_recipe("test10")
        ds = recipe.get_datasource("csv10.1")
        ds.objects = recipe.objects

        # Add host
        ds.add("hosts", coshsh.host.Host({
            'host_name': 'drivelsrv', 'address': '11.120.9.10', 'type': 'Server',
            'os': 'Red Hat 6.0', 'hardware': '', 'virtual': 'vs',
            'notification_period': '7x24', 'location': '2nd floor', 'department': 'ps'
        }))

        # Assign hostgroup directly to host
        ds.get("hosts", "drivelsrv").hostgroups.append("mysql")

        # Add MySQL application
        ds.add("applications", coshsh.application.Application({
            'name': 'drivel', 'type': 'mysql', 'component': '', 'version': '',
            'patchlevel': '', 'host_name': 'drivelsrv', 'check_period': '7x24'
        }))

        # Add monitoring detail
        ds.add("details", coshsh.monitoringdetail.MonitoringDetail({
            'host_name': 'drivelsrv',
            'name': 'drivel',
            'type': 'mysql',
            'monitoring_type': 'PORT',
            'monitoring_0': 10000
        }))

        # Act: Assemble recipe
        recipe.assemble()

        # Assert: Verify hostgroup is preserved
        host = recipe.objects["hosts"]["drivelsrv"]

        self.assertEqual(
            host.hostgroups, ["mysql"],
            "Host should have exactly the 'mysql' hostgroup assigned"
        )
        self.assertEqual(
            len(host.hostgroups), 1,
            "Host should have exactly 1 hostgroup"
        )

    def test_mysql_cluster_host_gets_additional_cluster_hostgroup(self) -> None:
        """Test that cluster hosts get automatic cluster-specific hostgroups.

        When a host name contains 'cluster' and has MySQL application,
        the plugin should automatically add a cluster-specific hostgroup
        in addition to the base MySQL hostgroup.

        Test Setup:
            1. Create host named 'drivelsrv-clustera' with 'mysql' hostgroup
            2. Add MySQL application
            3. Add monitoring detail
            4. Assemble recipe

        Expected Behavior:
            - Original 'mysql' hostgroup is preserved
            - Additional 'mysql-clusters' hostgroup is added
            - Total of 2 hostgroups

        Assertions:
            - 'mysql' hostgroup exists
            - 'mysql-clusters' hostgroup exists
            - Total hostgroups count is 2
        """
        # Arrange: Set up recipe and datasource
        self.setUpConfig("etc/coshsh.cfg", "test10")
        recipe = self.generator.get_recipe("test10")
        ds = recipe.get_datasource("csv10.1")
        ds.objects = recipe.objects

        # Add host with 'cluster' in the name
        ds.add("hosts", coshsh.host.Host({
            'host_name': 'drivelsrv-clustera', 'address': '11.120.9.10', 'type': 'Server',
            'os': 'Red Hat 6.0', 'hardware': '', 'virtual': 'vs',
            'notification_period': '7x24', 'location': '2nd floor', 'department': 'ps'
        }))

        # Assign base MySQL hostgroup
        ds.get("hosts", "drivelsrv-clustera").hostgroups.append("mysql")

        # Add MySQL application
        ds.add("applications", coshsh.application.Application({
            'name': 'drivel', 'type': 'mysql', 'component': '', 'version': '',
            'patchlevel': '', 'host_name': 'drivelsrv-clustera', 'check_period': '7x24'
        }))

        # Add monitoring detail
        ds.add("details", coshsh.monitoringdetail.MonitoringDetail({
            'host_name': 'drivelsrv-clustera',
            'name': 'drivel',
            'type': 'mysql',
            'monitoring_type': 'PORT',
            'monitoring_0': 10000
        }))

        # Act: Assemble recipe (triggers hostgroup logic)
        recipe.assemble()

        # Assert: Verify both hostgroups are present
        host = recipe.objects["hosts"]["drivelsrv-clustera"]

        self.assertIn(
            "mysql", host.hostgroups,
            "Host should have 'mysql' hostgroup"
        )
        self.assertIn(
            "mysql-clusters", host.hostgroups,
            "Cluster host should have 'mysql-clusters' hostgroup"
        )
        self.assertEqual(
            len(host.hostgroups), 2,
            "Host should have exactly 2 hostgroups (mysql and mysql-clusters)"
        )


if __name__ == '__main__':
    unittest.main()


