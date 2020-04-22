import unittest
import os
import io
import sys
import shutil
from optparse import OptionParser
from configparser import RawConfigParser
import logging


sys.dont_write_bytecode = True
sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath(os.path.join("..", "coshsh")))

import coshsh
from coshsh.generator import Generator
from coshsh.datasource import Datasource
from coshsh.application import Application
from coshsh.util import setup_logging

class CoshshTest(unittest.TestCase):
    def print_header(self):
        print("#" * 80 + "\n" + "#" + " " * 78 + "#")
        print("#" + str.center(self.id(), 78) + "#")
        print("#" + " " * 78 + "#\n" + "#" * 80 + "\n")

    def setUp(self):
        shutil.rmtree("./var/objects/test1", True)
        os.makedirs("./var/objects/test1")
        shutil.rmtree("./var/log", True)
        os.makedirs("./var/log")
        self.config = RawConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = coshsh.generator.Generator()
        setup_logging(logfile="zishsh.log", logdir="./var/log", scrnloglevel=logging.DEBUG, txtloglevel=logging.INFO)
        # default, wie im coshsh-cook
        setup_logging(logdir="./var/log", scrnloglevel=logging.INFO)

    def tearDown(self):
        #shutil.rmtree("./var/objects/test1", True)
        print()

    def test_log(self):
        logger = logging.getLogger('zishsh')
        print(logger.__dict__)
        print
        for h in logger.handlers:
            print(h.__dict__)
            print
        logger.warn("i warn you")
        logger.info("i inform you")
        logger.debug("i spam you")
        self.assertTrue(os.path.exists("./var/log/zishsh.log"))
        with io.open('./var/log/zishsh.log') as x:
            zishshlog = x.read()
        self.assertTrue("WARNING" in zishshlog)
        self.assertTrue("INFO" in zishshlog)
        self.assertTrue("DEBUG" not in zishshlog)

    def test_write(self):
        # innendrin im Code wird logging.getLogger('coshsh') aufgerufen
        self.print_header()
        self.generator.add_recipe(name='test4', **dict(self.config.items('recipe_TEST4')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        self.generator.recipes['test4'].add_datasource(**dict(cfg))

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
        self.assertTrue('host.cfg' in self.generator.recipes['test4'].objects['hosts']['test_host_0'].config_files['nagios'])

        # write hosts/apps to the filesystem
        self.generator.recipes['test4'].output()
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg"))
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue('os_windows_default_check_unittest' in os_windows_default_cfg)
        self.assertTrue(os.path.exists("./var/log/coshsh.log"))
        with io.open('./var/log/coshsh.log') as x:
            coshshlog = x.read()
        self.assertTrue("test_host_0" in coshshlog)


if __name__ == '__main__':
    unittest.main()


