import unittest
import os
import io
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
        shutil.rmtree("./var/objects/test4", True)
        os.makedirs("./var/objects/test4")
        self.config = RawConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = coshsh.generator.Generator()
        setup_logging(scrnloglevel=logging.DEBUG)

    def tearDown(self):
        #shutil.rmtree("./var/objects/test1", True)
        print()

    def test_create_recipe_check_paths(self):
        self.print_header()
        self.generator.add_recipe(name='test4', **dict(self.config.items('recipe_TESTjinja')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        self.generator.recipes['test4'].add_datasource(**dict(cfg))
        self.generator.recipes['test4'].collect()
        self.generator.recipes['test4'].assemble()
        self.generator.recipes['test4'].render()
        self.generator.recipes['test4'].output()
        self.assertTrue(os.path.exists('var/objects/test4/dynamic/hosts/test_host_0/os_linux_default.cfg'))
        self.assertTrue(os.path.exists('var/objects/test4/dynamic/hosts/test_host_0/os_windows_default.cfg'))
        with io.open("var/objects/test4/dynamic/hosts/test_host_0/os_windows_kaas.cfg") as f:
            os_windows_kaas_cfg = f.read()
            self.assertTrue('os_linux.Linux' in os_windows_kaas_cfg)
            self.assertTrue('# type is red hat' in os_windows_kaas_cfg)
            self.assertTrue('# class is Linux' in os_windows_kaas_cfg)
            self.assertTrue('os_windows.Windows' in os_windows_kaas_cfg)
            self.assertTrue('# type is windows' in os_windows_kaas_cfg)
            self.assertTrue('# class is Windows' in os_windows_kaas_cfg)
            self.assertTrue("# ('red hat', 'os', 'linux')" in os_windows_kaas_cfg)
            self.assertTrue('ttype is red hat' in os_windows_kaas_cfg)
            self.assertTrue("# ('windows', 'os', 'windows')" in os_windows_kaas_cfg)
            self.assertTrue('ttype is windows' in os_windows_kaas_cfg)

        return

