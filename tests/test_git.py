import os
import io
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

