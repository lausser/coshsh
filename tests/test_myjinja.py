import os
import io
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def test_create_recipe_check_paths(self):
        self.setUpConfig("etc/coshsh.cfg", "testjinja")
        r = self.generator.get_recipe("testjinja")
        self.generator.run()
        self.assertTrue(os.path.exists('var/objects/test4/dynamic/hosts/test_host_0/os_linux_default.cfg'))
        self.assertTrue(os.path.exists('var/objects/test4/dynamic/hosts/test_host_0/os_windows_default.cfg'))
        with io.open("var/objects/test4/dynamic/hosts/test_host_0/os_windows_kaas.cfg") as f:
            os_windows_kaas_cfg = f.read()
            self.assertTrue('os_linux.Linux' in os_windows_kaas_cfg)
            self.assertTrue('# type is red hat' in os_windows_kaas_cfg)
            self.assertTrue('# class is Linux' in os_windows_kaas_cfg)
            self.assertTrue('os_windows.Windows' in os_windows_kaas_cfg)
            self.assertTrue('# type is windows' in os_windows_kaas_cfg)
            self.assertTrue('# class is Windows' in os_windows_kaas_cfg)
            self.assertTrue("# ('red hat', 'os', 'linux')" in os_windows_kaas_cfg)
            self.assertTrue('ttype is red hat' in os_windows_kaas_cfg)
            self.assertTrue("# ('windows', 'os', 'windows')" in os_windows_kaas_cfg)
            self.assertTrue('ttype is windows' in os_windows_kaas_cfg)

