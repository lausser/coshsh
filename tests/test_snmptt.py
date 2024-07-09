import pytest
import os
import io
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    @pytest.mark.skipif(not os.path.exists(os.path.dirname(os.path.realpath(__file__))+"/recipes/testsnmptt/classes/datasource_snmptt.py"), reason="Please install a recipes/testsnmptt/classes/datasource_snmptt.py, which is part of OMD")
    def __KAKAKAKA__test_create_recipe_multiple_sources(self):
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

    @pytest.mark.skipif(not os.path.exists(os.path.dirname(os.path.realpath(__file__))+"/recipes/testsnmptt/classes/datasource_snmptt.py"), reason="Please install a recipes/testsnmptt/classes/datasource_snmptt.py, which is part of OMD")
    #
    # EVENT panHWPsFailureTrap .1.3.6.1.4.1.25461.2.1.3.2.0.913 "Status Events" CRITICAL
    # NODES MODE=NEG
    # NODES pa_1
    #
    # EVENT panHWPsInsertedTrap .1.3.6.1.4.1.25461.2.1.3.2.0.911 "Status Events" Normal
    # NODES MODE=NEG
    # NODES pa_1
    #
    # EVENT panROUTINGRoutedBGPPeerEnterEstablishedTrap .1.3.6.1.4.1.25461.2.1.3.2.0.1531 "Status Events" Normal
    # RECOVERS panROUTINGRoutedBGPPeerLeftEstablishedTrap
    # NODES pa_1
    # NODES pa_2
    # NODES pa_a pa_b
    #
    # EVENT panROUTINGRoutedBGPPeerLeftEstablishedTrap .1.3.6.1.4.1.25461.2.1.3.2.0.1532 "Status Events" Normal
    # NODES pa_1 pa_2 pa_a pa_b
    # 
    # only pa_1/2/a/b get the panROUTINGRoutedBGPPeer*
    # only pa_1 does NOT get the panHWPs*
    #
    def test_nodes_in_snmptt(self):
        self.setUpConfig("etc/coshsh.cfg", "testsnmptt_nodes")
        r = self.generator.get_recipe("testsnmptt_nodes")
        r.count_before_objects()
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        r.assemble()
        r.render()
        for pa in ["pa_1", "pa_2", "pa_3", "pa_a", "pa_b", "pa_c"]:
            self.assertTrue(hasattr(r.objects['hosts'][pa], 'config_files'))
            self.assertTrue('host.cfg' in r.objects['hosts'][pa].config_files['nagios'])
        r.output()
        for pa in ["pa_1", "pa_2", "pa_3", "pa_a", "pa_b", "pa_c"]:
            self.assertTrue(os.path.exists(f"var/objects/testsnmptt/dynamic/hosts/{pa}/os_paloalto_traps.cfg"))
        # host  Failure Insert Enter Left
        # pa_1  -       -      +     +
        # pa_2  +       +      +     +
        # pa_3  +       +      -     -
        # pa_a  +       +      +     +
        # pa_b  +       +      +     +
        # pa_c  +       +      -     -
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_1/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertTrue('panHWPsFailureTrap' not in os_paloalto_traps_cfg)
        self.assertTrue('panHWPsInsertedTrap' not in os_paloalto_traps_cfg)
        self.assertTrue('panROUTINGRoutedBGPPeerEnterEstablishedTrap' in os_paloalto_traps_cfg)
        self.assertTrue('panROUTINGRoutedBGPPeerLeftEstablishedTrap' in os_paloalto_traps_cfg)
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_2/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertTrue('panHWPsFailureTrap' in os_paloalto_traps_cfg)
        self.assertTrue('panHWPsInsertedTrap' in os_paloalto_traps_cfg)
        self.assertTrue('panROUTINGRoutedBGPPeerEnterEstablishedTrap' in os_paloalto_traps_cfg)
        self.assertTrue('panROUTINGRoutedBGPPeerLeftEstablishedTrap' in os_paloalto_traps_cfg)
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_3/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertTrue('panHWPsFailureTrap' in os_paloalto_traps_cfg)
        self.assertTrue('panHWPsInsertedTrap' in os_paloalto_traps_cfg)
        self.assertTrue('panROUTINGRoutedBGPPeerEnterEstablishedTrap' not in os_paloalto_traps_cfg)
        self.assertTrue('panROUTINGRoutedBGPPeerLeftEstablishedTrap' not in os_paloalto_traps_cfg)
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_a/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertTrue('panHWPsFailureTrap' in os_paloalto_traps_cfg)
        self.assertTrue('panHWPsInsertedTrap' in os_paloalto_traps_cfg)
        self.assertTrue('panROUTINGRoutedBGPPeerEnterEstablishedTrap' in os_paloalto_traps_cfg)
        self.assertTrue('panROUTINGRoutedBGPPeerLeftEstablishedTrap' in os_paloalto_traps_cfg)
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_b/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertTrue('panHWPsFailureTrap' in os_paloalto_traps_cfg)
        self.assertTrue('panHWPsInsertedTrap' in os_paloalto_traps_cfg)
        self.assertTrue('panROUTINGRoutedBGPPeerEnterEstablishedTrap' in os_paloalto_traps_cfg)
        self.assertTrue('panROUTINGRoutedBGPPeerLeftEstablishedTrap' in os_paloalto_traps_cfg)
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_c/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertTrue('panHWPsFailureTrap' in os_paloalto_traps_cfg)
        self.assertTrue('panHWPsInsertedTrap' in os_paloalto_traps_cfg)
        self.assertTrue('panROUTINGRoutedBGPPeerEnterEstablishedTrap' not in os_paloalto_traps_cfg)
        self.assertTrue('panROUTINGRoutedBGPPeerLeftEstablishedTrap' not in os_paloalto_traps_cfg)
        # and check if the long description is ok
        self.assertTrue('os_paloalto_traps_PAN-TRAPS-MIB_panHWPsFailureTrap' in os_paloalto_traps_cfg)

        # panConfigTrap has only NODES MODE=NEG, so it should not appear at all
        self.assertFalse('panConfigTrap' in os_paloalto_traps_cfg)

        # pa_b has version 8, all others have version 7
        # pa_b gets PAN-TRAPS-8-MIB, where the oid of EstablishedTrap is
        # .1.3.6.1.4.1.25461.2.1.3.2.0.51531 instead of
        # .1.3.6.1.4.1.25461.2.1.3.2.0.1531
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_a/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertTrue('PAN-TRAPS-7-MIB' in os_paloalto_traps_cfg)
        self.assertTrue('_OID                            .1.3.6.1.4.1.25461.2.1.3.2.0.1531' in os_paloalto_traps_cfg)
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_b/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertTrue('PAN-TRAPS-8-MIB' in os_paloalto_traps_cfg)
        self.assertTrue('_OID                            .1.3.6.1.4.1.25461.2.1.3.2.0.51531' in os_paloalto_traps_cfg)

    def tearDown(self):
        pass
# PAN-TRAP-MIB .1.3.6.1.4.1.25461.2.1.3.2.0.1531
# PAN-TRAP-X-MIB .1.3.6.1.4.1.25461.2.1.3.2.0.51531
