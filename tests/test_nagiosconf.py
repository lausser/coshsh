"""Tests for NAGIOSCONF MonitoringDetail injection into service and host config files."""
import os
import io
from coshsh.monitoringdetail import MonitoringDetail
from tests.common_coshsh_test import CommonCoshshTest


class NagiosconfTest(CommonCoshshTest):

    def tearDown(self):
        pass

    def test_nagiosconf(self):
        """Verify NAGIOSCONF detail values appear correctly in rendered service and host config files."""
        self.setUpConfig("etc/coshsh.cfg", "test10")
        r = self.generator.get_recipe("test10")
        r.count_before_objects()
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        ds = self.generator.get_recipe("test10").get_datasource("csv10.1")
        ds.objects = r.objects
        win = [app for app in r.objects['applications'].values() if "windows" in app.__class__.__name__.lower()][0]
        sci = MonitoringDetail({
            'host_name': win.host_name,
            'name': win.name,
            'type': win.type,
            'monitoring_type': 'NAGIOSCONF',
            'monitoring_0': 'os_windows_default_check_nsclient',
            'monitoring_1': 'check_interval',
            'monitoring_2': '4711',
        })
        ds.add('details', sci)
        host = [h for h in r.objects['hosts'].values() if h.host_name == win.host_name][0]
        hci = MonitoringDetail({
            'host_name': host.host_name,
            'name': None,
            'type': None,
            'monitoring_type': 'NAGIOSCONF',
            'monitoring_1': 'check_interval',
            'monitoring_2': '0815',
        })
        ds.add('details', hci)
        r.assemble()
        r.render()
        self.assertTrue(hasattr(self.generator.recipes['test10'].objects['hosts']['test_host_0'], 'config_files'))
        self.assertIn('host.cfg', self.generator.recipes['test10'].objects['hosts']['test_host_0'].config_files['nagios'])

        r.output()
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg"))
        with io.open("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertIn('os_windows_default_check_nsclient', os_windows_default_cfg)
        self.assertIn('os_windows_default_check_nsclient_test_host_1', os_windows_default_cfg)
        self.assertIn('4711', os_windows_default_cfg)
        with io.open("var/objects/test10/dynamic/hosts/test_host_1/host.cfg") as f:
            host_cfg = f.read()
        self.assertIn('test_host_1_coshsh', host_cfg)
        self.assertIn('0815', host_cfg)
