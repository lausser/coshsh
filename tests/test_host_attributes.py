import unittest
import os
import io
import sys
import shutil
import string
from optparse import OptionParser
import logging
from random import choices, randint
from string import ascii_lowercase

import coshsh
from coshsh.generator import Generator
from coshsh.datasource import Datasource
from coshsh.application import Application
from coshsh.configparser import CoshshConfigParser
from coshsh.util import setup_logging
from tests.common_coshsh_test import CommonCoshshTest

sys.dont_write_bytecode = True

class CoshshTest(CommonCoshshTest):
    _configfile = 'etc/coshsh.cfg'
    _objectsdir = "./var/objects/test10"

    def print_header(self):
        print("#" * 80 + "\n" + "#" + " " * 78 + "#")
        print("#" + str.center(self.id(), 78) + "#")
        print("#" + " " * 78 + "#\n" + "#" * 80 + "\n")

    def setUps(self):
        self.config = coshsh.configparser.CoshshConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = coshsh.generator.Generator()
        setup_logging()

    def tearDowns(self):
        shutil.rmtree("./var/objects/test10", True)
        pass

    def test_host_templates_order(self):
        self.print_header()
        self.generator.add_recipe(name='test10', **dict(self.config.items('recipe_TEST10')))
        self.config.set("datasource_CSV10.1", "name", "csv1")
        self.config.set("datasource_CSV10.2", "name", "csv2")
        self.config.set("datasource_CSV10.3", "name", "csv3")
        cfg = self.config.items("datasource_CSV10.1")
        self.generator.recipes['test10'].add_datasource(**dict(cfg))
        cfg = self.config.items("datasource_CSV10.2")
        self.generator.recipes['test10'].add_datasource(**dict(cfg))
        cfg = self.config.items("datasource_CSV10.3")
        self.generator.recipes['test10'].add_datasource(**dict(cfg))
        # remove target dir / create empty
        self.generator.recipes['test10'].count_before_objects()
        self.generator.recipes['test10'].cleanup_target_dir()

        self.generator.recipes['test10'].prepare_target_dir()
        # check target

        # read the datasources
        self.generator.recipes['test10'].collect()
        saved_templates = {}
        for host in self.generator.recipes['test10'].objects["hosts"].values():
            for len in range(3, randint(4, 10)):
                host.templates.append("".join(choices(ascii_lowercase, k=len)))
            saved_templates[host.host_name] = [t for t in host.templates]
            print("{} has {}".format(host.host_name, ",".join(host.templates)))

        self.generator.recipes['test10'].assemble()

        # for each host, application get the corresponding template files
        # get the template files and cache them in a struct owned by the recipe
        # resolve the templates and attach the result as config_files to host/app
        self.generator.recipes['test10'].render()
        for host in self.generator.recipes['test10'].objects["hosts"].values():
            print("{} has {}".format(host.host_name, ",".join(host.templates)))
            pass

        self.assertTrue(hasattr(self.generator.recipes['test10'].objects['hosts']['test_host_0'], 'config_files'))
        self.assertTrue('host.cfg' in self.generator.recipes['test10'].objects['hosts']['test_host_0'].config_files['nagios'])

        # write hosts/apps to the filesystem
        self.generator.recipes['test10'].output()
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts"))
        for host in self.generator.recipes['test10'].objects["hosts"].values():
            self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/"+host.host_name+"/host.cfg"))
            with io.open("var/objects/test10/dynamic/hosts/"+host.host_name+"/host.cfg") as f:
                host_cfg = f.read()
                self.assertTrue(",".join(saved_templates[host.host_name]) in host_cfg)


if __name__ == '__main__':
    unittest.main()


