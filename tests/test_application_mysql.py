import unittest
import sys
import os
import logging

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.abspath(".."))
#sys.path.insert(0, os.path.abspath(os.path.join("..", "coshsh")))

import coshsh
from coshsh.generator import Generator
#from datasource import Datasource
from coshsh.host import Host
from coshsh.application import Application
from coshsh.monitoringdetail import MonitoringDetail
from coshsh.util import setup_logging

logger = logging.getLogger('coshsh')

class CoshshTest(unittest.TestCase):
    def setUp(self):
        self.generator = Generator()
        # otherwise there is an "unclosed file" warning, because logging
        # was not used
        #setup_logging()
        self.hosts = {}
        self.applications = {}
        coshsh.application.Application.init_classes([
            os.path.join(os.path.dirname(__file__), '../recipes/default/classes'),
            os.path.join(os.path.dirname(__file__), 'recipes/test10/classes')])
        MonitoringDetail.init_classes([
            os.path.join(os.path.dirname(__file__), '../recipes/default/classes'),
            os.path.join(os.path.dirname(__file__), 'recipes/test10/classes')])
        pass
        row = ['drivelsrv', '11.120.9.10', 'Server', 'Red Hat 6.0', '', 'vs', '7x24', '2nd floor', 'ps']
        final_row = { }
        for (index, value) in enumerate(['host_name', 'address', 'type', 'os', 'hardware', 'virtual', 'notification_period', 'location', 'department']):
            final_row[value] = [None if row[index] == "" else row[index]][0]
        h = coshsh.host.Host(final_row)
        self.hosts[h.host_name] = h

        row = ['drivel', 'mysql', '', '', '', 'drivelsrv', '7x24']
        final_row = { }
        for (index, value) in enumerate(['name', 'type', 'component', 'version', 'patchlevel', 'host_name', 'check_period']):
            final_row[value] = [None if row[index] == "" else row[index]][0]
        a = coshsh.application.Application(final_row)
        #a.__init__(final_row)
        self.applications[a.fingerprint()] = a
        setattr(a, "host", self.hosts[a.host_name])

    def test_create_server(self):
        self.assertTrue("drivelsrv" in self.hosts)
        h = self.hosts["drivelsrv"]
        a = self.applications["drivelsrv+drivel+mysql"]
        self.assertTrue(hasattr(h, 'host_name'))
        self.assertTrue(h.host_name == 'drivelsrv')
        self.assertTrue(hasattr(a, 'host_name'))
        self.assertTrue(a.host_name == 'drivelsrv')
        self.assertTrue(hasattr(a, "port"))
        self.assertTrue(a.port == 3306)


    def test_create_server_alternative_port(self):
        self.assertTrue("drivelsrv" in self.hosts)
        h = self.hosts["drivelsrv"]
        a = self.applications["drivelsrv+drivel+mysql"]
        self.assertTrue(hasattr(h, 'host_name'))
        self.assertTrue(h.host_name == 'drivelsrv')
        self.assertTrue(hasattr(a, 'host_name'))
        self.assertTrue(a.host_name == 'drivelsrv')
        a.monitoring_details.append(coshsh.monitoringdetail.MonitoringDetail({
            "monitoring_type" : "PORT",
            "monitoring_0" : 10000}))
        a.resolve_monitoring_details()
        self.assertTrue(a.port == 10000)


if __name__ == '__main__':
    unittest.main()


