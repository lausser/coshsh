import unittest
import os
import sys
import shutil
import string
from optparse import OptionParser
import ConfigParser
import logging
from logging import INFO, DEBUG

logger = logging.getLogger('coshsh')

sys.dont_write_bytecode = True

import coshsh
from coshsh.generator import Generator
from coshsh.datasource import Datasource
from coshsh.application import Application
from coshsh.monitoringdetail import MonitoringDetail


class CoshshTest(unittest.TestCase):
    def print_header(self):
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def setUp(self):
        shutil.rmtree("./var/objects/test6", True)
        os.makedirs("./var/objects/test6")
        self.config = ConfigParser.ConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = coshsh.generator.Generator()
        self.generator.setup_logging(scrnloglevel=DEBUG)
        self.generator.add_recipe(name='test6', **dict(self.config.items('recipe_TEST6')))
        self.config.set("datasource_CSVDETAILS", "name", "test6")

    def tearDown(self):
        shutil.rmtree("./var/objects/test6", True)
        print 

    def test_detail_keyvalues(self):
        self.print_header()
        cfg = self.config.items("datasource_CSVDETAILS")
        self.generator.recipes['test6'].add_datasource(**dict(cfg))
        self.generator.recipes['test6'].collect()
        self.generator.recipes['test6'].assemble()
        objects = self.generator.recipes['test6'].objects
        app1 = objects['applications'].values()[0]
        app1.resolve_monitoring_details()
        app2 = objects['applications'].values()[1]
        app2.resolve_monitoring_details()
        # swap threshold via KEYVALUES detail
        self.assert_(app1.swap_warning == "15%")
        self.assert_(app1.swap_critical == "8%")
        # cron threshold via KEYVALUES detail
        self.assert_(app1.cron_warning == "30")
        self.assert_(app1.cron_critical == "100")
        # swap threshold via class os_linux
        self.assert_(app2.swap_warning == "5%")
        self.assert_(app2.swap_critical == "15%")
        # neither class detail nor csv detail
        self.assert_(not hasattr(app2, "cron_warning"))
        self.assert_(hasattr(app2, "thresholds"))
        self.assert_(hasattr(app2.thresholds, "cron_warning"))
        self.assert_(app2.thresholds.cron_warning == "31")

    def test_detail_url(self):
        self.print_header()
        oracle = coshsh.application.Application({
            'host_name': 'test',
            'name': 'test',
            'type': 'generic',
        })
        url = coshsh.monitoringdetail.MonitoringDetail({
            'host_name': 'test',
            'name': 'test',
            'type': 'generic',
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
        coshsh.application.Application.init_classes([
            os.path.join(os.path.dirname(__file__), 'recipes/test6/classes'),
            os.path.join(os.path.dirname(__file__), '../recipes/default/classes')])
        coshsh.monitoringdetail.MonitoringDetail.init_classes([
            os.path.join(os.path.dirname(__file__), 'recipes/test6/classes'),
            os.path.join(os.path.dirname(__file__), '../recipes/default/classes')])
        self.print_header()
        opsys = coshsh.application.Application({'name': 'os', 'type': 'red hat 6.1'})
        ram = coshsh.monitoringdetail.MonitoringDetail({'name': 'os',
            'type': 'red hat 6.1',
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

    def test_detail_2url(self):
        self.print_header()
        cfg = self.config.items("datasource_CSVDETAILS")
        objects = self.generator.recipes['test6'].objects
        ds = coshsh.datasource.Datasource(**dict(cfg))
        ds.read(objects=objects)



        #coshsh.application.Application.init_classes([
        #    os.path.join(os.path.dirname(__file__), 'recipes/test6/classes'),
        #    os.path.join(os.path.dirname(__file__), '../recipes/default/classes')])
        #coshsh.monitoringdetail.MonitoringDetail.init_classes([
        #    os.path.join(os.path.dirname(__file__), 'recipes/test6/classes'),
        #    os.path.join(os.path.dirname(__file__), '../recipes/default/classes')])
        opsys = coshsh.application.Application({'host_name': 'test_host_0', 'name': 'testapp', 'type': 'webapp'})
        url1 = coshsh.monitoringdetail.MonitoringDetail({
            'host_name': 'test_host_0',
            'name': 'testapp',
            'type': 'webapp',
            'monitoring_type': 'URL',
            'monitoring_0': 'https://uzi75.schoggimaschin.com:5480/login.html',
            'monitoring_1': '10',
            'monitoring_2': '15',
        })
        opsys.monitoring_details.append(url1)
        url2 = coshsh.monitoringdetail.MonitoringDetail({
            'host_name': 'test_host_0',
            'name': 'testapp',
            'type': 'webapp',
            'monitoring_type': 'URL',
            'monitoring_0': 'https://uzi75.schoggimaschin.com/vsphere-client/?csp',
            'monitoring_1': '10',
            'monitoring_2': '15',
        })
        opsys.monitoring_details.append(url2)
        ds.add('applications', opsys)
        for m in opsys.monitoring_details:
            print "detail", m
        opsys.resolve_monitoring_details()
        self.assert_(hasattr(opsys, 'urls'))
        for u in opsys.urls:
            print "url is", u, u.__dict__
        shutil.rmtree("./var/objects/test6", True)
        os.makedirs("./var/objects/test6/dynamic")
        self.generator.recipes['test6'].collect()
        self.generator.recipes['test6'].assemble()
        self.generator.recipes['test6'].render()
        self.generator.recipes['test6'].output()
        self.assert_(os.path.exists('var/objects/test6/dynamic/hosts/test_host_0/app_generic_web.cfg'))
        with open('var/objects/test6/dynamic/hosts/test_host_0/app_generic_web.cfg', 'r') as outfile:
            for line in outfile.read().split('\n'):
                print line

    def test_lazy_datasource(self):
        self.print_header()

        self.generator.add_recipe(name='test14', **dict(self.config.items('recipe_TEST14')))
        self.config.set("datasource_LAZY", "name", "test14")
        objects = self.generator.recipes['test14'].objects
        cfg = self.config.items("datasource_LAZY")
        ds = coshsh.datasource.Datasource(**dict(cfg))
        ds.read(objects=objects)

        shutil.rmtree("./var/objects/test14", True)
        os.makedirs("./var/objects/test14/dynamic")
        self.generator.recipes['test14'].collect()
        self.generator.recipes['test14'].assemble()
        self.generator.recipes['test14'].render()
        self.generator.recipes['test14'].output()
        app1 = objects['applications'].values()[0]
        self.assert_(hasattr(app1, 'huhu'))
        self.assert_(app1.huhu == 'dada')

if __name__ == '__main__':
    unittest.main()


