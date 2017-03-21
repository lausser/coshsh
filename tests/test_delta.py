import unittest
import os
import sys
import shutil
import string
from optparse import OptionParser
import ConfigParser
import logging
import pprint
from subprocess import Popen, PIPE, STDOUT


sys.dont_write_bytecode = True

import coshsh
from coshsh.generator import Generator
from coshsh.datasource import Datasource
from coshsh.application import Application
from coshsh.util import odict

class CoshshTest(unittest.TestCase):
    def print_header(self):
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def setUp(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = coshsh.generator.Generator()
        self.generator.setup_logging()

    def tearDown(self):
        pass

    def clean_generator(self):
        self.generator = None
        self.generator = coshsh.generator.Generator()
        self.generator.setup_logging()

    def test_growing_hosts(self):
        self.print_header()

        # create 100 hosts
        # recipes/test15/data
        self.generator.add_recipe(name='test15', **dict(self.config.items('recipe_TEST15')))
        self.config.set("datasource_CSVSHRINK", "name", "csvshrink")
        cfg = self.config.items("datasource_CSVSHRINK")
        self.generator.recipes['test15'].add_datasource(**dict(cfg))
        print "---->", self.generator.recipes['test15']
        print "mkdir", cfg
        dir = [t[1] for t in cfg if t[0] == 'dir'][0]
        name = [t[1] for t in cfg if t[0] == 'name'][0]
        hosts = os.path.join(dir, name + '_hosts.csv')
        targetdir = './var/objects/test15'
        shutil.rmtree(dir, True)
        shutil.rmtree(targetdir, True)
        print "removed", dir
        os.makedirs(dir)
        with open(hosts, 'a') as f:
            f.write('host_name,address,type,os,hardware,virtual,notification_period,location,department\n')
            for i in range(0,10):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        # remove target dir / create empty
        self.generator.recipes['test15'].count_before_objects()
        self.generator.recipes['test15'].cleanup_target_dir()

        self.generator.recipes['test15'].prepare_target_dir()
        # check target

        # read the datasources
        self.generator.recipes['test15'].collect()

        # for each host, application get the corresponding template files
        # get the template files and cache them in a struct owned by the recipe
        # resolve the templates and attach the result as config_files to host/app
        self.generator.recipes['test15'].render()
        self.assert_(hasattr(self.generator.recipes['test15'].objects['hosts']['test_host_000'], 'config_files'))
        self.assert_('host.cfg' in self.generator.recipes['test15'].objects['hosts']['test_host_000'].config_files)
        self.assert_(hasattr(self.generator.recipes['test15'].objects['hosts']['test_host_009'], 'config_files'))
        self.assert_('host.cfg' in self.generator.recipes['test15'].objects['hosts']['test_host_009'].config_files)

        # write hosts/apps to the filesystem
        self.generator.recipes['test15'].output()
        self.assert_(os.path.exists("var/objects/test15/dynamic/hosts"))
        self.assert_(os.path.exists("var/objects/test15/dynamic/hosts/test_host_000"))
        self.assert_(os.path.exists("var/objects/test15/dynamic/hosts/test_host_000/host.cfg"))
        self.assert_(os.path.exists("var/objects/test15/dynamic/hosts/test_host_009"))
        self.assert_(os.path.exists("var/objects/test15/dynamic/hosts/test_host_009/host.cfg"))

        save_dir = os.getcwd()
        os.chdir('./var/objects/test15/dynamic')
        process = Popen(["git", "init", "."], stdout=PIPE, stderr=STDOUT)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print output
        process = Popen(["git", "add", "."], stdout=PIPE, stderr=STDOUT)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print output
        process = Popen(["git", "commit", "-a", "-m", "commit init"], stdout=PIPE, stderr=STDOUT)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print output
        os.chdir(save_dir)

        with open(hosts, 'a') as f:
            for i in range(10,20):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        self.clean_generator()
        self.generator.add_recipe(name='test15', **dict(self.config.items('recipe_TEST15')))
        self.config.set("datasource_CSVSHRINK", "name", "csvshrink")
        cfg = self.config.items("datasource_CSVSHRINK")
        self.generator.recipes['test15'].add_datasource(**dict(cfg))

        self.generator.recipes['test15'].collect()
        self.generator.recipes['test15'].render()

        self.assert_(hasattr(self.generator.recipes['test15'].objects['hosts']['test_host_010'], 'config_files'))
        self.assert_('host.cfg' in self.generator.recipes['test15'].objects['hosts']['test_host_010'].config_files)
        self.assert_(hasattr(self.generator.recipes['test15'].objects['hosts']['test_host_019'], 'config_files'))
        self.assert_('host.cfg' in self.generator.recipes['test15'].objects['hosts']['test_host_019'].config_files)

        # write hosts/apps to the filesystem
        self.generator.recipes['test15'].output()

        # we violated the delta
        self.assert_(os.path.exists("var/objects/test15/dynamic/hosts"))
        self.assert_(os.path.exists("var/objects/test15/dynamic/hosts/test_host_000"))
        self.assert_(os.path.exists("var/objects/test15/dynamic/hosts/test_host_000/host.cfg"))
        self.assert_(os.path.exists("var/objects/test15/dynamic/hosts/test_host_009/host.cfg"))
        # the hosts 10..20 were automatically resetted and cleaned by the
        # max_delta_action
        self.assert_(not os.path.exists("var/objects/test15/dynamic/hosts/test_host_019"))


    def test_grow_grow_ok(self):
        self.print_header()

        self.generator.add_recipe(name='test16', **dict(self.config.items('recipe_TEST16')))
        self.config.set("datasource_CSVSHRINK", "name", "csvshrink")
        cfg = self.config.items("datasource_CSVSHRINK")
        self.generator.recipes['test16'].add_datasource(**dict(cfg))
        print "---->", self.generator.recipes['test16']
        print "mkdir", cfg
        dir = [t[1] for t in cfg if t[0] == 'dir'][0]
        name = [t[1] for t in cfg if t[0] == 'name'][0]
        hosts = os.path.join(dir, name + '_hosts.csv')
        targetdir = './var/objects/test16'
        shutil.rmtree(dir, True)
        shutil.rmtree(targetdir, True)
        print "removed", dir
        os.makedirs(dir)
        with open(hosts, 'a') as f:
            f.write('host_name,address,type,os,hardware,virtual,notification_period,location,department\n')
            for i in range(0,10):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        # remove target dir / create empty
        self.generator.recipes['test16'].count_before_objects()
        self.generator.recipes['test16'].cleanup_target_dir()

        self.generator.recipes['test16'].prepare_target_dir()
        # check target

        # read the datasources
        self.generator.recipes['test16'].collect()

        # for each host, application get the corresponding template files
        # get the template files and cache them in a struct owned by the recipe
        # resolve the templates and attach the result as config_files to host/app
        self.generator.recipes['test16'].render()
        self.assert_(hasattr(self.generator.recipes['test16'].objects['hosts']['test_host_000'], 'config_files'))
        self.assert_('host.cfg' in self.generator.recipes['test16'].objects['hosts']['test_host_000'].config_files)
        self.assert_(hasattr(self.generator.recipes['test16'].objects['hosts']['test_host_009'], 'config_files'))
        self.assert_('host.cfg' in self.generator.recipes['test16'].objects['hosts']['test_host_009'].config_files)

        # write hosts/apps to the filesystem
        self.generator.recipes['test16'].output()
        self.assert_(os.path.exists("var/objects/test16/dynamic/hosts"))
        self.assert_(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000"))
        self.assert_(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000/host.cfg"))
        self.assert_(os.path.exists("var/objects/test16/dynamic/hosts/test_host_009"))
        self.assert_(os.path.exists("var/objects/test16/dynamic/hosts/test_host_009/host.cfg"))

        save_dir = os.getcwd()
        os.chdir('./var/objects/test16/dynamic')
        process = Popen(["git", "init", "."], stdout=PIPE, stderr=STDOUT)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print output
        process = Popen(["git", "add", "."], stdout=PIPE, stderr=STDOUT)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print output
        process = Popen(["git", "commit", "-a", "-m", "commit init"], stdout=PIPE, stderr=STDOUT)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print output
        os.chdir(save_dir)

        print "and ten more hosts"
        with open(hosts, 'a') as f:
            for i in range(10,20):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        self.clean_generator()
        self.generator.add_recipe(name='test16', **dict(self.config.items('recipe_TEST16')))
        self.config.set("datasource_CSVSHRINK", "name", "csvshrink")
        cfg = self.config.items("datasource_CSVSHRINK")
        self.generator.recipes['test16'].add_datasource(**dict(cfg))

        self.generator.recipes['test16'].collect()
        self.generator.recipes['test16'].render()

        self.assert_(hasattr(self.generator.recipes['test16'].objects['hosts']['test_host_010'], 'config_files'))
        self.assert_('host.cfg' in self.generator.recipes['test16'].objects['hosts']['test_host_010'].config_files)
        self.assert_(hasattr(self.generator.recipes['test16'].objects['hosts']['test_host_019'], 'config_files'))
        self.assert_('host.cfg' in self.generator.recipes['test16'].objects['hosts']['test_host_019'].config_files)

        # write hosts/apps to the filesystem
        self.generator.recipes['test16'].output()

        # we violated the delta
        self.assert_(os.path.exists("var/objects/test16/dynamic/hosts"))
        self.assert_(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000"))
        self.assert_(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000/host.cfg"))
        self.assert_(os.path.exists("var/objects/test16/dynamic/hosts/test_host_009/host.cfg"))
        self.assert_(os.path.exists("var/objects/test16/dynamic/hosts/test_host_019"))


    def test_shrinking_hosts(self):
        self.print_header()

        self.generator.add_recipe(name='test16', **dict(self.config.items('recipe_TEST16')))
        self.config.set("datasource_CSVSHRINK", "name", "csvshrink")
        cfg = self.config.items("datasource_CSVSHRINK")
        self.generator.recipes['test16'].add_datasource(**dict(cfg))
        print "---->", self.generator.recipes['test16']
        print "mkdir", cfg
        dir = [t[1] for t in cfg if t[0] == 'dir'][0]
        name = [t[1] for t in cfg if t[0] == 'name'][0]
        hosts = os.path.join(dir, name + '_hosts.csv')
        targetdir = './var/objects/test16'
        shutil.rmtree(dir, True)
        shutil.rmtree(targetdir, True)
        print "removed", dir
        os.makedirs(dir)
        with open(hosts, 'a') as f:
            f.write('host_name,address,type,os,hardware,virtual,notification_period,location,department\n')
            for i in range(0,10):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        # remove target dir / create empty
        self.generator.recipes['test16'].count_before_objects()
        self.generator.recipes['test16'].cleanup_target_dir()

        self.generator.recipes['test16'].prepare_target_dir()
        # check target

        # read the datasources
        self.generator.recipes['test16'].collect()

        # for each host, application get the corresponding template files
        # get the template files and cache them in a struct owned by the recipe
        # resolve the templates and attach the result as config_files to host/app
        self.generator.recipes['test16'].render()
        self.assert_(hasattr(self.generator.recipes['test16'].objects['hosts']['test_host_000'], 'config_files'))
        self.assert_('host.cfg' in self.generator.recipes['test16'].objects['hosts']['test_host_000'].config_files)
        self.assert_(hasattr(self.generator.recipes['test16'].objects['hosts']['test_host_009'], 'config_files'))
        self.assert_('host.cfg' in self.generator.recipes['test16'].objects['hosts']['test_host_009'].config_files)

        # write hosts/apps to the filesystem
        self.generator.recipes['test16'].output()
        self.assert_(os.path.exists("var/objects/test16/dynamic/hosts"))
        self.assert_(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000"))
        self.assert_(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000/host.cfg"))
        self.assert_(os.path.exists("var/objects/test16/dynamic/hosts/test_host_009"))
        self.assert_(os.path.exists("var/objects/test16/dynamic/hosts/test_host_009/host.cfg"))

        save_dir = os.getcwd()
        os.chdir('./var/objects/test16/dynamic')
        process = Popen(["git", "init", "."], stdout=PIPE, stderr=STDOUT)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print output
        process = Popen(["git", "add", "."], stdout=PIPE, stderr=STDOUT)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print output
        process = Popen(["git", "commit", "-a", "-m", "commit init"], stdout=PIPE, stderr=STDOUT)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print output
        os.chdir(save_dir)

        shutil.rmtree(hosts, True)
        with open(hosts, 'w') as f:
            f.write('host_name,address,type,os,hardware,virtual,notification_period,location,department\n')
            for i in range(0,2):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        self.clean_generator()
        self.generator.add_recipe(name='test16', **dict(self.config.items('recipe_TEST16')))
        self.config.set("datasource_CSVSHRINK", "name", "csvshrink")
        cfg = self.config.items("datasource_CSVSHRINK")
        self.generator.recipes['test16'].add_datasource(**dict(cfg))

        self.generator.recipes['test16'].collect()
        self.generator.recipes['test16'].render()

        self.assert_(hasattr(self.generator.recipes['test16'].objects['hosts']['test_host_000'], 'config_files'))
        self.assert_('host.cfg' in self.generator.recipes['test16'].objects['hosts']['test_host_000'].config_files)
        self.assert_('test_host_001' in self.generator.recipes['test16'].objects['hosts'])
        self.assert_('test_host_002' not in self.generator.recipes['test16'].objects['hosts'])

        # write hosts/apps to the filesystem
        self.generator.recipes['test16'].output()

        # we violated the delta
        self.assert_(os.path.exists("var/objects/test16/dynamic/hosts"))
        self.assert_(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000"))
        self.assert_(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000/host.cfg"))
        self.assert_(os.path.exists("var/objects/test16/dynamic/hosts/test_host_009/host.cfg"))
        # the hosts 10..20 were automatically resetted and cleaned by the
        # max_delta_action
        self.assert_(not os.path.exists("var/objects/test16/dynamic/hosts/test_host_019"))


if __name__ == '__main__':
    unittest.main()


