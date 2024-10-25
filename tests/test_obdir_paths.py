import os
import io
from coshsh.host import Host
from coshsh.application import Application, GenericApplication
from coshsh.monitoringdetail import MonitoringDetail
from tests.common_coshsh_test import CommonCoshshTest


# i test .../dynamic/hostgroups/...
# hostgroup names with "/" should be stripped.


class CoshshTest(CommonCoshshTest):
    _configfile = 'etc/coshsh5.cfg'
    _objectsdir = "./var/objects/test33"

    def tearDown(self):
        pass

    def test_generic_app(self):
        self.setUpConfig("etc/coshsh5.cfg", "test33")
        r = self.generator.get_recipe("test33")
        ds = self.generator.get_recipe("test33").get_datasource("simplesample")
        ds.objects = r.objects
        host = Host({
            'host_name': 'testhost',
            'address': '127.0.0.1',
        })
        ds.add('hosts', host)
        host.hostgroups.append("servers")
        host.hostgroups.append("08/15")
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
        self.assertTrue(ds.getall('applications')[0] == app)
        self.assertTrue(ds.getall('applications')[0].__class__ == GenericApplication)
        r.output()
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hosts/testhost/host.cfg"))
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hostgroups/hostgroup_servers.cfg"))
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hostgroups/hostgroup_08_15_5641.cfg"))
        with io.open("var/objects/test33/dynamic/hostgroups/hostgroup_servers.cfg") as f:
            hg = f.read()
        self.assertTrue('servers' in hg)
        with io.open("var/objects/test33/dynamic/hostgroups/hostgroup_08_15_5641.cfg") as f:
            hg = f.read()
        self.assertTrue('08/15' in hg)
        self.assertFalse('08_15' in hg)
        self.assertTrue(not os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_fs.cfg"))
        self.assertTrue(not os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_ports.cfg"))

