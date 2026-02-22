"""Tests for git repository initialisation and commit behaviour in recipe output directories."""
import os
import io
import shutil
from tests.common_coshsh_test import CommonCoshshTest


class GitOutputTest(CommonCoshshTest):

    def test_create_recipe_multiple_sources(self):
        """Full pipeline produces expected cfg files and initialises a git repo in the output directory."""
        self.setUpConfig("etc/coshsh.cfg", "test10")
        r = self.generator.get_recipe("test10")
        r.count_before_objects()
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        r.assemble()
        r.render()
        self.assertTrue(hasattr(r.objects['hosts']['test_host_0'], 'config_files'))
        self.assertIn('host.cfg', r.objects['hosts']['test_host_0'].config_files['nagios'])
        r.output()
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg"))
        with io.open("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertIn('os_windows_default_check_', os_windows_default_cfg)
        self.assertEqual(len(r.objects['applications']['test_host_1+os+windows2k8r2'].filesystems), 5)
        # must be sorted
        self.assertEqual(
            [f.path for f in r.objects['applications']['test_host_1+os+windows2k8r2'].filesystems],
            ['C', 'D', 'F', 'G', 'Z'],
        )
        # git_init is yes by default
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/.git"))

    def test_create_recipe_multiple_sources_no_git(self):
        """Recipe with git_init=no skips git initialisation of the output directory."""
        self.setUpConfig("etc/coshsh.cfg", "test10nogit")
        self.generator.run()
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg"))
        self.assertFalse(os.path.exists("var/objects/test10/dynamic/.git"))

    def test_no_objects_init_empty_dir(self):
        """Recipe with git_init=no and zero objects still creates the dynamic output directory."""
        # even with zero objects the output dir must exist for check_git_updates to work
        self.setUpConfig("etc/coshsh13.cfg", "test20gitno")
        super(GitOutputTest, self).tearDown()
        test20 = self.generator.recipes['test20gitno'].datarecipients[0].objects_dir
        test20prom = self.generator.recipes['test20gitno'].datarecipients[1].objects_dir
        if os.path.exists(test20prom):
            shutil.rmtree(test20prom, True)
        if os.path.exists(test20):
            shutil.rmtree(test20, True)
        r = self.generator.get_recipe("test20gitno")
        r.collect()
        r.assemble()
        r.render()
        os.makedirs(test20, 0o755)
        os.makedirs(test20prom, 0o755)
        self.assertTrue(os.path.exists(test20))
        self.assertTrue(os.path.exists(test20prom))
        r.output()
        self.assertTrue(os.path.exists(os.path.join(test20, "dynamic")))
        self.assertTrue(os.path.exists(os.path.join(test20prom, "dynamic")))
        self.assertFalse(os.path.exists(os.path.join(test20, "dynamic", ".git")))
        self.assertFalse(os.path.exists(os.path.join(test20prom, "dynamic", "targets", ".git")))

    def test_no_objects_init_empty_git(self):
        """Recipe with git_init=yes and zero objects initialises an empty git repo in the output directory."""
        self.setUpConfig("etc/coshsh13.cfg", "test20gityes")
        super(GitOutputTest, self).tearDown()
        test20 = self.generator.recipes['test20gityes'].datarecipients[0].objects_dir
        test20prom = self.generator.recipes['test20gityes'].datarecipients[1].objects_dir
        if os.path.exists(test20prom):
            shutil.rmtree(test20prom, True)
        if os.path.exists(test20):
            shutil.rmtree(test20, True)
        r = self.generator.get_recipe("test20gityes")
        r.collect()
        r.assemble()
        r.render()
        os.makedirs(test20, 0o755)
        os.makedirs(test20prom, 0o755)
        self.assertTrue(os.path.exists(test20))
        self.assertTrue(os.path.exists(test20prom))
        r.output()
        self.assertTrue(os.path.exists(os.path.join(test20, "dynamic")))
        self.assertTrue(os.path.exists(os.path.join(test20prom, "dynamic")))
        self.assertTrue(os.path.exists(os.path.join(test20, "dynamic", ".git")))
