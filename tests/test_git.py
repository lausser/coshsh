import os
import io
import shutil
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def test_create_recipe_multiple_sources(self):
        self.setUpConfig("etc/coshsh.cfg", "test10")
        r = self.generator.get_recipe("test10")
        r.count_before_objects()
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        r.assemble()
        r.render()
        self.assertTrue(hasattr(r.objects['hosts']['test_host_0'], 'config_files'))
        self.assertTrue('host.cfg' in r.objects['hosts']['test_host_0'].config_files['nagios'])
        # write hosts/apps to the filesystem
        r.output()
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg"))
        with io.open("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue('os_windows_default_check_' in os_windows_default_cfg)
        self.assertTrue(len(r.objects['applications']['test_host_1+os+windows2k8r2'].filesystems) == 5)
        # must be sorted
        self.assertTrue([f.path for f in r.objects['applications']['test_host_1+os+windows2k8r2'].filesystems] == ['C', 'D', 'F', 'G', 'Z'])
        # git_init is yes by default
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/.git"))

    def test_create_recipe_multiple_sources_no_git(self):
        self.setUpConfig("etc/coshsh.cfg", "test10nogit")
        r = self.generator.get_recipe("test10nogit")
        # remove target dir / create empty
        self.generator.run()
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg"))
        # git_init is yes by default
        self.assertTrue(not os.path.exists("var/objects/test10/dynamic/.git"))

    # wenn null objekte generiert werden, dann muss dennoch das objects_dir
    # als vollwertiges git-Repository initialisiert werden, sonst treten beim
    # check_git_updates Fehler auf
    def test_no_objects_init_empty_dir(self):
        self.setUpConfig("etc/coshsh13.cfg", "test20gitno")
        super(CoshshTest, self).tearDown()
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
        self.setUpConfig("etc/coshsh13.cfg", "test20gityes")
        super(CoshshTest, self).tearDown()
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
        #kennt kein git_init#self.assertTrue(os.path.exists(os.path.join(test20prom, "dynamic", "targets", ".git")))

