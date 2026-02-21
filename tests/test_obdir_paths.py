"""Tests for output directory hostgroup path sanitisation (slash-in-name stripping)."""
import os
import io
from coshsh.host import Host
from coshsh.application import Application, GenericApplication
from coshsh.monitoringdetail import MonitoringDetail
from tests.common_coshsh_test import CommonCoshshTest


class ObdirPathsTest(CommonCoshshTest):
    _configfile = 'etc/coshsh5.cfg'
    _objectsdir = './var/objects/test33'

    def tearDown(self):
        pass

    def test_generic_app(self):
        """Verify hostgroup filenames with slashes are sanitised and content still contains the original name."""
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
        self.assertEqual(len(r.objects['applications']), 1)
        self.assertEqual(ds.getall('applications')[0], app)
        self.assertEqual(ds.getall('applications')[0].__class__, GenericApplication)
        r.output()
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hosts/testhost/host.cfg"))
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hostgroups/hostgroup_servers.cfg"))
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hostgroups/hostgroup_08_15_5641.cfg"))
        with io.open("var/objects/test33/dynamic/hostgroups/hostgroup_servers.cfg") as f:
            hg = f.read()
        self.assertIn('servers', hg)
        with io.open("var/objects/test33/dynamic/hostgroups/hostgroup_08_15_5641.cfg") as f:
            hg = f.read()
        self.assertIn('08/15', hg)
        self.assertFalse('08_15' in hg)
        self.assertFalse(os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_fs.cfg"))
        self.assertFalse(os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_ports.cfg"))
