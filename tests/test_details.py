"""Tests for MonitoringDetail subtypes — KEYVALUES, KEYVALUEARRAYS, URL, RAM threshold parsing, and lazy datasource attribute merging."""

import os
import io
from coshsh.host import Host
from coshsh.application import Application
from coshsh.monitoringdetail import MonitoringDetail
from tests.common_coshsh_test import CommonCoshshTest


class MonitoringDetailTest(CommonCoshshTest):

    def test_detail_keyvalues(self):
        """KEYVALUES MonitoringDetail sets threshold attributes directly on the application."""
        self.setUpConfig("etc/coshsh.cfg", "test6")
        r = self.generator.get_recipe("test6")
        ds = r.get_datasource("csvdetails")
        r.collect()
        r.assemble()
        objects = r.objects
        app1 = list(objects['applications'].values())[0]
        app1.resolve_monitoring_details()
        app2 = list(objects['applications'].values())[1]
        app2.resolve_monitoring_details()
        self.assertEqual(app1.swap_warning, "15%")
        self.assertEqual(app1.swap_critical, "8%")
        self.assertEqual(app1.cron_warning, "30")
        self.assertEqual(app1.cron_critical, "100")
        self.assertEqual(app2.swap_warning, "5%")
        self.assertEqual(app2.swap_critical, "15%")
        self.assertFalse(hasattr(app2, "cron_warning"))
        self.assertTrue(hasattr(app2, "thresholds"))
        self.assertTrue(hasattr(app2.thresholds, "cron_warning"))
        self.assertEqual(app2.thresholds.cron_warning, "31")

    def test_detail_keyvaluearrays(self):
        """KEYVALUEARRAYS MonitoringDetail builds list attributes on the application."""
        self.setUpConfig("etc/coshsh.cfg", "test6")
        r = self.generator.get_recipe("test6")
        ds = r.get_datasource("csvdetails")
        r.collect()
        r.assemble()
        objects = r.objects
        app1 = list(objects['applications'].values())[0]
        app1.resolve_monitoring_details()
        app2 = list(objects['applications'].values())[1]
        app2.resolve_monitoring_details()
        app2.resolve_monitoring_details()
        self.assertTrue(hasattr(app2, "roles"))
        self.assertIn("dach", app2.roles)
        self.assertIn("prod", app2.roles)
        self.assertIn("dmz", app2.roles)
        self.assertIn("master", app2.roles)
        self.assertTrue(hasattr(app2, "parents"))
        self.assertIn("sw1", app2.parents)
        self.assertIn("sw2", app2.parents)

    def test_detail_url(self):
        """URL MonitoringDetail parses username, password, hostname, port, and path components."""
        self.setUpConfig("etc/coshsh.cfg", "test6")
        r = self.generator.get_recipe("test6")
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
        oracle.resolve_monitoring_details()
        self.assertEqual(len(oracle.urls), 1)
        self.assertEqual(oracle.urls[0].username, 'dbadm')
        self.assertEqual(oracle.urls[0].password, 'pass')
        self.assertEqual(oracle.urls[0].hostname, 'dbsrv')
        self.assertEqual(oracle.urls[0].port, 1522)
        self.assertEqual(oracle.urls[0].path, '/svc')

    def test_detail_ram(self):
        """RAM MonitoringDetail sets warning threshold attribute on the application."""
        self.setUpConfig("etc/coshsh.cfg", "test6")
        r = self.generator.get_recipe("test6")
        opsys = Application({'name': 'os', 'type': 'red hat 6.1'})
        ram = MonitoringDetail({'name': 'os',
            'type': 'red hat 6.1',
            'monitoring_type': 'RAM',
            'monitoring_0': '80',
            'monitoring_1': '90',
        })
        opsys.monitoring_details.append(ram)
        opsys.resolve_monitoring_details()
        self.assertTrue(hasattr(opsys, 'ram'))
        self.assertEqual(opsys.ram.warning, '80')

    def test_detail_2url(self):
        """Multiple URL MonitoringDetails produce multiple url entries and render to a config file."""
        self.setUpConfig("etc/coshsh.cfg", "test6")
        r = self.generator.get_recipe("test6")
        ds = r.get_datasource("csvdetails")
        ds.open()
        objects = r.objects
        ds.read(objects=objects)
        opsys = Application({'host_name': 'test_host_0', 'name': 'testapp', 'type': 'webapp'})
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
        ds.add('applications', opsys)
        opsys.resolve_monitoring_details()
        self.assertTrue(hasattr(opsys, 'urls'))
        os.makedirs("./var/objects/test6/dynamic")
        r.collect()
        r.assemble()
        r.render()
        r.output()
        self.assertTrue(os.path.exists('var/objects/test6/dynamic/hosts/test_host_0/app_generic_web.cfg'))

    def test_lazy_datasource(self):
        """Lazy datasource attributes are merged onto application objects during assemble."""
        self.setUpConfig("etc/coshsh.cfg", "test14")
        r = self.generator.get_recipe("test14")
        ds = r.get_datasource("lazy")
        self.print_header()
        objects = r.objects
        ds.read(objects=objects)
        r.collect()
        r.assemble()
        r.render()
        r.output()
        app1 = list(objects['applications'].values())[0]
        self.assertTrue(hasattr(app1, 'huhu'))
        self.assertEqual(app1.huhu, 'dada')
