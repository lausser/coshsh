"""Tests for GenericApplication fallback and MyGenericApplication subtype selection."""

import os
from coshsh.host import Host
from coshsh.application import Application, GenericApplication
from coshsh.monitoringdetail import MonitoringDetail
from tests.common_coshsh_test import CommonCoshshTest


class GenericApplicationTest(CommonCoshshTest):
    _configfile = 'etc/coshsh5.cfg'
    _objectsdir = "./var/objects/test33"

    def test_generic_app(self):
        """Verify unknown application type falls back to GenericApplication without output files."""
        self.setUpConfig("etc/coshsh5.cfg", "test33")
        r = self.generator.get_recipe("test33")
        ds = self.generator.get_recipe("test33").get_datasource("simplesample")
        ds.objects = r.objects
        host = Host({
            'host_name': 'testhost',
            'address': '127.0.0.1',
        })
        ds.add('hosts', host)
        app = Application({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',
        })
        ds.add('applications', app)
        r.collect()
        r.assemble()
        r.render()
        self.assertEqual(len(r.objects['applications']), 1)
        self.assertEqual(ds.getall('applications')[0], app)
        self.assertEqual(ds.getall('applications')[0].__class__, GenericApplication)
        r.output()
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hosts/testhost/host.cfg"))
        self.assertFalse(os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_fs.cfg"))
        self.assertFalse(os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_ports.cfg"))

    def test_mygeneric_app(self):
        """Verify application with monitoring details is reblessed to MyGenericApplication with output files."""
        self.setUpConfig("etc/coshsh5.cfg", "test34")
        r = self.generator.get_recipe("test34")
        ds = self.generator.get_recipe("test34").get_datasource("simplesample")
        ds.objects = r.objects
        host = Host({
            'host_name': 'testhost',
            'address': '127.0.0.1',
        })
        ds.add('hosts', host)
        app = Application({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',
        })
        ds.add('applications', app)
        ds.add('details', MonitoringDetail({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',
            'monitoring_type': 'FILESYSTEM',
            'monitoring_0': '/',
            'monitoring_1': 90,
            'monitoring_2': 95,
        }))
        ds.add('details', MonitoringDetail({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',
            'monitoring_type': 'PORT',
            'monitoring_0': 80,
            'monitoring_1': 1,
            'monitoring_2': 5,
        }))
        r.collect()
        r.assemble()
        r.render()
        self.assertEqual(len(r.objects['applications']), 1)
        self.assertEqual(ds.getall('applications')[0], app)
        self.assertEqual(ds.getall('applications')[0].__class__.__name__, "MyGenericApplication")
        r.output()
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hosts/testhost/host.cfg"))
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_fs.cfg"))
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_ports.cfg"))
