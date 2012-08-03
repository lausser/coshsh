import unittest
import sys

sys.path.append("..")
sys.path.append("../shintarator")

from host import Host
from application import Application
from monitoring_detail import MonitoringDetail

class GeneratorTest(unittest.TestCase):
    def setUp(self):
        self.hosts = {}
        self.applications = {}
        pass
        row = ['nagioscop001', '10.130.9.10', 'Server', 'Red Hat 6.0', '', 'vs', '7x24', 'cl-itm003', 'Dir-III']
        final_row = { }
        for (index, value) in enumerate(['host_name', 'address', 'type', 'os', 'hardware', 'virtual', 'notification_period', 'location', 'department']):
            final_row[value] = [None if row[index] == "" else row[index]][0]
        h = Host(final_row)
        self.hosts[h.host_name] = h

        row = ['gms1', 'gearman-server', '', '', '', 'nagioscop001', '7x24']
        final_row = { }
        for (index, value) in enumerate(['name', 'type', 'component', 'version', 'patchlevel', 'host_name', 'check_period']):
            final_row[value] = [None if row[index] == "" else row[index]][0]
        a = Application(final_row)
        #a.__init__(final_row)
        print "my fingerprint is", a.fingerprint()
        self.applications[a.fingerprint()] = a
        setattr(a, "host", self.hosts[a.host_name])

    def test_create_server(self):
        self.assert_("nagioscop001" in self.hosts)
        h = self.hosts["nagioscop001"]
        a = self.applications["nagioscop001+gms1+gearman-server"]
        self.assert_(hasattr(h, 'host_name'))
        self.assert_(h.host_name == 'nagioscop001')
        self.assert_(hasattr(a, 'host_name'))
        self.assert_(a.host_name == 'nagioscop001')
        self.assert_(hasattr(a, "port"))
        self.assert_(a.port == '4730')


    def test_create_server_alternative_port(self):
        self.assert_("nagioscop001" in self.hosts)
        h = self.hosts["nagioscop001"]
        a = self.applications["nagioscop001+gms1+gearman-server"]
        self.assert_(hasattr(h, 'host_name'))
        self.assert_(h.host_name == 'nagioscop001')
        self.assert_(hasattr(a, 'host_name'))
        self.assert_(a.host_name == 'nagioscop001')
        a.monitoring_details.append(MonitoringDetail({
            "monitoring_type" : "PORT",
            "value" : "10000"}))
        a.resolve_monitoring_details()
        self.assert_(a.port == '10000')


if __name__ == '__main__':
    unittest.main()


