import os
import shutil
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def tearDown(self):
        super(CoshshTest, self).tearDown()
        if os.path.exists("var/objects/test20se/dynamic/targets"):
            shutil.rmtree("var/objects/test20se/dynamic/targets", True)
        if os.path.exists("var/objects/test21/dynamic/targets"):
            shutil.rmtree("var/objects/test21/dynamic/targets", True)

    def test_output(self):
        self.setUpConfig("etc/coshsh3.cfg", "test20")
        r = self.generator.get_recipe("test20")
        r.collect()
        r.assemble()
        r.render()
        os.makedirs("var/objects/test20se/dynamic/targets", 0o755)
        r.output()
        self.assertTrue(os.path.exists('var/objects/test20se/dynamic/targets/snmp_switch1.json'))
        self.assertTrue(not os.path.exists('var/objects/test20/dynamic/snmp_switch1.json'))
        self.assertTrue(os.path.exists('var/objects/test20/dynamic/hosts/switch1/os_ios_default.cfg'))

    def test_output_mixed(self):
        self.setUpConfig("etc/coshsh3.cfg", "test21")
        r = self.generator.get_recipe("test21")
        r.collect()
        r.assemble()
        r.render()
        os.makedirs("var/objects/test21/dynamic/targets", 0o755)
        r.output()
        self.assertTrue(os.path.exists('var/objects/test21/dynamic/hosts/switch1/os_ios_default.cfg'))
        self.assertTrue(os.path.exists('var/objects/test21/dynamic/targets/snmp_switch1.json'))


