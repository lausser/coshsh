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


class CoshshTest(unittest.TestCase):
    def print_header(self):
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def setUp(self):
        shutil.rmtree("./var/objects/test13", True)
        os.makedirs("./var/objects/test13")
        self.config = ConfigParser.ConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = coshsh.generator.Generator()
        self.generator.setup_logging(scrnloglevel=logging.DEBUG)

    def tearDown(self):
        #shutil.rmtree("./var/objects/test1", True)
        print 

    def test_check_class_order(self):
        """
        classes_dir = ./recipes/test13d/classes,./recipes/test13c/classes
        templates_dir = ./recipes/test13d/templates,./recipes/test13c/templates

        department		corporate		default
	os_linux.py		os_linux.py		os_linux.py
	os_beos.py
	os_aix.py		os_aix.py
				os_dos.py

        department		corporate		default
	os_linux_default.tpl	os_linux_default.tpl	os_linux_default.tpl
				os_beos_default.tpl
	os_aix_default.tpl	os_aix_default.tpl
	os_dos_default.tpl
	

	
        """
        self.print_header()
        self.generator.add_recipe(name='test13', **dict(self.config.items('recipe_TEST13')))
        self.config.set("datasource_CSV13", "name", "csv13")
        cfg = self.config.items("datasource_CSV13")
        self.generator.recipes['test13'].add_datasource(**dict(cfg))

        # remove target dir / create empty
        self.generator.recipes['test13'].count_before_objects()
        self.generator.recipes['test13'].cleanup_target_dir()

        self.generator.recipes['test13'].prepare_target_dir()
        # check target

        # read the datasources
        self.generator.recipes['test13'].collect()
        self.generator.recipes['test13'].assemble()

        # for each host, application get the corresponding template files
        # get the template files and cache them in a struct owned by the recipe
        # resolve the templates and attach the result as config_files to host/app
        self.generator.recipes['test13'].render()
        self.assert_(hasattr(self.generator.recipes['test13'].objects['hosts']['linux_host'], 'config_files'))
        self.assert_('host.cfg' in self.generator.recipes['test13'].objects['hosts']['linux_host'].config_files['nagios'])

        # write hosts/apps to the filesystem
        self.generator.recipes['test13'].output()
        self.assert_(os.path.exists("var/objects/test13/dynamic/hosts"))
        self.assert_(os.path.exists("var/objects/test13/dynamic/hosts/linux_host"))
        self.assert_(os.path.exists("var/objects/test13/dynamic/hosts/linux_host/os_linux_default.cfg"))
        self.assert_(os.path.exists("var/objects/test13/dynamic/hosts/aix_host/os_aix_default.cfg"))
        self.assert_(os.path.exists("var/objects/test13/dynamic/hosts/beos_host/os_beos_default.cfg"))
        self.assert_(os.path.exists("var/objects/test13/dynamic/hosts/dos_host/os_dos_default.cfg"))
        self.assert_(os.path.exists("var/objects/test13/dynamic/hosts/windows_host/os_windows_default.cfg"))

        # test classes
        print self.generator.recipes['test13'].objects['applications']
        self.assert_(self.generator.recipes['test13'].objects['applications']['linux_host+os+red hat'].marker == 'department')
        self.assert_(self.generator.recipes['test13'].objects['applications']['beos_host+os+beos'].marker == 'department')
        self.assert_(self.generator.recipes['test13'].objects['applications']['aix_host+os+aix'].marker == 'department')
        self.assert_(self.generator.recipes['test13'].objects['applications']['dos_host+os+dos'].marker == 'corporate')
        self.assert_(not hasattr(self.generator.recipes['test13'].objects['applications']['windows_host+os+windows'], 'marker'))
        # test templates
        os_linux_default_cfg = open("var/objects/test13/dynamic/hosts/linux_host/os_linux_default.cfg").read()
        self.assert_('department' in os_linux_default_cfg)
        os_beos_default_cfg = open("var/objects/test13/dynamic/hosts/beos_host/os_beos_default.cfg").read()
        self.assert_('corporate' in os_beos_default_cfg)
        os_aix_default_cfg = open("var/objects/test13/dynamic/hosts/aix_host/os_aix_default.cfg").read()
        self.assert_('department' in os_aix_default_cfg)
        os_dos_default_cfg = open("var/objects/test13/dynamic/hosts/dos_host/os_dos_default.cfg").read()
        self.assert_('department' in os_dos_default_cfg)
        os_windows_default_cfg = open("var/objects/test13/dynamic/hosts/windows_host/os_windows_default.cfg").read()
        self.assert_('define' in os_windows_default_cfg)
        host_cfg = open("var/objects/test13/dynamic/hosts/windows_host/host.cfg").read()
        self.assert_('corporate host' in host_cfg)


if __name__ == '__main__':
    unittest.main()


