import os
import io
import shutil
from subprocess import Popen, PIPE, STDOUT
import coshsh
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):
    _configfile = 'etc/coshsh.cfg'
    _objectsdir = "./var/objects/test1"

    def test_growing_hosts(self):
        self.setUpConfig("etc/coshsh.cfg", "test15")
        r = self.generator.get_recipe("test15")
        # create 10 hosts
        # reset
        # create another 10 hosts
        # failes because of too much delta
        ds = r.get_datasource("csvgrow")
        dir = ds.dir
        name = ds.name
        hosts = os.path.join(dir, name + '_hosts.csv')
        print("hosts file is "+hosts)
        targetdir = './var/objects/test15'
        shutil.rmtree(dir, True)
        shutil.rmtree(targetdir, True)
        print("removed", dir)
        os.makedirs(dir)
        with io.open(hosts, 'w') as f:
            f.write('host_name,address,type,os,hardware,virtual,notification_period,location,department\n')
            for i in range(0,10):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        self.generator.run()
        self.assertTrue(hasattr(r.objects['hosts']['test_host_000'], 'config_files'))
        self.assertTrue('host.cfg' in r.objects['hosts']['test_host_000'].config_files['nagios'])
        self.assertTrue(hasattr(r.objects['hosts']['test_host_009'], 'config_files'))
        self.assertTrue('host.cfg' in r.objects['hosts']['test_host_009'].config_files['nagios'])
        self.assertTrue(os.path.exists("var/objects/test15/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test15/dynamic/hosts/test_host_000"))
        self.assertTrue(os.path.exists("var/objects/test15/dynamic/hosts/test_host_000/host.cfg"))
        self.assertTrue(os.path.exists("var/objects/test15/dynamic/hosts/test_host_009"))
        self.assertTrue(os.path.exists("var/objects/test15/dynamic/hosts/test_host_009/host.cfg"))

        save_dir = os.getcwd()
        os.chdir('./var/objects/test15/dynamic')
        process = Popen(["git", "init", "."], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        process = Popen(["git", "add", "."], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        process = Popen(["git", "commit", "-a", "-m", "commit init"], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        os.chdir(save_dir)

        with io.open(hosts, 'a') as f:
            for i in range(10,20):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        self.clean_generator()
        self.setUpConfig("etc/coshsh.cfg", "test15")
        r = self.generator.get_recipe("test15")
        ds = r.get_datasource("csvgrow")

        self.generator.run()
        self.assertTrue(hasattr(r.objects['hosts']['test_host_010'], 'config_files'))
        self.assertTrue('host.cfg' in r.objects['hosts']['test_host_010'].config_files['nagios'])
        self.assertTrue(hasattr(r.objects['hosts']['test_host_019'], 'config_files'))
        self.assertTrue('host.cfg' in r.objects['hosts']['test_host_019'].config_files['nagios'])
        # write hosts/apps to the filesystem
        # we violated the delta
        self.assertTrue(os.path.exists("var/objects/test15/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test15/dynamic/hosts/test_host_000"))
        self.assertTrue(os.path.exists("var/objects/test15/dynamic/hosts/test_host_000/host.cfg"))
        self.assertTrue(os.path.exists("var/objects/test15/dynamic/hosts/test_host_009/host.cfg"))
        # the hosts 10..20 were automatically resetted and cleaned by the
        # max_delta_action
        self.assertTrue(not os.path.exists("var/objects/test15/dynamic/hosts/test_host_019"))


    def test_grow_grow_ok(self):
        self.setUpConfig("etc/coshsh.cfg", "test16")
        r = self.generator.get_recipe("test16")
        # create 10 hosts
        # reset
        # create another 10 hosts
        # succeeds because delta threshold is -10
        # growing is ok
        ds = r.get_datasource("csvshrink")
        dir = ds.dir
        name = ds.name
        hosts = os.path.join(dir, name + '_hosts.csv')
        print("hosts file is "+hosts)
        targetdir = './var/objects/test16'
        shutil.rmtree(dir, True)
        shutil.rmtree(targetdir, True)
        print("removed", dir)
        os.makedirs(dir)
        with io.open(hosts, 'w') as f:
            f.write('host_name,address,type,os,hardware,virtual,notification_period,location,department\n')
            for i in range(0,10):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)
        self.generator.run()
        self.assertTrue(hasattr(r.objects['hosts']['test_host_000'], 'config_files'))
        self.assertTrue('host.cfg' in r.objects['hosts']['test_host_000'].config_files['nagios'])
        self.assertTrue(hasattr(r.objects['hosts']['test_host_009'], 'config_files'))
        self.assertTrue('host.cfg' in r.objects['hosts']['test_host_009'].config_files['nagios'])
        # write hosts/apps to the filesystem
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000/host.cfg"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_009"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_009/host.cfg"))
        save_dir = os.getcwd()
        os.chdir('./var/objects/test16/dynamic')
        process = Popen(["git", "init", "."], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        process = Popen(["git", "add", "."], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        process = Popen(["git", "commit", "-a", "-m", "commit init"], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        os.chdir(save_dir)
        with io.open(hosts, 'a') as f:
            for i in range(10,20):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        self.clean_generator()
        self.setUpConfig("etc/coshsh.cfg", "test16")
        r = self.generator.get_recipe("test16")
        ds = r.get_datasource("csvshrink")
        self.generator.run()
        self.assertTrue(hasattr(r.objects['hosts']['test_host_010'], 'config_files'))
        self.assertTrue('host.cfg' in r.objects['hosts']['test_host_010'].config_files['nagios'])
        self.assertTrue(hasattr(r.objects['hosts']['test_host_019'], 'config_files'))
        self.assertTrue('host.cfg' in r.objects['hosts']['test_host_019'].config_files['nagios'])
        # write hosts/apps to the filesystem
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000/host.cfg"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_009/host.cfg"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_019"))


    def test_grow_shrink_nok(self):
        self.setUpConfig("etc/coshsh.cfg", "test16")
        r = self.generator.get_recipe("test16")
        # create 10 hosts
        # reset
        # overwrite csv with 2 hosts
        # fails because delta threshold is -10
        ds = r.get_datasource("csvshrink")
        dir = ds.dir
        name = ds.name
        hosts = os.path.join(dir, name + '_hosts.csv')
        print("hosts file is "+hosts)
        targetdir = './var/objects/test16'
        shutil.rmtree(dir, True)
        shutil.rmtree(targetdir, True)
        print("removed", dir)
        os.makedirs(dir)
        with io.open(hosts, 'w') as f:
            f.write('host_name,address,type,os,hardware,virtual,notification_period,location,department\n')
            for i in range(0,10):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)
        self.generator.run()
        self.assertTrue(hasattr(r.objects['hosts']['test_host_000'], 'config_files'))
        self.assertTrue('host.cfg' in r.objects['hosts']['test_host_000'].config_files['nagios'])
        self.assertTrue(hasattr(r.objects['hosts']['test_host_009'], 'config_files'))
        self.assertTrue('host.cfg' in r.objects['hosts']['test_host_009'].config_files['nagios'])
        # write hosts/apps to the filesystem
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000/host.cfg"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_009"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_009/host.cfg"))
        save_dir = os.getcwd()
        os.chdir('./var/objects/test16/dynamic')
        process = Popen(["git", "init", "."], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        process = Popen(["git", "add", "."], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        process = Popen(["git", "commit", "-a", "-m", "commit init"], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        os.chdir(save_dir)
        with io.open(hosts, 'w') as f:
            f.write('host_name,address,type,os,hardware,virtual,notification_period,location,department\n')
            for i in range(0, 2):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        self.clean_generator()
        self.setUpConfig("etc/coshsh.cfg", "test16")
        r = self.generator.get_recipe("test16")
        ds = r.get_datasource("csvshrink")
        self.generator.run()
        self.assertTrue(hasattr(r.objects['hosts']['test_host_000'], 'config_files'))
        self.assertTrue('host.cfg' in r.objects['hosts']['test_host_000'].config_files['nagios'])
        self.assertTrue('test_host_001' in r.objects['hosts'])
        self.assertTrue('test_host_002' not in r.objects['hosts'])
        # write hosts/apps to the filesystem
        # we violated the delta, so 0..9 must still be there
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000/host.cfg"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_009/host.cfg"))
        self.assertTrue(not os.path.exists("var/objects/test16/dynamic/hosts/test_host_019"))


