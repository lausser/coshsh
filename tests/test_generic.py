import unittest
import os
import sys
import shutil
from optparse import OptionParser
from configparser import RawConfigParser
import logging
import pprint
from logging import INFO, DEBUG
from tempfile import gettempdir

sys.dont_write_bytecode = True

import coshsh
from coshsh.generator import Generator
from coshsh.datasource import Datasource
from coshsh.host import Host
from coshsh.application import Application
from coshsh.monitoringdetail import MonitoringDetail
from coshsh.util import setup_logging
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):
    _configfile = 'etc/coshsh5.cfg'
    _objectsdir = "./var/objects/test33"

    def test_generic_app(self):
        self.print_header()
        self.generator.add_recipe(name='test33', **dict(self.config.items('recipe_test33')))
        self.config.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.config.items("datasource_SIMPLESAMPLE")
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
        self.assertTrue(len(self.generator.recipes['test33'].objects['applications']) == 1)
        self.assertTrue(self.generator.recipes['test33'].datasources[0].getall('applications')[0] == app)
        self.assertTrue(self.generator.recipes['test33'].datasources[0].getall('applications')[0].__class__ == coshsh.application.GenericApplication)
        self.generator.recipes['test33'].output()
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hosts/testhost/host.cfg"))
        self.assertTrue(not os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_fs.cfg"))
        self.assertTrue(not os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_ports.cfg"))
        raise

    def xtest_mygeneric_app(self):
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
        self.assertTrue(len(self.generator.recipes['test34'].objects['applications']) == 1)
        self.assertTrue(self.generator.recipes['test34'].datasources[0].getall('applications')[0] == app)
        self.assertTrue(self.generator.recipes['test34'].datasources[0].getall('applications')[0].__class__.__name__ == "MyGenericApplication")
        self.generator.recipes['test34'].output()
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hosts/testhost/host.cfg"))
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_fs.cfg"))
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_ports.cfg"))

