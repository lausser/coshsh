import unittest
import os
import sys
import shutil
import string
from optparse import OptionParser
import ConfigParser
from logging import INFO, DEBUG


sys.dont_write_bytecode = True
sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath(os.path.join("..", "coshsh")))

from log import logger
from generator import Generator
from datasource import Datasource
from application import Application
from monitoring_detail import MonitoringDetail


class CoshshTest(unittest.TestCase):
    def print_header(self):
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def setUp(self):
        logger.handlers[1].setLevel(DEBUG)
        os.makedirs("./var/objects/test6")
        self.config = ConfigParser.ConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = Generator()

    def tearDown(self):
        shutil.rmtree("./var/objects/test6", True)
        print 

    def test_detail_keyvalues(self):
        self.print_header()
        self.generator.add_recipe(name='test6', **dict(self.config.items('recipe_TEST6')))
        self.config.set("datasource_CSVDETAILS", "name", "test6")
        cfg = self.config.items("datasource_CSVDETAILS")
        ds = Datasource(**dict(cfg))
        hosts, applications, contacts, contactgroups, appdetails, dependencies, bps = ds.read()
        applications[0].resolve_monitoring_details()
        applications[1].resolve_monitoring_details()
        # swap threshold via KEYVALUES detail
        self.assert_(applications[0].swap_warning == "15%")
        self.assert_(applications[0].swap_critical == "8%")
        # cron threshold via KEYVALUES detail
        self.assert_(applications[0].cron_warning == "30")
        self.assert_(applications[0].cron_critical == "100")
        # swap threshold via class os_linux
        self.assert_(applications[1].swap_warning == "5%")
        self.assert_(applications[1].swap_critical == "15%")
        # neither class detail nor csv detail
        self.assert_(not hasattr(applications[1], "cron_warning"))
        self.assert_(hasattr(applications[1], "thresholds"))
        self.assert_(hasattr(applications[1].thresholds, "cron_warning"))
        self.assert_(applications[1].thresholds.cron_warning == "31")

    def test_detail_url(self):
        self.print_header()
        oracle = Application({'name': 'test', 'type': 'generic'})
        url = MonitoringDetail({'application_name': 'test',
            'application_type': 'generic',
            'monitoring_type': 'URL',
            'monitoring_0': 'oracle://dbadm:pass@dbsrv:1522/svc',
        })
        oracle.monitoring_details.append(url)
        oracle.resolve_monitoring_details()
        self.assert_(len(oracle.urls) == 1)
        # consol app_db_oracle class will call wemustrepeat() to create
        # a fake LOGIN-detail, so there is a oracle.username
        self.assert_(oracle.urls[0].username == 'dbadm')
        self.assert_(oracle.urls[0].password == 'pass')
        self.assert_(oracle.urls[0].hostname == 'dbsrv')
        self.assert_(oracle.urls[0].port == 1522)
        # will be without the / in the consol app_db_oracle class
        self.assert_(oracle.urls[0].path == '/svc')

    def test_detail_ram(self):
        Application.init_classes([
            os.path.join(os.path.dirname(__file__), 'recipes/test6/classes'),
            os.path.join(os.path.dirname(__file__), '../recipes/default/classes')])
        MonitoringDetail.init_classes([
            os.path.join(os.path.dirname(__file__), 'recipes/test6/classes'),
            os.path.join(os.path.dirname(__file__), '../recipes/default/classes')])
        self.print_header()
        opsys = Application({'name': 'os', 'type': 'red hat 6.1'})
        ram = MonitoringDetail({'application_name': 'os',
            'application_type': 'red hat 6.1',
            'monitoring_type': 'RAM',
            'monitoring_0': '80',
            'monitoring_1': '90',
        })
        opsys.monitoring_details.append(ram)
        for m in opsys.monitoring_details:
            print "detail", m
        opsys.resolve_monitoring_details()
        self.assert_(hasattr(opsys, 'ram'))
        self.assert_(opsys.ram.warning == '80')

if __name__ == '__main__':
    unittest.main()


