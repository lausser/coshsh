#-*- coding: utf-8 -*-
import unittest
import os
import io
import sys
import shutil
from optparse import OptionParser
from configparser import RawConfigParser
import logging
import pprint
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import coshsh
from coshsh.generator import Generator
from coshsh.datasource import Datasource
from coshsh.datarecipient import Datarecipient
from coshsh.host import Host
from coshsh.application import Application
from coshsh.util import setup_logging
from tests.common_coshsh_test import CommonCoshshTest

sys.dont_write_bytecode = True

class CoshshTest(CommonCoshshTest):
    _configfile = 'etc/coshsh.cfg'
    _objectsdir = ["./var/objects/test1", "./var/objects/test12"]

    def print_header(self):
        print("#" * 80 + "\n" + "#" + " " * 78 + "#")
        print("#" + str.center(self.id(), 78) + "#")
        print("#" + " " * 78 + "#\n" + "#" * 80 + "\n")

    def setUps(self):
        shutil.rmtree("./var/objects/test12", True)
        os.makedirs("./var/objects/test12")
        shutil.rmtree("./var/objects/test1", True)
        os.makedirs("./var/objects/test1")
        self.config = RawConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = coshsh.generator.Generator()
        setup_logging()
        self.pp = pprint.PrettyPrinter(indent=4)

    def tearDowns(self):
        shutil.rmtree("./var/objects/test12", True)
        shutil.rmtree("./var/objects/test1", True)
        print()

    def test_create_recipe_hand_down(self):
        attributes_for_adapters = ["name", "force", "safe_output", "pid_dir", "pid_file", "templates_dir", "classes_dir", "max_delta", "classes_path", "templates_path", "filter", "objects_dir"]
        self.print_header()
        self.generator.add_recipe(name='test12', **dict(self.config.items('recipe_TEST12')))

        self.config.set("datasource_CSV10.1", "name", "csv1")
        self.config.set("datasource_CSV10.2", "name", "csv2")
        self.config.set("datasource_CSV10.3", "name", "csv3")
        cfg = self.config.items("datasource_CSV10.1")
        self.generator.recipes['test12'].add_datasource(**dict(cfg))
        cfg = self.config.items("datasource_CSV10.2")
        self.generator.recipes['test12'].add_datasource(**dict(cfg))
        cfg = self.config.items("datasource_CSV10.3")
        self.generator.recipes['test12'].add_datasource(**dict(cfg))

        self.config.set("datarecipient_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datarecipient_SIMPLESAMPLE")
        self.generator.recipes['test12'].add_datarecipient(**dict(cfg))

        self.config.set("datarecipient_SIMPLESAMPLE2", "name", "simplesample2")
        cfg = self.config.items("datarecipient_SIMPLESAMPLE2")
        self.generator.recipes['test12'].add_datarecipient(**dict(cfg))

        self.config.set("datarecipient_DEFAULT", "name", "default")
        cfg = self.config.items("datarecipient_DEFAULT")
        self.generator.recipes['test12'].add_datarecipient(**dict(cfg))

        dr_simplesample = [dr for dr in self.generator.recipes['test12'].datarecipients if dr.name == 'simplesample'][0]
        self.assertTrue(dr_simplesample.objects_dir == "/tmp")
        self.assertTrue(dr_simplesample.recipe_objects_dir == self.generator.recipes['test12'].objects_dir)
        dr_simplesample2 = [dr for dr in self.generator.recipes['test12'].datarecipients if dr.name == 'simplesample2'][0]
        self.assertTrue(dr_simplesample2.objects_dir == "./var/objects/test1")
        self.assertTrue(dr_simplesample2.recipe_objects_dir == self.generator.recipes['test12'].objects_dir)
        dr_default = [dr for dr in self.generator.recipes['test12'].datarecipients if dr.name == 'default'][0]
        self.assertTrue(dr_default.objects_dir == "./var/objects/test12")
        self.assertTrue(dr_default.recipe_objects_dir == self.generator.recipes['test12'].objects_dir)

        self.generator.recipes['test12'].collect()
        self.generator.recipes['test12'].assemble()
        self.generator.recipes['test12'].render()
        self.generator.recipes['test12'].output()
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
        attributes_for_adapters = ["name", "force", "safe_output", "pid_dir", "pid_file", "templates_dir", "classes_dir", "max_delta", "classes_path", "templates_path", "filter", "objects_dir"]
        self.print_header()
        self.generator.add_recipe(name='test12a', **dict(self.config.items('recipe_TEST12a')))

        self.config.set("datasource_CSV10.1", "name", "csv1")
        self.config.set("datasource_CSV10.2", "name", "csv2")
        self.config.set("datasource_CSV10.3", "name", "csv3")
        cfg = self.config.items("datasource_CSV10.1")
        self.generator.recipes['test12a'].add_datasource(**dict(cfg))
        cfg = self.config.items("datasource_CSV10.2")
        self.generator.recipes['test12a'].add_datasource(**dict(cfg))
        cfg = self.config.items("datasource_CSV10.3")
        self.generator.recipes['test12a'].add_datasource(**dict(cfg))

        self.config.set("datarecipient_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datarecipient_SIMPLESAMPLE")
        self.generator.recipes['test12a'].add_datarecipient(**dict(cfg))

        self.config.set("datarecipient_SIMPLESAMPLE2", "name", "simplesample2")
        cfg = self.config.items("datarecipient_SIMPLESAMPLE2")
        self.generator.recipes['test12a'].add_datarecipient(**dict(cfg))

        dr_simplesample = [dr for dr in self.generator.recipes['test12a'].datarecipients if dr.name == 'simplesample'][0]
        self.assertTrue(dr_simplesample.objects_dir == "/tmp")
        self.assertTrue(dr_simplesample.recipe_objects_dir == self.generator.recipes['test12a'].objects_dir)
        dr_simplesample2 = [dr for dr in self.generator.recipes['test12a'].datarecipients if dr.name == 'simplesample2'][0]
        self.assertTrue(dr_simplesample2.objects_dir == "./var/objects/test1")
        self.assertTrue(dr_simplesample2.recipe_objects_dir == self.generator.recipes['test12a'].objects_dir)
        dr_default = [dr for dr in self.generator.recipes['test12a'].datarecipients if dr.name == 'datarecipient_coshsh_default'][0]
        self.assertTrue(dr_default.objects_dir == "./var/objects/test12")
        self.assertTrue(dr_default.recipe_objects_dir == self.generator.recipes['test12a'].objects_dir)

        self.generator.recipes['test12a'].collect()
        self.generator.recipes['test12a'].assemble()
        self.generator.recipes['test12a'].render()
        self.generator.recipes['test12a'].output()
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
        self.print_header()
        bash_breaker = u"*(;!&haha,friss!das!du!blöde!shell!"
        bash_breaker_encoded = 'rfc3986://' + urllib.request.pathname2url(bash_breaker.encode('utf-8'))
        self.generator.add_recipe(name='oracleds2tpl', **dict(self.config.items('recipe_ORACLEDS2TPL')))
        self.config.set("datasource_CSV10.1", "name", "csv1")
        cfg = self.config.items("datasource_CSV10.1")
        self.generator.recipes['oracleds2tpl'].add_datasource(**dict(cfg))
        setattr(self.generator.recipes['oracleds2tpl'].datasources[0], "sid", "ORCL1234")
        setattr(self.generator.recipes['oracleds2tpl'].datasources[0], "username", "zosch")
        setattr(self.generator.recipes['oracleds2tpl'].datasources[0], "password", bash_breaker)

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
        self.generator.recipes['oracleds2tpl'].collect()
        self.generator.recipes['oracleds2tpl'].datasources[0].add('hosts', host)
        self.generator.recipes['oracleds2tpl'].datasources[0].add('applications', app)
        self.generator.recipes['oracleds2tpl'].assemble()
        self.generator.recipes['oracleds2tpl'].render()
        self.assertTrue(len(self.generator.recipes['oracleds2tpl'].objects['applications']) == 3)
        self.generator.recipes['oracleds2tpl'].output()
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/testhost/app_oraappindsdb_default.cfg"))
        with io.open("var/objects/test1/dynamic/hosts/testhost/app_oraappindsdb_default.cfg") as f:
            app_oraappindsdb_default_cfg = f.read()
        self.assertTrue("!"+bash_breaker_encoded+" --sql" in app_oraappindsdb_default_cfg)

if __name__ == '__main__':
    unittest.main()

