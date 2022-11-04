import os
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def test_create_recipe_collect(self):
        self.setUpConfig("etc/coshsh.cfg", "test11")
        r = self.generator.get_recipe("test11")
        self.generator.run()
        self.assertTrue(os.path.exists('var/objects/test11/dynamic/hosts/test_host_0/nrpe_os_windows_fs.conf'))
        self.assertTrue(os.path.exists('var/objects/test11/dynamic/hosts/test_host_0/os_windows_fs.cfg'))

