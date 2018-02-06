import unittest
import os
import sys
import shutil
import string
from optparse import OptionParser
import ConfigParser
import logging


sys.dont_write_bytecode = True
print __file__
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
print sys.path

import coshsh
from coshsh.generator import Generator
from coshsh.datasource import Datasource
from coshsh.datarecipient import Datarecipient
from coshsh.application import Application
from coshsh.util import setup_logging

class CoshshTest(unittest.TestCase):
    def print_header(self):
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def setUp(self):
        shutil.rmtree("./var/objects/test12", True)
        os.makedirs("./var/objects/test12")
        shutil.rmtree("./var/objects/test1", True)
        os.makedirs("./var/objects/test1")
        self.config = ConfigParser.ConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = coshsh.generator.Generator()
        setup_logging()

    def tearDown(self):
        shutil.rmtree("./var/objects/test12", True)
        shutil.rmtree("./var/objects/test1", True)
        print 

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
        self.assert_(dr_simplesample.objects_dir == "/tmp")
        self.assert_(dr_simplesample.recipe_objects_dir == self.generator.recipes['test12'].objects_dir)
        dr_simplesample2 = [dr for dr in self.generator.recipes['test12'].datarecipients if dr.name == 'simplesample2'][0]
        self.assert_(dr_simplesample2.objects_dir == "./var/objects/test1")
        self.assert_(dr_simplesample2.recipe_objects_dir == self.generator.recipes['test12'].objects_dir)
        dr_default = [dr for dr in self.generator.recipes['test12'].datarecipients if dr.name == 'default'][0]
        self.assert_(dr_default.objects_dir == "./var/objects/test12")
        self.assert_(dr_default.recipe_objects_dir == self.generator.recipes['test12'].objects_dir)

        self.generator.recipes['test12'].collect()
        self.generator.recipes['test12'].assemble()
        self.generator.recipes['test12'].render()
        self.generator.recipes['test12'].output()
        # written by datarecipient_coshsh_default
        self.assert_(os.path.exists("var/objects/test12/dynamic/hosts"))
        self.assert_(os.path.exists("var/objects/test12/dynamic/hosts/test_host_0"))
        self.assert_(os.path.exists("var/objects/test12/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assert_(os.path.exists("var/objects/test12/dynamic/hosts/test_host_1/os_windows_default.cfg"))
        os_windows_default_cfg = open("var/objects/test12/dynamic/hosts/test_host_1/os_windows_default.cfg").read()
        self.assert_('os_windows_default_check_unittest' in os_windows_default_cfg)
        # written by simplesample2 which has it's own objects_dir
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"))
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts/test_host_1/os_windows_default.cfg"))

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
        self.assert_(dr_simplesample.objects_dir == "/tmp")
        self.assert_(dr_simplesample.recipe_objects_dir == self.generator.recipes['test12a'].objects_dir)
        dr_simplesample2 = [dr for dr in self.generator.recipes['test12a'].datarecipients if dr.name == 'simplesample2'][0]
        self.assert_(dr_simplesample2.objects_dir == "./var/objects/test1")
        self.assert_(dr_simplesample2.recipe_objects_dir == self.generator.recipes['test12a'].objects_dir)
        dr_default = [dr for dr in self.generator.recipes['test12a'].datarecipients if dr.name == 'datarecipient_coshsh_default'][0]
        self.assert_(dr_default.objects_dir == "./var/objects/test12")
        self.assert_(dr_default.recipe_objects_dir == self.generator.recipes['test12a'].objects_dir)

        self.generator.recipes['test12a'].collect()
        self.generator.recipes['test12a'].assemble()
        self.generator.recipes['test12a'].render()
        self.generator.recipes['test12a'].output()
        # written by datarecipient_coshsh_default
        self.assert_(os.path.exists("var/objects/test12/dynamic/hosts"))
        self.assert_(os.path.exists("var/objects/test12/dynamic/hosts/test_host_0"))
        self.assert_(os.path.exists("var/objects/test12/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assert_(os.path.exists("var/objects/test12/dynamic/hosts/test_host_1/os_windows_default.cfg"))
        os_windows_default_cfg = open("var/objects/test12/dynamic/hosts/test_host_1/os_windows_default.cfg").read()
        self.assert_('os_windows_default_check_unittest' in os_windows_default_cfg)
        # written by simplesample2 which has it's own objects_dir
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"))
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts/test_host_1/os_windows_default.cfg"))


if __name__ == '__main__':
    unittest.main()

