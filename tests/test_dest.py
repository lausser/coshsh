import unittest
import os
import sys
import shutil
from optparse import OptionParser
from configparser import RawConfigParser
import logging

import coshsh
from coshsh.generator import Generator
from coshsh.datasource import Datasource
from coshsh.datarecipient import Datarecipient
from coshsh.application import Application
from coshsh.util import setup_logging
from tests.common_coshsh_test import CommonCoshshTest

sys.dont_write_bytecode = True

class CoshshTest(CommonCoshshTest):
    _configfile = 'etc/coshsh.cfg'
    _objectsdir = "./var/objects/test9"

    def print_header(self):
        print("#" * 80 + "\n" + "#" + " " * 78 + "#")
        print("#" + str.center(self.id(), 78) + "#")
        print("#" + " " * 78 + "#\n" + "#" * 80 + "\n")

    def setUps(self):
        shutil.rmtree("./var/objects/test9", True)
        os.makedirs("./var/objects/test9")
        self.config = RawConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = coshsh.generator.Generator()
        setup_logging()

    def tearDowns(self):
        #shutil.rmtree("./var/objects/test1", True)
        print()

    def test_factories(self):
        self.print_header()
        self.generator.add_recipe(name='test9', **dict(self.config.items('recipe_TEST9')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        ds = coshsh.datasource.Datasource(**dict(cfg))
        self.assertTrue(hasattr(ds, 'only_the_test_simplesample'))
        self.config.set("datarecipient_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datarecipient_SIMPLESAMPLE")
        ds = coshsh.datarecipient.Datarecipient(**dict(cfg))
        self.assertTrue(hasattr(ds, 'only_the_test_simplesample') and ds.only_the_test_simplesample == False)

    def test_create_recipe_check_factories(self):
        self.print_header()
        self.generator.add_recipe(name='test9', **dict(self.config.items('recipe_TEST9')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        self.generator.recipes['test9'].add_datasource(**dict(cfg))
        self.config.set("datarecipient_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datarecipient_SIMPLESAMPLE")
        self.generator.recipes['test9'].add_datarecipient(**dict(cfg))
        self.assertTrue(self.generator.recipes['test9'].datasources[0].only_the_test_simplesample == True)
        self.assertTrue(self.generator.recipes['test9'].datarecipients[0].only_the_test_simplesample == False)


    def test_create_recipe_fallback_datarecipient(self):
        self.print_header()
        self.generator.add_recipe(name='test9a', **dict(self.config.items('recipe_TEST9a')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        self.generator.recipes['test9a'].add_datasource(**dict(cfg))
        # there must be a recipient named "datarecipient_coshsh_default"
        self.assertTrue(self.generator.recipes['test9a'].datarecipients[0].name == "datarecipient_coshsh_default")
        # which must inherit the recipe's object_dir
        self.assertTrue(self.generator.recipes['test9a'].datarecipients[0].objects_dir == self.generator.recipes['test9a'].objects_dir)

    def test_create_recipe_fallback_datarecipient_write(self):
        self.print_header()
        self.generator.add_recipe(name='test9a', **dict(self.config.items('recipe_TEST9a')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        self.generator.recipes['test9a'].add_datasource(**dict(cfg))
        self.assertTrue(self.generator.recipes['test9a'].datarecipients[0].name == "datarecipient_coshsh_default")
        exporter = self.generator.recipes['test9a'].datarecipients[0]
        exporter.count_before_objects()
        self.assertTrue(exporter.old_objects == (0, 0))
        self.generator.recipes['test9a'].collect()
        self.generator.recipes['test9a'].assemble()
        # fill items.[cfgfiles]
        self.generator.recipes['test9a'].render()
        self.generator.recipes['test9a'].output()
        exporter.count_after_objects()
        self.assertTrue(exporter.new_objects == (1, 2))

    def test_mcid_recipient(self):
        self.print_header()
        recipe = {'classes_dir': './recipes/test9/classes', 'datarecipients': 'xpaas'}
        datasource = {'name': 'datasource', 'type': 'simplesample'}
        datareceiver = {'name': 'datarcv', 'type': 'xpaas', 'objects_dir': './var/objects/test9'}
        self.generator.add_recipe(name='recp', **recipe)
        self.generator.recipes['recp'].add_datasource(**datasource)
        self.generator.recipes['recp'].add_datarecipient(**datareceiver)
        self.generator.recipes['recp'].collect()
        self.generator.recipes['recp'].assemble()
        mcid = 1
        for host in self.generator.recipes['recp'].objects['hosts'].values():
            setattr(host, "mcid", "%010d" % mcid)
            mcid += 1
        for app in self.generator.recipes['recp'].objects['applications'].values():
            setattr(app, "mcid", "%010d" % mcid)
            mcid += 1
        self.generator.recipes['recp'].render()
        self.generator.recipes['recp'].output()

    def test_create_recipe_collect(self):
        self.print_header()
        self.generator.add_recipe(name='test9', **dict(self.config.items('recipe_TEST9')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        self.generator.recipes['test9'].add_datasource(**dict(cfg))
        self.config.set("datarecipient_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datarecipient_SIMPLESAMPLE")
        self.generator.recipes['test9'].add_datarecipient(**dict(cfg))
        self.generator.recipes['test9'].collect()
        self.generator.recipes['test9'].assemble()
        self.generator.recipes['test9'].output()




if __name__ == '__main__':
    unittest.main()


