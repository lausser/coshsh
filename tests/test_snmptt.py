"""Tests for SNMPTT trap-to-service mapping with NODES filtering and MIB version selection."""

import pytest
import os
import io
from tests.common_coshsh_test import CommonCoshshTest


class SnmpttTest(CommonCoshshTest):

    def tearDown(self):
        pass

    @pytest.mark.skipif(not os.path.exists(os.path.dirname(os.path.realpath(__file__))+"/recipes/testsnmptt/classes/datasource_snmptt.py"), reason="Please install a recipes/testsnmptt/classes/datasource_snmptt.py, which is part of OMD")
    def __KAKAKAKA__test_create_recipe_multiple_sources(self):
        """Disabled: integration test requiring OMD datasource_snmptt.py plugin."""
        self.setUpConfig("etc/coshsh.cfg", "testsnmptt")
        r = self.generator.get_recipe("testsnmptt")
        r.count_before_objects()
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        r.assemble()
        r.render()
        self.assertTrue(hasattr(r.objects['hosts']['test_host_0'], 'config_files'))
        self.assertIn('host.cfg', r.objects['hosts']['test_host_0'].config_files['nagios'])
        r.output()
        self.assertTrue(os.path.exists("var/objects/testsnmptt/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/testsnmptt/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/testsnmptt/dynamic/hosts/test_host_0/os_unity_traps.cfg"))
        self.assertTrue(os.path.exists("var/objects/testsnmptt/dynamic/hosts/test_host_1/os_unity_traps.cfg"))
        with io.open("var/objects/testsnmptt/dynamic/hosts/test_host_1/os_unity_traps.cfg") as f:
            os_unity_traps_cfg = f.read()
        self.assertIn('.1.3.6.1.4.1.1139.103.1.18.2.2', os_unity_traps_cfg)
        self.assertIn('.1.3.6.1.4.1.1139.103.1.18.2.3', os_unity_traps_cfg)

    @pytest.mark.skipif(not os.path.exists(os.path.dirname(os.path.realpath(__file__))+"/recipes/testsnmptt/classes/datasource_snmptt.py"), reason="Please install a recipes/testsnmptt/classes/datasource_snmptt.py, which is part of OMD")
    def test_nodes_in_snmptt(self):
        """
        Verify NODES/MODE=NEG filtering so each host gets only the correct trap service definitions.

        EVENT panHWPsFailureTrap .1.3.6.1.4.1.25461.2.1.3.2.0.913 "Status Events" CRITICAL
        NODES MODE=NEG
        NODES pa_1

        EVENT panHWPsInsertedTrap .1.3.6.1.4.1.25461.2.1.3.2.0.911 "Status Events" Normal
        NODES MODE=NEG
        NODES pa_1

        EVENT panROUTINGRoutedBGPPeerEnterEstablishedTrap .1.3.6.1.4.1.25461.2.1.3.2.0.1531 "Status Events" Normal
        RECOVERS panROUTINGRoutedBGPPeerLeftEstablishedTrap
        NODES pa_1
        NODES pa_2
        NODES pa_a pa_b

        EVENT panROUTINGRoutedBGPPeerLeftEstablishedTrap .1.3.6.1.4.1.25461.2.1.3.2.0.1532 "Status Events" Normal
        NODES pa_1 pa_2 pa_a pa_b

        only pa_1/2/a/b get the panROUTINGRoutedBGPPeer*
        only pa_1 does NOT get the panHWPs*
        """
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
            self.assertIn('host.cfg', r.objects['hosts'][pa].config_files['nagios'])
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
        self.assertNotIn('panHWPsFailureTrap', os_paloalto_traps_cfg)
        self.assertNotIn('panHWPsInsertedTrap', os_paloalto_traps_cfg)
        self.assertIn('panROUTINGRoutedBGPPeerEnterEstablishedTrap', os_paloalto_traps_cfg)
        self.assertIn('panROUTINGRoutedBGPPeerLeftEstablishedTrap', os_paloalto_traps_cfg)
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_2/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertIn('panHWPsFailureTrap', os_paloalto_traps_cfg)
        self.assertIn('panHWPsInsertedTrap', os_paloalto_traps_cfg)
        self.assertIn('panROUTINGRoutedBGPPeerEnterEstablishedTrap', os_paloalto_traps_cfg)
        self.assertIn('panROUTINGRoutedBGPPeerLeftEstablishedTrap', os_paloalto_traps_cfg)
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_3/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertIn('panHWPsFailureTrap', os_paloalto_traps_cfg)
        self.assertIn('panHWPsInsertedTrap', os_paloalto_traps_cfg)
        self.assertNotIn('panROUTINGRoutedBGPPeerEnterEstablishedTrap', os_paloalto_traps_cfg)
        self.assertNotIn('panROUTINGRoutedBGPPeerLeftEstablishedTrap', os_paloalto_traps_cfg)
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_a/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertIn('panHWPsFailureTrap', os_paloalto_traps_cfg)
        self.assertIn('panHWPsInsertedTrap', os_paloalto_traps_cfg)
        self.assertIn('panROUTINGRoutedBGPPeerEnterEstablishedTrap', os_paloalto_traps_cfg)
        self.assertIn('panROUTINGRoutedBGPPeerLeftEstablishedTrap', os_paloalto_traps_cfg)
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_b/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertIn('panHWPsFailureTrap', os_paloalto_traps_cfg)
        self.assertIn('panHWPsInsertedTrap', os_paloalto_traps_cfg)
        self.assertIn('panROUTINGRoutedBGPPeerEnterEstablishedTrap', os_paloalto_traps_cfg)
        self.assertIn('panROUTINGRoutedBGPPeerLeftEstablishedTrap', os_paloalto_traps_cfg)
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_c/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertIn('panHWPsFailureTrap', os_paloalto_traps_cfg)
        self.assertIn('panHWPsInsertedTrap', os_paloalto_traps_cfg)
        self.assertNotIn('panROUTINGRoutedBGPPeerEnterEstablishedTrap', os_paloalto_traps_cfg)
        self.assertNotIn('panROUTINGRoutedBGPPeerLeftEstablishedTrap', os_paloalto_traps_cfg)
        # and check if the long description is ok
        self.assertIn('os_paloalto_traps_PAN-TRAPS-MIB_panHWPsFailureTrap', os_paloalto_traps_cfg)

        # panConfigTrap has only NODES MODE=NEG, so it should not appear at all
        self.assertFalse('panConfigTrap' in os_paloalto_traps_cfg)

        # pa_b has version 8, all others have version 7
        # pa_b gets PAN-TRAPS-8-MIB, where the oid of EstablishedTrap is
        # .1.3.6.1.4.1.25461.2.1.3.2.0.51531 instead of
        # .1.3.6.1.4.1.25461.2.1.3.2.0.1531
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_a/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertIn('PAN-TRAPS-7-MIB', os_paloalto_traps_cfg)
        self.assertIn('_OID                            .1.3.6.1.4.1.25461.2.1.3.2.0.1531', os_paloalto_traps_cfg)
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_b/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertIn('PAN-TRAPS-8-MIB', os_paloalto_traps_cfg)
        self.assertIn('_OID                            .1.3.6.1.4.1.25461.2.1.3.2.0.51531', os_paloalto_traps_cfg)

    def test_ignored_traps(self):
        """Verify that traps marked HIDDEN in the MIB file are excluded from check_logfiles config output."""
        # PAN-TRAPS-8-MIB.snmptt
        # EVENT panBFDSessionStateChangeTrap .1.3.6.1.4.1.25461.2.1.3.2.0.3504 "Status Events" HIDDEN
        # PAN-TRAPS-7-MIB.snmptt
        # EVENT panBFDSessionStateChangeTrap .1.3.6.1.4.1.25461.2.1.3.2.0.3504 "Status Events" Normal
        # HIDDEN = completely ignore this trap
        # it will never become a service definition
        # its oid will not be checked in the check_logfiles scan
        self.setUpConfig("etc/coshsh.cfg", "testsnmptt_nodes")
        r = self.generator.get_recipe("testsnmptt_nodes")
        r.count_before_objects()
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        r.assemble()
        r.render()
        r.output()
        with io.open("etc/check_logfiles/snmptt/PAN-TRAPS-7-MIB.cfg") as f:
            check_logfiles_cfg = f.read()
        self.assertIn('panBFDSessionStateChangeTrap', check_logfiles_cfg)
        self.assertFalse('panBFDAdminDownTrap' in check_logfiles_cfg)
        with io.open("etc/check_logfiles/snmptt/PAN-TRAPS-8-MIB.cfg") as f:
            check_logfiles_cfg = f.read()
        self.assertFalse('panBFDSessionStateChangeTrap' in check_logfiles_cfg)
        self.assertIn('panBFDAdminDownTrap', check_logfiles_cfg)
# PAN-TRAP-MIB .1.3.6.1.4.1.25461.2.1.3.2.0.1531
# PAN-TRAP-X-MIB .1.3.6.1.4.1.25461.2.1.3.2.0.51531
