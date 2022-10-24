import os
import shutil
import coshsh
from coshsh.host import Host
from coshsh.application import Application
from coshsh.monitoringdetail import MonitoringDetail
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def test_mygeneric_app(self):
        shutil.rmtree("/tmp/coshsh_test34.log", True)
        self.setUpConfig("etc/coshsh5.cfg", "test34")
        # init-meldungen von test34
        self.assertTrue(os.path.exists("/tmp/coshsh_test34.log"))
        r = self.generator.get_recipe("test34")
        r.update_item_class_factories()
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
        ds.add('details', MonitoringDetail({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',
            'monitoring_type': 'BLINKENLIGHT',
            'monitoring_0': 'red',
        }))
        r.collect()
        r.assemble()
        r.render()
        self.assertTrue(len(r.objects['applications']) == 1)
        self.assertTrue(r.datasources[0].getall('applications')[0] == app)
        self.assertTrue(r.datasources[0].getall('applications')[0].__class__.__name__ == "MyGenericApplication")
        r.output()
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hosts/testhost/host.cfg"))
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_fs.cfg"))
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_ports.cfg"))
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_blinkenlights.cfg"))


