import unittest
import os
import sys
import shutil
import string
from optparse import OptionParser
import ConfigParser
import logging
import pprint
from logging import INFO, DEBUG
from tempfile import gettempdir
import re

sys.dont_write_bytecode = True

import coshsh
from coshsh.generator import Generator
from coshsh.datasource import Datasource
from coshsh.host import Host
from coshsh.application import Application
from coshsh.monitoringdetail import MonitoringDetail

class CoshshTest(unittest.TestCase):
    def print_header(self):
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def setUp(self):
        shutil.rmtree("./var/objects/test33", True)
        os.makedirs("./var/objects/test33")
        shutil.rmtree("./var/log/coshshlogs", True)
        self.config = ConfigParser.ConfigParser()
        self.config.read('etc/coshsh5.cfg')
	print self.config.__dict__
        self.generator = coshsh.generator.Generator()
	if "defaults" in self.config.sections() and "log_dir" in [c[0] for c in self.config.items("defaults")]:
            log_dir = dict(self.config.items("defaults"))["log_dir"]
            log_dir = re.sub('%.*?%', coshsh.util.substenv, log_dir)
        elif 'OMD_ROOT' in os.environ:
            log_dir = os.path.join(os.environ['OMD_ROOT'], "var", "coshsh")
        else:
            log_dir = gettempdir()
        self.generator.setup_logging(logdir=log_dir, scrnloglevel=logging.DEBUG)

    def tearDown(self):
        shutil.rmtree("./var/objects/test33", True)
        print

    def test_generic_app(self):
        self.print_header()
        self.generator.add_recipe(name='test33', **dict(self.config.items('recipe_test33')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
	self.assert_(hasattr(self.generator.recipes['test33'], "log_file"))
	self.assert_(self.generator.recipes['test33'].log_file == "./var/log/coshsh_test33.log")
        self.generator.recipes['test33'].add_datasource(**dict(cfg))
        self.generator.recipes['test33'].datasources[0].objects = self.generator.recipes['test33'].objects
        host = Host({
            'host_name': 'testhost',
            'address': '127.0.0.1',
        })
        self.generator.recipes['test33'].datasources[0].add('hosts', host)
        app = Application({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',
        })
        self.generator.recipes['test33'].datasources[0].add('applications', app)
        self.generator.recipes['test33'].collect()
        self.generator.recipes['test33'].assemble()
        self.generator.recipes['test33'].render()
        self.assert_(len(self.generator.recipes['test33'].objects['applications']) == 1)
        self.assert_(self.generator.recipes['test33'].datasources[0].getall('applications')[0] == app)
        self.assert_(self.generator.recipes['test33'].datasources[0].getall('applications')[0].__class__ == coshsh.application.GenericApplication)
        self.generator.recipes['test33'].output()
        self.assert_(os.path.exists("var/objects/test33/dynamic/hosts/testhost/host.cfg"))
        self.assert_(not os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_fs.cfg"))
        self.assert_(not os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_ports.cfg"))

    def test_mygeneric_app(self):
        self.print_header()
        self.generator.add_recipe(name='test34', **dict(self.config.items('recipe_test34')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        self.generator.recipes['test34'].add_datasource(**dict(cfg))
        self.generator.recipes['test34'].datasources[0].objects = self.generator.recipes['test34'].objects
        host = Host({
            'host_name': 'testhost',
            'address': '127.0.0.1',
        })
        self.generator.recipes['test34'].datasources[0].add('hosts', host)
        app = Application({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',
        })
        self.generator.recipes['test34'].datasources[0].add('applications', app)
        self.generator.recipes['test34'].datasources[0].add('details', MonitoringDetail({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',
            'monitoring_type': 'FILESYSTEM',
            'monitoring_0': '/',
            'monitoring_1': 90,
            'monitoring_2': 95,
        }))
        self.generator.recipes['test34'].datasources[0].add('details', MonitoringDetail({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',
            'monitoring_type': 'PORT',
            'monitoring_0': 80,
            'monitoring_1': 1,
            'monitoring_2': 5,
        }))
        self.generator.recipes['test34'].collect()
        self.generator.recipes['test34'].assemble()
        self.generator.recipes['test34'].render()
        self.assert_(len(self.generator.recipes['test34'].objects['applications']) == 1)
        self.assert_(self.generator.recipes['test34'].datasources[0].getall('applications')[0] == app)
        self.assert_(self.generator.recipes['test34'].datasources[0].getall('applications')[0].__class__.__name__ == "MyGenericApplication")
        self.generator.recipes['test34'].output()
        self.assert_(os.path.exists("var/objects/test33/dynamic/hosts/testhost/host.cfg"))
        self.assert_(os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_fs.cfg"))
        self.assert_(os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_ports.cfg"))

