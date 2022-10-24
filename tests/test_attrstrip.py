import os
import coshsh
from coshsh.host import Host
from coshsh.application import Application
from coshsh.monitoringdetail import MonitoringDetail
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def test_generic_app(self):
        self.setUpConfig("etc/coshsh5.cfg", "test33")
        r = self.generator.get_recipe("test33")
        r.update_item_class_factories()
        self.generator.cookbook.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.generator.cookbook.items("datasource_SIMPLESAMPLE")
        r.add_datasource(**dict(cfg))
        ds = r.get_datasource("simplesample")
        ds.objects = r.objects
        host = Host({
            'host_name': 'testhost',
            'address': '127.0.0.1',
        })
        ds.add('hosts', host)
        app1 = Application({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'appwithblanks',
            'prefix': '    prefix ',
            'suffix': '    suffix ',
            'swisscheese': ' gruezi i am a swiss cheese ',
        })
        app2 = Application({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'appwithblanksbool',
            'prefix': '    prefix ',
            'suffix': '    suffix ',
            'swisscheese': ' gruezi i am a swiss cheese ',
        })
        app3 = Application({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'appwithblankslist',
            'prefix': '    prefix ',
            'suffix': '    suffix ',
            'swisscheese': ' gruezi i am a swiss cheese ',
        })
        ds.add('applications', app1)
        ds.add('applications', app2)
        ds.add('applications', app3)
        r.collect()
        r.assemble()
        r.render()
        self.assertTrue(len(r.objects['applications']) == 3)
        self.assertTrue(list(ds.getall('applications'))[0] == app1)
        self.assertTrue(list(ds.getall('applications'))[0].__class__.__name__ == "AppWithBlanks")
        self.assertTrue(list(self.generator.recipes['test33'].datasources[0].getall('applications'))[1].__class__.__name__ == "AppWithBlanksBool")
        self.assertTrue(list(self.generator.recipes['test33'].datasources[0].getall('applications'))[2].__class__.__name__ == "AppWithBlanksList")
        self.assertTrue(app1.prefix == "prefix")
        self.assertTrue(app1.suffix == "suffix")
        self.assertTrue(app1.swisscheese == "gruezi i am a swiss cheese")
        self.assertTrue(app2.prefix == "    prefix ")
        self.assertTrue(app2.suffix == "    suffix ")
        self.assertTrue(app2.swisscheese == " gruezi i am a swiss cheese ")
        self.assertTrue(app3.prefix == "    prefix ")
        self.assertTrue(app3.suffix == "    suffix ")
        self.assertTrue(app3.swisscheese == "gruezi i am a swiss cheese")

