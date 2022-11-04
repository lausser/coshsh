import os
import io
import urllib
from coshsh.host import Host
from coshsh.application import Application
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def test_create_recipe_hand_down(self):
        self.setUpConfig("etc/coshsh.cfg", "test12")
        r = self.generator.get_recipe("test12")
        attributes_for_adapters = ["name", "force", "safe_output", "pid_dir", "pid_file", "templates_dir", "classes_dir", "max_delta", "classes_path", "templates_path", "filter", "objects_dir"]
        
        dr_simplesample = r.get_datarecipient('simplesample')
        self.assertTrue(dr_simplesample.objects_dir == "/tmp")
        self.assertTrue(dr_simplesample.recipe_objects_dir == r.objects_dir)
        dr_simplesample2 = r.get_datarecipient('simplesample2')
        self.assertTrue(dr_simplesample2.objects_dir == "./var/objects/test1")
        self.assertTrue(dr_simplesample2.recipe_objects_dir == r.objects_dir)
        dr_default = r.get_datarecipient('default')
        self.assertTrue(dr_default.objects_dir == "./var/objects/test12")
        self.assertTrue(dr_default.recipe_objects_dir == r.objects_dir)

        r.collect()
        r.assemble()
        r.render()
        r.output()
        # written by datarecipient_coshsh_default
        self.assertTrue(os.path.exists("var/objects/test12/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test12/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test12/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test12/dynamic/hosts/test_host_1/os_windows_default.cfg"))
        with io.open("var/objects/test12/dynamic/hosts/test_host_1/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue('os_windows_default_check_unittest' in os_windows_default_cfg)
        # written by simplesample2 which has it's own objects_dir
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_1/os_windows_default.cfg"))

    def test_create_recipe_hand_down_implicit_default_dr(self):
        self.setUpConfig("etc/coshsh.cfg", "test12a")
        r = self.generator.get_recipe("test12a")
        ds1 = r.get_datasource('csv10.1')
        ds2 = r.get_datasource('csv10.2')
        ds3 = r.get_datasource('csv10.3')
        ds1.objects = r.objects
        ds2.objects = r.objects
        ds3.objects = r.objects
        attributes_for_adapters = ["name", "force", "safe_output", "pid_dir", "pid_file", "templates_dir", "classes_dir", "max_delta", "classes_path", "templates_path", "filter", "objects_dir"]

        dr_simplesample = r.get_datarecipient("simplesample")
        self.assertTrue(dr_simplesample.objects_dir == "/tmp")
        self.assertTrue(dr_simplesample.recipe_objects_dir == self.generator.recipes['test12a'].objects_dir)
        dr_simplesample2 = r.get_datarecipient("simplesample2")
        self.assertTrue(dr_simplesample2.objects_dir == "./var/objects/test1")
        self.assertTrue(dr_simplesample2.recipe_objects_dir == self.generator.recipes['test12a'].objects_dir)
        dr_default = r.get_datarecipient("datarecipient_coshsh_default")
        self.assertTrue(dr_default.objects_dir == "./var/objects/test12")
        self.assertTrue(dr_default.recipe_objects_dir == self.generator.recipes['test12a'].objects_dir)

        r.collect()
        r.assemble()
        r.render()
        r.output()
        # written by datarecipient_coshsh_default
        self.assertTrue(os.path.exists("var/objects/test12/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test12/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test12/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test12/dynamic/hosts/test_host_1/os_windows_default.cfg"))
        with io.open("var/objects/test12/dynamic/hosts/test_host_1/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
            self.assertTrue('os_windows_default_check_unittest' in os_windows_default_cfg)
        # written by simplesample2 which has it's own objects_dir
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_1/os_windows_default.cfg"))

    def test_datasource_attributes_in_tpl(self):
        self.setUpConfig("etc/coshsh.cfg", "oracleds2tpl")
        r = self.generator.get_recipe("oracleds2tpl")
        ds = r.get_datasource('csv10.1')
        ds.objects = r.objects
        bash_breaker = u"*(;!&haha,friss!das!du!blöde!shell!"
        bash_breaker_encoded = 'rfc3986://' + urllib.request.pathname2url(bash_breaker.encode('utf-8'))
        setattr(ds, "sid", "ORCL1234")
        setattr(ds, "username", "zosch")
        setattr(ds, "password", bash_breaker)

        host = Host({
            'host_name': 'testhost',
            'address': '127.0.0.1',
            'alias': 'hosttest',
        })
        app = Application({
            'host_name': 'testhost',
            'name': 'eventhandlerdb',
            'type': 'oraappindsdb',
        })
        r.collect()
        ds.add('hosts', host)
        ds.add('applications', app)
        r.assemble()
        r.render()
        self.assertTrue(len(self.generator.recipes['oracleds2tpl'].objects['applications']) == 3)
        self.generator.recipes['oracleds2tpl'].output()
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/testhost/app_oraappindsdb_default.cfg"))
        with io.open("var/objects/test1/dynamic/hosts/testhost/app_oraappindsdb_default.cfg") as f:
            app_oraappindsdb_default_cfg = f.read()
        self.assertTrue("!"+bash_breaker_encoded+" --sql" in app_oraappindsdb_default_cfg)

