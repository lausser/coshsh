"""Tests for recipe-level log file creation and log directory configuration."""
import os
from coshsh.host import Host
from coshsh.application import Application, GenericApplication
from tests.common_coshsh_test import CommonCoshshTest


class RecipeLogsTest(CommonCoshshTest):

    def test_generic_app(self):
        """Recipe-level log file is created when recipe is loaded."""
        self.setUpConfig("etc/coshsh5.cfg", "test33")
        r = self.generator.get_recipe("test33")
        r.update_item_class_factories()
        ds = self.generator.get_recipe("test33").get_datasource("simplesample")
        ds.objects = r.objects

        self.assertTrue(os.path.exists("./var/log/coshshlogs/coshsh_test33.log"))

        host = Host({
            'host_name': 'testhost',
            'address': '127.0.0.1',
        })
        ds.add('hosts', host)
        app = Application({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',
        })
        self.generator.recipes['test33'].datasources[0].add('applications', app)
        self.generator.recipes['test33'].collect()
        self.generator.recipes['test33'].assemble()
        self.generator.recipes['test33'].render()
        self.assertEqual(len(self.generator.recipes['test33'].objects['applications']), 1)
        self.assertEqual(
            list(self.generator.recipes['test33'].datasources[0].getall('applications'))[0],
            app
        )
        self.assertEqual(
            list(self.generator.recipes['test33'].datasources[0].getall('applications'))[0].__class__,
            GenericApplication
        )
        self.generator.recipes['test33'].output()
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hosts/testhost/host.cfg"))
        self.assertFalse(os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_fs.cfg"))
        self.assertFalse(os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_ports.cfg"))

    def test_everything_default(self):
        """Default generator log file is created at the default path when no log_dir is set."""
        self.setUpConfig("etc/coshsh5.cfg", "test35")
        self.assertTrue(os.path.exists("./var/log/coshshlogs/coshsh.log"))

    def test_extra_dir(self):
        """Recipe-level log file is written to an explicit extra log directory."""
        self.setUpConfig("etc/coshsh5.cfg", "test36")
        self.assertTrue(os.path.exists("/tmp/coshsh5/coshsh.log"))
