import unittest
import os
import sys
import shutil
import string
from optparse import OptionParser
import ConfigParser
import logging


sys.dont_write_bytecode = True

import coshsh
from coshsh.generator import Generator
from coshsh.datasource import Datasource
from coshsh.datarecipient import Datarecipient
from coshsh.application import Application

class CoshshTest(unittest.TestCase):
    def print_header(self):
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def setUp(self):
        shutil.rmtree("./var/objects/test12", True)
        os.makedirs("./var/objects/test12")
        self.config = ConfigParser.ConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = coshsh.generator.Generator()
        self.generator.setup_logging()

    def tearDown(self):
        shutil.rmtree("./var/objects/test12", True)
        print 

    def test_create_recipe_collect(self):
        attributes_for_adapters = ["name", "force", "safe_output", "pid_dir", "pid_file", "templates_dir", "classes_dir", "max_delta", "classes_path", "templates_path", "filter", "objects_dir"]
        self.print_header()
        self.generator.add_recipe(name='test12', **dict(self.config.items('recipe_TEST12')))

        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        self.generator.recipes['test12'].add_datasource(**dict(cfg))

        self.config.set("datasource_CSVSAMPLE", "name", "csvsample")
        cfg = self.config.items("datasource_CSVSAMPLE")
        self.generator.recipes['test12'].add_datasource(**dict(cfg))

        self.config.set("datarecipient_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datarecipient_SIMPLESAMPLE")
        self.generator.recipes['test12'].add_datarecipient(**dict(cfg))

        self.config.set("datarecipient_SIMPLESAMPLE2", "name", "simplesample2")
        cfg = self.config.items("datarecipient_SIMPLESAMPLE2")
        self.generator.recipes['test12'].add_datarecipient(**dict(cfg))

        self.generator.recipes['test12'].hand_down_to_ds_dr()
        for attr in attributes_for_adapters:
            self.assert_(hasattr(self.generator.recipes['test12'], attr))
            for ds in self.generator.recipes['test12'].datasources:
                self.assert_(hasattr(ds, "recipe_"+attr))
            for dr in self.generator.recipes['test12'].datarecipients:
                self.assert_(hasattr(dr, "recipe_"+attr))
        dr_simplesample = [dr for dr in self.generator.recipes['test12'].datarecipients if dr.name == 'simplesample'][0]
        self.assert_(dr_simplesample.objects_dir == "/tmp")
        self.assert_(dr_simplesample.recipe_objects_dir == self.generator.recipes['test12'].objects_dir)
        dr_simplesample2 = [dr for dr in self.generator.recipes['test12'].datarecipients if dr.name == 'simplesample2'][0]
        self.assert_(dr_simplesample2.objects_dir == "./var/objects/test1")
        self.assert_(dr_simplesample2.recipe_objects_dir == self.generator.recipes['test12'].objects_dir)


if __name__ == '__main__':
    unittest.main()

