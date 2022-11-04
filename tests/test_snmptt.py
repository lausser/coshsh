import pytest
import os
import io
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    @pytest.mark.skipif(not os.path.exists(os.path.dirname(os.path.realpath(__file__))+"/recipes/testsnmptt/classes/datasource_snmptt.py"), reason="Please install a recipes/testsnmptt/classes/datasource_snmptt.py, which is part of OMD")
    def test_create_recipe_multiple_sources(self):
        self.setUpConfig("etc/coshsh.cfg", "testsnmptt")
        r = self.generator.get_recipe("testsnmptt")
        r.count_before_objects()
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        r.assemble()
        r.render()
        self.assertTrue(hasattr(r.objects['hosts']['test_host_0'], 'config_files'))
        self.assertTrue('host.cfg' in r.objects['hosts']['test_host_0'].config_files['nagios'])
        r.output()
        self.assertTrue(os.path.exists("var/objects/testsnmptt/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/testsnmptt/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/testsnmptt/dynamic/hosts/test_host_0/os_unity_traps.cfg"))
        self.assertTrue(os.path.exists("var/objects/testsnmptt/dynamic/hosts/test_host_1/os_unity_traps.cfg"))
        with io.open("var/objects/testsnmptt/dynamic/hosts/test_host_1/os_unity_traps.cfg") as f:
            os_unity_traps_cfg = f.read()
        self.assertTrue('.1.3.6.1.4.1.1139.103.1.18.2.2' in os_unity_traps_cfg)
        self.assertTrue('.1.3.6.1.4.1.1139.103.1.18.2.3' in os_unity_traps_cfg)
        print(r.objects["applications"]["test_host_1+os+unity"].type)
        print(r.objects["applications"]["test_host_1+os+unity"].version)

