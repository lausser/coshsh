"""Tests for recipe delta protection — max_delta threshold enforcement on host count growth and shrinkage."""

import os
import io
import shutil
import subprocess
import coshsh
from tests.common_coshsh_test import CommonCoshshTest


class DeltaTest(CommonCoshshTest):
    _configfile = 'etc/coshsh.cfg'
    _objectsdir = "./var/objects/test1"

    def _git_commit_initial(self, objects_dir):
        """Initialise a git repo in objects_dir and make an initial commit."""
        subprocess.run(["git", "init", "."], cwd=objects_dir, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=objects_dir, capture_output=True)
        subprocess.run(["git", "commit", "-a", "-m", "commit init"], cwd=objects_dir, capture_output=True)

    def test_delta_exceeded_on_growth_aborts_new_files(self):
        """Host count growth beyond max_delta prevents new files from being written."""
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
        targetdir = './var/objects/test15'
        shutil.rmtree(dir, True)
        shutil.rmtree(targetdir, True)
        os.makedirs(dir)
        with io.open(hosts, 'w') as f:
            f.write('host_name,address,type,os,hardware,virtual,notification_period,location,department\n')
            for i in range(0, 10):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        self.generator.run()
        self.assertTrue(hasattr(r.objects['hosts']['test_host_000'], 'config_files'))
        self.assertIn('host.cfg', r.objects['hosts']['test_host_000'].config_files['nagios'])
        self.assertTrue(hasattr(r.objects['hosts']['test_host_009'], 'config_files'))
        self.assertIn('host.cfg', r.objects['hosts']['test_host_009'].config_files['nagios'])
        self.assertTrue(os.path.exists("var/objects/test15/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test15/dynamic/hosts/test_host_000"))
        self.assertTrue(os.path.exists("var/objects/test15/dynamic/hosts/test_host_000/host.cfg"))
        self.assertTrue(os.path.exists("var/objects/test15/dynamic/hosts/test_host_009"))
        self.assertTrue(os.path.exists("var/objects/test15/dynamic/hosts/test_host_009/host.cfg"))

        self._git_commit_initial('./var/objects/test15/dynamic')

        # --- second run ---
        with io.open(hosts, 'a') as f:
            for i in range(10, 20):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        self.clean_generator()
        self.setUpConfig("etc/coshsh.cfg", "test15")
        r = self.generator.get_recipe("test15")
        ds = r.get_datasource("csvgrow")

        self.generator.run()
        self.assertTrue(hasattr(r.objects['hosts']['test_host_010'], 'config_files'))
        self.assertIn('host.cfg', r.objects['hosts']['test_host_010'].config_files['nagios'])
        self.assertTrue(hasattr(r.objects['hosts']['test_host_019'], 'config_files'))
        self.assertIn('host.cfg', r.objects['hosts']['test_host_019'].config_files['nagios'])
        # write hosts/apps to the filesystem
        # we violated the delta
        self.assertTrue(os.path.exists("var/objects/test15/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test15/dynamic/hosts/test_host_000"))
        self.assertTrue(os.path.exists("var/objects/test15/dynamic/hosts/test_host_000/host.cfg"))
        self.assertTrue(os.path.exists("var/objects/test15/dynamic/hosts/test_host_009/host.cfg"))
        # the hosts 10..20 were automatically resetted and cleaned by the
        # max_delta_action
        self.assertFalse(os.path.exists("var/objects/test15/dynamic/hosts/test_host_019"))

    def test_delta_not_exceeded_when_threshold_allows_growth(self):
        """Host count growth within the negative threshold is allowed and new files are written."""
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
        targetdir = './var/objects/test16'
        shutil.rmtree(dir, True)
        shutil.rmtree(targetdir, True)
        os.makedirs(dir)
        with io.open(hosts, 'w') as f:
            f.write('host_name,address,type,os,hardware,virtual,notification_period,location,department\n')
            for i in range(0, 10):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        self.generator.run()
        self.assertTrue(hasattr(r.objects['hosts']['test_host_000'], 'config_files'))
        self.assertIn('host.cfg', r.objects['hosts']['test_host_000'].config_files['nagios'])
        self.assertTrue(hasattr(r.objects['hosts']['test_host_009'], 'config_files'))
        self.assertIn('host.cfg', r.objects['hosts']['test_host_009'].config_files['nagios'])
        # write hosts/apps to the filesystem
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000/host.cfg"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_009"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_009/host.cfg"))

        self._git_commit_initial('./var/objects/test16/dynamic')

        # --- second run ---
        with io.open(hosts, 'a') as f:
            for i in range(10, 20):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        self.clean_generator()
        self.setUpConfig("etc/coshsh.cfg", "test16")
        r = self.generator.get_recipe("test16")
        ds = r.get_datasource("csvshrink")

        self.generator.run()
        self.assertTrue(hasattr(r.objects['hosts']['test_host_010'], 'config_files'))
        self.assertIn('host.cfg', r.objects['hosts']['test_host_010'].config_files['nagios'])
        self.assertTrue(hasattr(r.objects['hosts']['test_host_019'], 'config_files'))
        self.assertIn('host.cfg', r.objects['hosts']['test_host_019'].config_files['nagios'])
        # write hosts/apps to the filesystem
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000/host.cfg"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_009/host.cfg"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_019"))

    def test_too_much_delta_boundary_exactly_at_threshold(self):
        """Datarecipient.too_much_delta() returns False when change is exactly at threshold."""
        from coshsh.datarecipient import Datarecipient
        dr = object.__new__(Datarecipient)
        dr.max_delta = (100, 100)  # positive: guards both directions
        dr.old_objects = (10, 10)
        dr.new_objects = (20, 20)  # exactly 100% increase
        # 100% change == threshold of 100 → abs(100) > 100 is False
        self.assertFalse(dr.too_much_delta())

    def test_delta_exceeded_on_shrink_restores_old_files(self):
        """Shrinkage beyond max_delta threshold keeps old files and does not write new ones."""
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
        targetdir = './var/objects/test16'
        shutil.rmtree(dir, True)
        shutil.rmtree(targetdir, True)
        os.makedirs(dir)
        with io.open(hosts, 'w') as f:
            f.write('host_name,address,type,os,hardware,virtual,notification_period,location,department\n')
            for i in range(0, 10):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        self.generator.run()
        self.assertTrue(hasattr(r.objects['hosts']['test_host_000'], 'config_files'))
        self.assertIn('host.cfg', r.objects['hosts']['test_host_000'].config_files['nagios'])
        self.assertTrue(hasattr(r.objects['hosts']['test_host_009'], 'config_files'))
        self.assertIn('host.cfg', r.objects['hosts']['test_host_009'].config_files['nagios'])
        # write hosts/apps to the filesystem
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000/host.cfg"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_009"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_009/host.cfg"))

        self._git_commit_initial('./var/objects/test16/dynamic')

        # --- second run ---
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
        self.assertIn('host.cfg', r.objects['hosts']['test_host_000'].config_files['nagios'])
        self.assertIn('test_host_001', r.objects['hosts'])
        self.assertNotIn('test_host_002', r.objects['hosts'])
        # write hosts/apps to the filesystem
        # we violated the delta, so 0..9 must still be there
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_000/host.cfg"))
        self.assertTrue(os.path.exists("var/objects/test16/dynamic/hosts/test_host_009/host.cfg"))
        self.assertFalse(os.path.exists("var/objects/test16/dynamic/hosts/test_host_019"))
