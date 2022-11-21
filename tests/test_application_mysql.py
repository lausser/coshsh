import os
import coshsh
from tests.common_coshsh_test import CommonCoshshTest


class CoshshTest(CommonCoshshTest):

    def test_create_server(self):
        self.setUpConfig("etc/coshsh.cfg", "test10")
        ds = self.generator.get_recipe("test10").get_datasource("csv10.1")
        ds.objects = self.generator.get_recipe("test10").objects
        ds.add("hosts", coshsh.host.Host({
            'host_name': 'drivelsrv', 'address': '11.120.9.10', 'type': 'Server', 'os': 'Red Hat 6.0', 'hardware': '', 'virtual': 'vs', 'notification_period': '7x24', 'location': '2nd floor', 'department': 'ps'
        }))
        ds.add("applications", coshsh.application.Application({
            'name': 'drivel', 'type': 'mysql', 'component': '', 'version': '', 'patchlevel': '', 'host_name': 'drivelsrv', 'check_period': '7x24'
        }))
        self.assertTrue("drivelsrv" in self.generator.get_recipe("test10").objects["hosts"])
        self.assertTrue("drivelsrv+drivel+mysql" in self.generator.get_recipe("test10").objects["applications"])
        self.generator.get_recipe("test10").assemble()
        h = self.generator.get_recipe("test10").objects["hosts"]["drivelsrv"]
        a = h.applications[0]
        self.assertTrue(hasattr(a, "port"))
        self.assertTrue(a.port == 3306)
       

    def test_create_server_alternative_port(self):
        self.setUpConfig("etc/coshsh.cfg", "test10")
        ds = self.generator.get_recipe("test10").get_datasource("csv10.1")
        ds.objects = self.generator.get_recipe("test10").objects
        ds.add("hosts", coshsh.host.Host({
            'host_name': 'drivelsrv', 'address': '11.120.9.10', 'type': 'Server', 'os': 'Red Hat 6.0', 'hardware': '', 'virtual': 'vs', 'notification_period': '7x24', 'location': '2nd floor', 'department': 'ps'
        }))
        ds.add("applications", coshsh.application.Application({
            'name': 'drivel', 'type': 'mysql', 'component': '', 'version': '', 'patchlevel': '', 'host_name': 'drivelsrv', 'check_period': '7x24'
        }))
        ds.add("details", coshsh.monitoringdetail.MonitoringDetail({
            'host_name': 'drivelsrv',
            'name': 'drivel',
            'type': 'mysql',
            "monitoring_type" : "PORT",
            "monitoring_0" : 10000}))
        self.generator.get_recipe("test10").assemble()
        h = self.generator.get_recipe("test10").objects["hosts"]["drivelsrv"]
        a = h.applications[0]
        self.assertTrue(hasattr(a, "port"))
        self.assertTrue(a.port == 10000)

    def test_hostgroup_by_host(self):
        self.setUpConfig("etc/coshsh.cfg", "test10")
        ds = self.generator.get_recipe("test10").get_datasource("csv10.1")
        ds.objects = self.generator.get_recipe("test10").objects
        ds.add("hosts", coshsh.host.Host({
            'host_name': 'drivelsrv', 'address': '11.120.9.10', 'type': 'Server', 'os': 'Red Hat 6.0', 'hardware': '', 'virtual': 'vs', 'notification_period': '7x24', 'location': '2nd floor', 'department': 'ps'
        }))
        ds.get("hosts", "drivelsrv").hostgroups.append("mysql")
        ds.add("applications", coshsh.application.Application({
            'name': 'drivel', 'type': 'mysql', 'component': '', 'version': '', 'patchlevel': '', 'host_name': 'drivelsrv', 'check_period': '7x24'
        }))
        ds.add("details", coshsh.monitoringdetail.MonitoringDetail({
            'host_name': 'drivelsrv',
            'name': 'drivel',
            'type': 'mysql',
            "monitoring_type" : "PORT",
            "monitoring_0" : 10000}))
        self.generator.get_recipe("test10").assemble()
        self.assertTrue(self.generator.get_recipe("test10").objects["hosts"]["drivelsrv"].hostgroups == ["mysql"])
        self.assertTrue(len(self.generator.get_recipe("test10").objects["hosts"]["drivelsrv"].hostgroups) == 1)

    def test_hostgroup_by_app(self):
        self.setUpConfig("etc/coshsh.cfg", "test10")
        ds = self.generator.get_recipe("test10").get_datasource("csv10.1")
        ds.objects = self.generator.get_recipe("test10").objects
        ds.add("hosts", coshsh.host.Host({
            'host_name': 'drivelsrv-clustera', 'address': '11.120.9.10', 'type': 'Server', 'os': 'Red Hat 6.0', 'hardware': '', 'virtual': 'vs', 'notification_period': '7x24', 'location': '2nd floor', 'department': 'ps'
        }))
        ds.get("hosts", "drivelsrv-clustera").hostgroups.append("mysql")
        ds.add("applications", coshsh.application.Application({
            'name': 'drivel', 'type': 'mysql', 'component': '', 'version': '', 'patchlevel': '', 'host_name': 'drivelsrv-clustera', 'check_period': '7x24'
        }))
        ds.add("details", coshsh.monitoringdetail.MonitoringDetail({
            'host_name': 'drivelsrv-clustera',
            'name': 'drivel',
            'type': 'mysql',
            "monitoring_type" : "PORT",
            "monitoring_0" : 10000}))
        self.generator.get_recipe("test10").assemble()
        self.assertTrue("mysql" in self.generator.get_recipe("test10").objects["hosts"]["drivelsrv-clustera"].hostgroups)
        self.assertTrue("mysql-clusters" in self.generator.get_recipe("test10").objects["hosts"]["drivelsrv-clustera"].hostgroups)
        self.assertTrue(len(self.generator.get_recipe("test10").objects["hosts"]["drivelsrv-clustera"].hostgroups) == 2)


if __name__ == '__main__':
    unittest.main()


