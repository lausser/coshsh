import unittest
import os
import sys
import shutil
from optparse import OptionParser
from configparser import RawConfigParser
import logging


sys.dont_write_bytecode = True

import coshsh
from coshsh.generator import Generator
from coshsh.util import setup_logging


class CoshshTest(unittest.TestCase):
    def print_header(self):
        print("#" * 80 + "\n" + "#" + " " * 78 + "#")
        print("#" + str.center(self.id(), 78) + "#")
        print("#" + " " * 78 + "#\n" + "#" * 80 + "\n")

    def setUp(self):
        shutil.rmtree("./var/objects/test1", True)
        os.makedirs("./var/objects/test1")
        self.config = RawConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = coshsh.generator.Generator()
        setup_logging(scrnloglevel=logging.DEBUG)

    def tearDown(self):
        shutil.rmtree("./var/objects/test1", True)
        print()

    def test_osenviron(self):
        self.print_header()
        self.generator.add_recipe(name='test4', **dict(self.config.items('recipe_TEST4B')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        self.generator.recipes['test4'].add_datasource(**dict(cfg))
        self.config.set("datarecipient_SIMPLESAMPLE2", "name", "simplesample")
        cfg = self.config.items("datarecipient_SIMPLESAMPLE2")
        self.generator.recipes['test4'].add_datarecipient(**dict(cfg))


        # remove target dir / create empty
        self.generator.recipes['test4'].count_before_objects()
        self.generator.recipes['test4'].cleanup_target_dir()

        self.generator.recipes['test4'].prepare_target_dir()
        # check target

        # read the datasources
        self.generator.recipes['test4'].collect()
        self.generator.recipes['test4'].assemble()
        
        # for each host, application get the corresponding template files
        # get the template files and cache them in a struct owned by the recipe
        # resolve the templates and attach the result as config_files to host/app
        self.generator.recipes['test4'].render()
        self.assertTrue(hasattr(self.generator.recipes['test4'].objects['hosts']['test_host_0'], 'config_files'))
        self.assertTrue('host.cfg' in self.generator.recipes['test4'].objects['hosts']['test_host_0'].config_files["nagios"])

        # write hosts/apps to the filesystem
        self.generator.recipes['test4'].output()
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg"))
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue('environment variable COSHSHENV1 ()' in os_windows_default_cfg)
        self.assertTrue('environment default COSHSHENV1 (schlurz)' in os_windows_default_cfg)

        shutil.rmtree("./var/objects/test1", True)
        os.makedirs("./var/objects/test1")
        os.environ["COSHSHENV1"] = "die nr 1"
        os.environ["COSHSHENV2"] = "die nr 2"
        self.generator.recipes['test4'].render()
        self.generator.recipes['test4'].output()
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue('environment variable COSHSHENV1 (die nr 1)' in os_windows_default_cfg)
        self.assertTrue('environment variable COSHSHENV2 (die nr 2)' in os_windows_default_cfg)
        self.assertTrue('environment default COSHSHENV1 (die nr 1)' in os_windows_default_cfg)
        self.assertTrue('environment variante die nr 2' in os_windows_default_cfg)

        shutil.rmtree("./var/objects/test1", True)
        os.makedirs("./var/objects/test1")
        os.environ["COSHSHENV1"] = "variante1"
        self.generator.recipes['test4'].render()
        self.generator.recipes['test4'].output()
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue('environment variable COSHSHENV1 (variante1)' in os_windows_default_cfg)
        self.assertTrue('environment variable COSHSHENV2 (die nr 2)' in os_windows_default_cfg)
        self.assertTrue('environment variante variante1' in os_windows_default_cfg)

        shutil.rmtree("./var/objects/test1", True)
        os.makedirs("./var/objects/test1")
        os.environ["COSHSHENV1"] = "variantex"
        self.generator.recipes['test4'].render()
        self.generator.recipes['test4'].output()
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue('environment variable COSHSHENV1 (variantex)' in os_windows_default_cfg)
        self.assertTrue('environment variable COSHSHENV2 (die nr 2)' in os_windows_default_cfg)
        self.assertTrue('environment variante die nr 2' in os_windows_default_cfg)


