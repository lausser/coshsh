import os
import io
from coshsh.host import Host
from coshsh.application import Application, GenericApplication
from coshsh.monitoringdetail import MonitoringDetail
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def test_generic_app(self):
        self.setUpConfig("etc/coshsh5.cfg", "test33")
        r = self.generator.get_recipe("test33")
        ds = self.generator.get_recipe("test33").get_datasource("simplesample")
        ds.objects = r.objects
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
        app = Application({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',
        })
        ds.add('applications', app)
        r.collect()
        r.assemble()
        r.render()
        self.assertTrue(len(r.objects['applications']) == 1)
        self.assertTrue(list(ds.getall('applications'))[0] == app)
        self.assertTrue(list(ds.getall('applications'))[0].__class__ == GenericApplication)
        r.output()
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hosts/testhost/host.cfg"))
        with io.open("var/objects/test33/dynamic/hosts/testhost/host.cfg") as f:
            testhost_cfg = f.read()
            print(testhost_cfg)
        self.assertTrue(not os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_fs.cfg"))
        self.assertTrue(not os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_ports.cfg"))

    def test_mygeneric_app(self):
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
        self.assertTrue(len(r.objects['applications']) == 1)
        self.assertTrue(ds.getall('applications')[0] == app)
        self.assertTrue(ds.getall('applications')[0].__class__.__name__ == "MyGenericApplication")
        r.output()
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hosts/testhost/host.cfg"))
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_fs.cfg"))
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_ports.cfg"))

