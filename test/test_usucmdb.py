import unittest
import sys

sys.path.append("..")
sys.path.append("../shintarator")

#from host import Host
from datasource.valuemation import MyHost
from datasource.valuemation import MyApplication
from monitoring_detail import MonitoringDetail

class GeneratorTest(unittest.TestCase):
    def setUp(self):
        self.hosts = {}
        self.applications = {}
        pass
        row = ['nagioscop001', '10.130.9.10', 'Server', 'Red Hat 6.0', '', 'vs', '7x24', 'cl-itm003', 'Dir-III']
        final_row = { }
        for (index, value) in enumerate(MyHost.columns):
            final_row[value] = [None if row[index] == "" else row[index]][0]
        h = MyHost(final_row)
        self.hosts[h.host_name] = h

        row = ['os', 'os', '', 'RedHat6.0', '', 'nagioscop001', '7x24']
        final_row = { }
        for (index, value) in enumerate(MyApplication.columns):
            final_row[value] = [None if row[index] == "" else row[index]][0]
        a = MyApplication(final_row)
        application_id = "%s+%s+%s" % (a.host_name, a.name, a.type)
        self.applications[application_id] = a
        setattr(a, "host", self.hosts[a.host_name])

    def test_create(self):
        self.assert_("nagioscop001" in self.hosts)
        h = self.hosts["nagioscop001"]
        self.assert_(hasattr(h, 'host_name'))
        self.assert_(h.host_name == 'nagioscop001')
        print h
        print type(h.host_name)
        h.pythonize()
        print h.config_files()
        self.assert_(hasattr(h, 'address'))
        self.assert_(hasattr(h, 'type'))
        self.assert_(hasattr(h, 'os'))
        self.assert_(hasattr(h, 'hardware'))
        self.assert_(hasattr(h, 'virtual'))
        self.assert_(hasattr(h, 'notification_period'))
        self.assert_(hasattr(h, 'location'))
        self.assert_(hasattr(h, 'department'))


    def test_command(self):
        h = self.hosts["nagioscop001"]
        self.assert_(hasattr(h, 'host_name'))
        self.assert_(h.host_name == 'nagioscop001')
        h.monitoring_details.append(MonitoringDetail({
            "monitoring_type" : "NAGIOS",
            "value" : "check_command",
            "monitoring_1" : "ping_me!icmp"}))
        h.monitoring_details.append(MonitoringDetail({
            "monitoring_type" : "NAGIOS",
            "value" : "check_period",
            "monitoring_1" : "5x8"}))
        # baut neues template aus allen NAGIOS-Details
        # erweitert use:w!
        h.resolve_monitoring_details()
        self.assert_(hasattr(h, 'check_command') and h.check_command == "ping_me!icmp")
        self.assert_(hasattr(h, 'check_period') and h.check_period == "5x8")
        h.pythonize()
        print h.config_files()


    def test_linux(self):
        a = self.applications["nagioscop001+os+os"]
        self.assert_(a.__class__.__name__ == "Linux")
        a.monitoring_details.append(MonitoringDetail({
            "monitoring_type" : "FILESYSTEM",
            "value" : "/",
            "monitoring_1" : "10",
            "monitoring_2" : "5"}))
        a.monitoring_details.append(MonitoringDetail({
            "monitoring_type" : "FILESYSTEM",
            "value" : "/usr",
            "monitoring_1" : "20",
            "monitoring_2" : "15"}))
        a.monitoring_details.append(MonitoringDetail({
            "monitoring_type" : "FILESYSTEM",
            "value" : "/opt"}))
        a.resolve_monitoring_details()
        a.pythonize()


    def test_unknown_app(self):
        row = ['nix', 'nix', '', 'Nix 1.0', '', 'nagioscop001', '7x24']
        final_row = { }
        for (index, value) in enumerate(MyApplication.columns):
            final_row[value] = [None if row[index] == "" else row[index]][0]
        try:
            a = MyApplication(final_row)
            self.applications[a.fingerprint()] = a
        except:
            pass
        self.assert_("nagioscop001+nix+nix" not in self.applications)


if __name__ == '__main__':
    unittest.main()


