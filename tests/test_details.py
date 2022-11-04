import os
import io
from coshsh.host import Host
from coshsh.application import Application
from coshsh.monitoringdetail import MonitoringDetail
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def test_detail_keyvalues(self):
        self.setUpConfig("etc/coshsh.cfg", "test6")
        r = self.generator.get_recipe("test6")
        ds = r.get_datasource("csvdetails")
        r.collect()
        r.assemble()
        objects = r.objects
        print(objects)
        app1 = list(objects['applications'].values())[0]
        app1.resolve_monitoring_details()
        app2 = list(objects['applications'].values())[1]
        app2.resolve_monitoring_details()
        # swap threshold via KEYVALUES detail
        self.assertTrue(app1.swap_warning == "15%")
        self.assertTrue(app1.swap_critical == "8%")
        # cron threshold via KEYVALUES detail
        self.assertTrue(app1.cron_warning == "30")
        self.assertTrue(app1.cron_critical == "100")
        # swap threshold via class os_linux
        self.assertTrue(app2.swap_warning == "5%")
        self.assertTrue(app2.swap_critical == "15%")
        # neither class detail nor csv detail
        self.assertTrue(not hasattr(app2, "cron_warning"))
        self.assertTrue(hasattr(app2, "thresholds"))
        self.assertTrue(hasattr(app2.thresholds, "cron_warning"))
        self.assertTrue(app2.thresholds.cron_warning == "31")

    def test_detail_keyvaluearrays(self):
        self.setUpConfig("etc/coshsh.cfg", "test6")
        r = self.generator.get_recipe("test6")
        ds = r.get_datasource("csvdetails")
        r.collect()
        r.assemble()
        objects = r.objects
        app1 = list(objects['applications'].values())[0]
        app1.resolve_monitoring_details()
        app2 = list(objects['applications'].values())[1]
        app2.resolve_monitoring_details()
        app2.resolve_monitoring_details()
        self.assertTrue(hasattr(app2, "roles"))
        self.assertTrue("dach" in app2.roles)
        self.assertTrue("prod" in app2.roles)
        self.assertTrue("dmz" in app2.roles)
        self.assertTrue("master" in app2.roles)
        self.assertTrue(hasattr(app2, "parents"))
        self.assertTrue("sw1" in app2.parents)
        self.assertTrue("sw2" in app2.parents)


    def test_detail_url(self):
        self.setUpConfig("etc/coshsh.cfg", "test6")
        r = self.generator.get_recipe("test6")
        oracle = Application({
            'host_name': 'test',
            'name': 'test',
            'type': 'generic',
        })
        url = MonitoringDetail({
            'host_name': 'test',
            'name': 'test',
            'type': 'generic',
            'monitoring_type': 'URL',
            'monitoring_0': 'oracle://dbadm:pass@dbsrv:1522/svc',
        })
        oracle.monitoring_details.append(url)
        oracle.resolve_monitoring_details()
        self.assertTrue(len(oracle.urls) == 1)
        # consol app_db_oracle class will call wemustrepeat() to create
        # a fake LOGIN-detail, so there is a oracle.username
        self.assertTrue(oracle.urls[0].username == 'dbadm')
        self.assertTrue(oracle.urls[0].password == 'pass')
        self.assertTrue(oracle.urls[0].hostname == 'dbsrv')
        self.assertTrue(oracle.urls[0].port == 1522)
        # will be without the / in the consol app_db_oracle class
        self.assertTrue(oracle.urls[0].path == '/svc')

    def test_detail_ram(self):
        self.setUpConfig("etc/coshsh.cfg", "test6")
        r = self.generator.get_recipe("test6")
        opsys = Application({'name': 'os', 'type': 'red hat 6.1'})
        ram = MonitoringDetail({'name': 'os',
            'type': 'red hat 6.1',
            'monitoring_type': 'RAM',
            'monitoring_0': '80',
            'monitoring_1': '90',
        })
        opsys.monitoring_details.append(ram)
        for m in opsys.monitoring_details:
            print("detail", m)
        opsys.resolve_monitoring_details()
        self.assertTrue(hasattr(opsys, 'ram'))
        self.assertTrue(opsys.ram.warning == '80')

    def test_detail_2url(self):
        self.setUpConfig("etc/coshsh.cfg", "test6")
        r = self.generator.get_recipe("test6")
        ds = r.get_datasource("csvdetails")
        ds.open()
        objects = r.objects
        ds.read(objects=objects)



        #coshsh.application.Application.init_classes([
        #    os.path.join(os.path.dirname(__file__), 'recipes/test6/classes'),
        #    os.path.join(os.path.dirname(__file__), '../recipes/default/classes')])
        #coshsh.monitoringdetail.MonitoringDetail.init_classes([
        #    os.path.join(os.path.dirname(__file__), 'recipes/test6/classes'),
        #    os.path.join(os.path.dirname(__file__), '../recipes/default/classes')])
        opsys = Application({'host_name': 'test_host_0', 'name': 'testapp', 'type': 'webapp'})
        url1 = MonitoringDetail({
            'host_name': 'test_host_0',
            'name': 'testapp',
            'type': 'webapp',
            'monitoring_type': 'URL',
            'monitoring_0': 'https://uzi75.schoggimaschin.com:5480/login.html',
            'monitoring_1': '10',
            'monitoring_2': '15',
        })
        opsys.monitoring_details.append(url1)
        url2 = MonitoringDetail({
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
            print("detail", m)
        opsys.resolve_monitoring_details()
        self.assertTrue(hasattr(opsys, 'urls'))
        for u in opsys.urls:
            print("url is", u, u.__dict__)
        os.makedirs("./var/objects/test6/dynamic")
        r.collect()
        r.assemble()
        r.render()
        r.output()
        self.assertTrue(os.path.exists('var/objects/test6/dynamic/hosts/test_host_0/app_generic_web.cfg'))
        with io.open('var/objects/test6/dynamic/hosts/test_host_0/app_generic_web.cfg', 'r') as outfile:
            for line in outfile.read().split('\n'):
                print(line)

    def test_lazy_datasource(self):
        self.setUpConfig("etc/coshsh.cfg", "test14")
        r = self.generator.get_recipe("test14")
        ds = r.get_datasource("lazy")
        self.print_header()
        objects = r.objects
        ds.read(objects=objects)
        r.collect()
        r.assemble()
        r.render()
        r.output()
        app1 = list(objects['applications'].values())[0]
        self.assertTrue(hasattr(app1, 'huhu'))
        self.assertTrue(app1.huhu == 'dada')

if __name__ == '__main__':
    unittest.main()


