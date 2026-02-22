"""Tests for MySQL application class — default port, port override via MonitoringDetail, and hostgroup assignment."""

import os
import coshsh
from tests.common_coshsh_test import CommonCoshshTest


class ApplicationMysqlTest(CommonCoshshTest):

    def test_create_server(self):
        """MySQL application is assigned default port 3306 during assemble."""
        self.setUpConfig("etc/coshsh.cfg", "test10")
        ds = self.generator.get_recipe("test10").get_datasource("csv10.1")
        ds.objects = self.generator.get_recipe("test10").objects
        ds.add("hosts", coshsh.host.Host({
            "host_name": "drivelsrv", "address": "11.120.9.10", "type": "Server", "os": "Red Hat 6.0", "hardware": "", "virtual": "vs", "notification_period": "7x24", "location": "2nd floor", "department": "ps"
        }))
        ds.add("applications", coshsh.application.Application({
            "name": "drivel", "type": "mysql", "component": "", "version": "", "patchlevel": "", "host_name": "drivelsrv", "check_period": "7x24"
        }))
        self.assertIn("drivelsrv", self.generator.get_recipe("test10").objects["hosts"])
        self.assertIn("drivelsrv+drivel+mysql", self.generator.get_recipe("test10").objects["applications"])
        self.generator.get_recipe("test10").assemble()
        h = self.generator.get_recipe("test10").objects["hosts"]["drivelsrv"]
        a = h.applications[0]
        self.assertTrue(hasattr(a, "port"))
        self.assertEqual(a.port, 3306)

    def test_create_server_alternative_port(self):
        """PORT MonitoringDetail overrides the default MySQL port during assemble."""
        self.setUpConfig("etc/coshsh.cfg", "test10")
        ds = self.generator.get_recipe("test10").get_datasource("csv10.1")
        ds.objects = self.generator.get_recipe("test10").objects
        ds.add("hosts", coshsh.host.Host({
            "host_name": "drivelsrv", "address": "11.120.9.10", "type": "Server", "os": "Red Hat 6.0", "hardware": "", "virtual": "vs", "notification_period": "7x24", "location": "2nd floor", "department": "ps"
        }))
        ds.add("applications", coshsh.application.Application({
            "name": "drivel", "type": "mysql", "component": "", "version": "", "patchlevel": "", "host_name": "drivelsrv", "check_period": "7x24"
        }))
        ds.add("details", coshsh.monitoringdetail.MonitoringDetail({
            "host_name": "drivelsrv",
            "name": "drivel",
            "type": "mysql",
            "monitoring_type": "PORT",
            "monitoring_0": 10000}))
        self.generator.get_recipe("test10").assemble()
        h = self.generator.get_recipe("test10").objects["hosts"]["drivelsrv"]
        a = h.applications[0]
        self.assertTrue(hasattr(a, "port"))
        self.assertEqual(a.port, 10000)

    def test_hostgroup_by_host(self):
        """Manually appended hostgroup is preserved after assemble."""
        self.setUpConfig("etc/coshsh.cfg", "test10")
        ds = self.generator.get_recipe("test10").get_datasource("csv10.1")
        ds.objects = self.generator.get_recipe("test10").objects
        ds.add("hosts", coshsh.host.Host({
            "host_name": "drivelsrv", "address": "11.120.9.10", "type": "Server", "os": "Red Hat 6.0", "hardware": "", "virtual": "vs", "notification_period": "7x24", "location": "2nd floor", "department": "ps"
        }))
        ds.get("hosts", "drivelsrv").hostgroups.append("mysql")
        ds.add("applications", coshsh.application.Application({
            "name": "drivel", "type": "mysql", "component": "", "version": "", "patchlevel": "", "host_name": "drivelsrv", "check_period": "7x24"
        }))
        ds.add("details", coshsh.monitoringdetail.MonitoringDetail({
            "host_name": "drivelsrv",
            "name": "drivel",
            "type": "mysql",
            "monitoring_type": "PORT",
            "monitoring_0": 10000}))
        self.generator.get_recipe("test10").assemble()
        self.assertEqual(self.generator.get_recipe("test10").objects["hosts"]["drivelsrv"].hostgroups, ["mysql"])
        self.assertEqual(len(self.generator.get_recipe("test10").objects["hosts"]["drivelsrv"].hostgroups), 1)

    def test_hostgroup_by_app(self):
        """MySQL application adds mysql-clusters hostgroup when host is in mysql hostgroup."""
        self.setUpConfig("etc/coshsh.cfg", "test10")
        ds = self.generator.get_recipe("test10").get_datasource("csv10.1")
        ds.objects = self.generator.get_recipe("test10").objects
        ds.add("hosts", coshsh.host.Host({
            "host_name": "drivelsrv-clustera", "address": "11.120.9.10", "type": "Server", "os": "Red Hat 6.0", "hardware": "", "virtual": "vs", "notification_period": "7x24", "location": "2nd floor", "department": "ps"
        }))
        ds.get("hosts", "drivelsrv-clustera").hostgroups.append("mysql")
        ds.add("applications", coshsh.application.Application({
            "name": "drivel", "type": "mysql", "component": "", "version": "", "patchlevel": "", "host_name": "drivelsrv-clustera", "check_period": "7x24"
        }))
        ds.add("details", coshsh.monitoringdetail.MonitoringDetail({
            "host_name": "drivelsrv-clustera",
            "name": "drivel",
            "type": "mysql",
            "monitoring_type": "PORT",
            "monitoring_0": 10000}))
        self.generator.get_recipe("test10").assemble()
        self.assertIn("mysql", self.generator.get_recipe("test10").objects["hosts"]["drivelsrv-clustera"].hostgroups)
        self.assertIn("mysql-clusters", self.generator.get_recipe("test10").objects["hosts"]["drivelsrv-clustera"].hostgroups)
        self.assertEqual(len(self.generator.get_recipe("test10").objects["hosts"]["drivelsrv-clustera"].hostgroups), 2)
