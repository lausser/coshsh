import unittest
import os
import sys
import shutil
import string
from optparse import OptionParser
import logging

import coshsh
from coshsh.generator import Generator
from coshsh.datasource import Datasource
from coshsh.application import Application
from coshsh.configparser import CoshshConfigParser
from coshsh.util import setup_logging
from tests.common_coshsh_test import CommonCoshshTest

sys.dont_write_bytecode = True

class CoshshTest(CommonCoshshTest):
    _configfile = 'etc/timeperiods.cfg'
    _objectsdir = "./var/objects/tp"
    default_recipe = "test10"

    def print_header(self):
        print("#" * 80 + "\n" + "#" + " " * 78 + "#")
        print("#" + str.center(self.id(), 78) + "#")
        print("#" + " " * 78 + "#\n" + "#" * 80 + "\n")

    def setUps(self):
        os.chdir(os.path.realpath(os.path.dirname(__file__)))
        self.config = coshsh.configparser.CoshshConfigParser()
        self.config.read('etc/timeperiods.cfg')
        self.generator = coshsh.generator.Generator()
        #setup_logging()
        setup_logging(scrnloglevel=logging.DEBUG)

    def tearDowns(self):
        #shutil.rmtree("./var/objects/tp", True)
        pass

    def test_create_recipe_multiple_sources(self):
        self.print_header()
        #self.generator.add_recipe(name='test10', **dict(self.config.items('recipe_TEST10')))
        #self.config.set("datasource_TP", "name", "TP")
        #cfg = self.config.items("datasource_TP")
        #self.generator.recipes['test10'].add_datasource(**dict(cfg))
        import pprint
        pprint.pprint(self.generator.recipes['test10'].datasources[0].__dict__)
        # remove target dir / create empty
        self.generator.recipes['test10'].count_before_objects()
        self.generator.recipes['test10'].cleanup_target_dir()

        self.generator.recipes['test10'].prepare_target_dir()

        self.generator.recipes['test10'].collect()
        self.generator.recipes['test10'].assemble()
        self.generator.recipes['test10'].render()

        print(self.generator.recipes['test10'].objects['hosts'])
        print(self.generator.recipes['test10'].objects['applications'])
        print(self.generator.recipes['test10'].objects['details'])
        self.assertTrue(hasattr(self.generator.recipes['test10'].objects['hosts']['monops_tp_cmd_dummy_host'], 'config_files'))
        self.assertTrue('host.cfg' in self.generator.recipes['test10'].objects['hosts']['monops_tp_cmd_dummy_host'].config_files['nagios'])

        # write hosts/apps to the filesystem
        self.generator.recipes['test10'].output()
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/monops_tp_cmd_dummy_host"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts//monops_tp_cmd_dummy_host/timeperiods_monops.cfg"))


if __name__ == '__main__':
    unittest.main()


