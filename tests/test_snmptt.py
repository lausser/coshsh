"""Test suite for SNMPTT integration and trap handling.

This module tests the SNMPTT (SNMP Trap Translator) integration with coshsh.
Tests verify trap configuration generation, NODES filtering, MIB version
handling, and HIDDEN trap directives. SNMPTT is used to convert SNMP traps
into monitoring events.
"""

from __future__ import annotations

import io
import os

import pytest

from tests.common_coshsh_test import CommonCoshshTest


class SnmpttIntegrationTest(CommonCoshshTest):
    """Test suite for SNMPTT integration.

    This suite verifies that:
    - SNMPTT datasource processes trap configurations correctly
    - NODES directives filter traps per host
    - NODES MODE=NEG (negative mode) excludes specific hosts
    - MIB version-specific traps are handled correctly
    - HIDDEN trap directive excludes traps from configuration
    - RECOVERS directive creates recovery relationships

    Test Configuration:
        Uses recipes: testsnmptt, testsnmptt_nodes
        Config file: etc/coshsh.cfg
        Output directory: var/objects/testsnmptt/

    SNMPTT Directives:
        - EVENT: Defines a trap
        - NODES: Lists hosts that should receive this trap
        - NODES MODE=NEG: Lists hosts that should NOT receive this trap
        - RECOVERS: Defines recovery trap relationship
        - HIDDEN: Completely ignores this trap

    Related:
        Requires datasource_snmptt.py plugin (part of OMD)
    """

    @pytest.mark.skipif(
        not os.path.exists(
            os.path.dirname(os.path.realpath(__file__)) +
            "/recipes/testsnmptt/classes/datasource_snmptt.py"
        ),
        reason="Please install a recipes/testsnmptt/classes/datasource_snmptt.py, which is part of OMD"
    )
    def __KAKAKAKA__test_create_recipe_multiple_sources(self) -> None:
        """Test that SNMPTT recipe processes multiple datasources correctly.

        This test is currently disabled (prefix __KAKAKAKA__) but verifies
        basic SNMPTT functionality when enabled.

        Test Setup:
            1. Load testsnmptt recipe
            2. Execute full pipeline
            3. Verify trap configurations are created
            4. Check for specific OIDs in configuration

        Expected Behavior:
            - Host configurations are created
            - Trap configuration files exist
            - Specific trap OIDs appear in configurations

        Note:
            Test requires datasource_snmptt.py plugin which is part of OMD.
        """
        # Arrange: Load recipe
        self.setUpConfig("etc/coshsh.cfg", "testsnmptt")
        r = self.generator.get_recipe("testsnmptt")

        # Act: Execute full pipeline
        r.count_before_objects()
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        r.assemble()
        r.render()

        # Assert: Verify host objects are created
        self.assertTrue(
            hasattr(r.objects['hosts']['test_host_0'], 'config_files'),
            "Host objects should have config_files attribute"
        )
        self.assertTrue(
            'host.cfg' in r.objects['hosts']['test_host_0'].config_files['nagios'],
            "Host should have host.cfg in nagios config_files"
        )

        # Act: Output configurations
        r.output()

        # Assert: Verify trap configurations are created
        self.assertTrue(
            os.path.exists("var/objects/testsnmptt/dynamic/hosts"),
            "Dynamic hosts directory should be created"
        )
        self.assertTrue(
            os.path.exists("var/objects/testsnmptt/dynamic/hosts/test_host_0"),
            "Host directory should be created for test_host_0"
        )
        self.assertTrue(
            os.path.exists("var/objects/testsnmptt/dynamic/hosts/test_host_0/os_unity_traps.cfg"),
            "Unity traps configuration should be created for test_host_0"
        )
        self.assertTrue(
            os.path.exists("var/objects/testsnmptt/dynamic/hosts/test_host_1/os_unity_traps.cfg"),
            "Unity traps configuration should be created for test_host_1"
        )

        # Assert: Verify trap OIDs in configuration
        with io.open("var/objects/testsnmptt/dynamic/hosts/test_host_1/os_unity_traps.cfg") as f:
            os_unity_traps_cfg = f.read()
        self.assertTrue(
            '.1.3.6.1.4.1.1139.103.1.18.2.2' in os_unity_traps_cfg,
            "Unity trap OID .1.3.6.1.4.1.1139.103.1.18.2.2 should be in configuration"
        )
        self.assertTrue(
            '.1.3.6.1.4.1.1139.103.1.18.2.3' in os_unity_traps_cfg,
            "Unity trap OID .1.3.6.1.4.1.1139.103.1.18.2.3 should be in configuration"
        )

        print(r.objects["applications"]["test_host_1+os+unity"].type)
        print(r.objects["applications"]["test_host_1+os+unity"].version)

    def test_snmptt_nodes_directive_filters_traps_per_host(self) -> None:
        """Test that SNMPTT NODES directives filter traps per host correctly.

        This test verifies the complex NODES filtering logic including:
        - NODES MODE=NEG (negative filtering)
        - Multiple NODES lines for the same trap
        - RECOVERS relationships between traps

        Test Scenario:
            SNMPTT configuration contains traps with different NODES directives:

            1. panHWPsFailureTrap - NODES MODE=NEG, NODES pa_1
               (all hosts EXCEPT pa_1 get this trap)

            2. panHWPsInsertedTrap - NODES MODE=NEG, NODES pa_1
               (all hosts EXCEPT pa_1 get this trap)

            3. panROUTINGRoutedBGPPeerEnterEstablishedTrap
               RECOVERS panROUTINGRoutedBGPPeerLeftEstablishedTrap
               NODES pa_1, NODES pa_2, NODES pa_a pa_b
               (only pa_1, pa_2, pa_a, pa_b get this trap)

            4. panROUTINGRoutedBGPPeerLeftEstablishedTrap
               NODES pa_1 pa_2 pa_a pa_b
               (only these 4 hosts get this trap)

        Expected Results:
            Host    Failure  Insert  Enter  Left
            pa_1    -        -       +      +
            pa_2    +        +       +      +
            pa_3    +        +       -      -
            pa_a    +        +       +      +
            pa_b    +        +       +      +
            pa_c    +        +       -      -

        Test Setup:
            1. Load testsnmptt_nodes recipe
            2. Process all hosts (pa_1, pa_2, pa_3, pa_a, pa_b, pa_c)
            3. Verify trap configurations for each host
            4. Check MIB version-specific OIDs

        Additional Tests:
            - MIB version handling (version 7 vs version 8)
            - Different OIDs for different MIB versions
            - HIDDEN traps are completely excluded
        """
        # Arrange: Load recipe
        self.setUpConfig("etc/coshsh.cfg", "testsnmptt_nodes")
        r = self.generator.get_recipe("testsnmptt_nodes")

        # Act: Execute full pipeline
        r.count_before_objects()
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        r.assemble()
        r.render()

        # Assert: Verify all hosts have config files
        for pa in ["pa_1", "pa_2", "pa_3", "pa_a", "pa_b", "pa_c"]:
            self.assertTrue(
                hasattr(r.objects['hosts'][pa], 'config_files'),
                f"Host {pa} should have config_files attribute"
            )
            self.assertTrue(
                'host.cfg' in r.objects['hosts'][pa].config_files['nagios'],
                f"Host {pa} should have host.cfg in nagios config_files"
            )

        # Act: Output configurations
        r.output()

        # Assert: Verify trap configuration files exist for all hosts
        for pa in ["pa_1", "pa_2", "pa_3", "pa_a", "pa_b", "pa_c"]:
            self.assertTrue(
                os.path.exists(f"var/objects/testsnmptt/dynamic/hosts/{pa}/os_paloalto_traps.cfg"),
                f"PaloAlto traps configuration should exist for host {pa}"
            )

        # Assert: Verify pa_1 trap configuration (NODES MODE=NEG excludes HWPs traps)
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_1/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertTrue(
            'panHWPsFailureTrap' not in os_paloalto_traps_cfg,
            "pa_1 should NOT have panHWPsFailureTrap (excluded by NODES MODE=NEG)"
        )
        self.assertTrue(
            'panHWPsInsertedTrap' not in os_paloalto_traps_cfg,
            "pa_1 should NOT have panHWPsInsertedTrap (excluded by NODES MODE=NEG)"
        )
        self.assertTrue(
            'panROUTINGRoutedBGPPeerEnterEstablishedTrap' in os_paloalto_traps_cfg,
            "pa_1 should have panROUTINGRoutedBGPPeerEnterEstablishedTrap (included in NODES)"
        )
        self.assertTrue(
            'panROUTINGRoutedBGPPeerLeftEstablishedTrap' in os_paloalto_traps_cfg,
            "pa_1 should have panROUTINGRoutedBGPPeerLeftEstablishedTrap (included in NODES)"
        )

        # Assert: Verify pa_2 trap configuration (has all traps)
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_2/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertTrue(
            'panHWPsFailureTrap' in os_paloalto_traps_cfg,
            "pa_2 should have panHWPsFailureTrap (not excluded)"
        )
        self.assertTrue(
            'panHWPsInsertedTrap' in os_paloalto_traps_cfg,
            "pa_2 should have panHWPsInsertedTrap (not excluded)"
        )
        self.assertTrue(
            'panROUTINGRoutedBGPPeerEnterEstablishedTrap' in os_paloalto_traps_cfg,
            "pa_2 should have panROUTINGRoutedBGPPeerEnterEstablishedTrap (included in NODES)"
        )
        self.assertTrue(
            'panROUTINGRoutedBGPPeerLeftEstablishedTrap' in os_paloalto_traps_cfg,
            "pa_2 should have panROUTINGRoutedBGPPeerLeftEstablishedTrap (included in NODES)"
        )

        # Assert: Verify pa_3 trap configuration (has HWPs but not BGP traps)
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_3/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertTrue(
            'panHWPsFailureTrap' in os_paloalto_traps_cfg,
            "pa_3 should have panHWPsFailureTrap (not excluded)"
        )
        self.assertTrue(
            'panHWPsInsertedTrap' in os_paloalto_traps_cfg,
            "pa_3 should have panHWPsInsertedTrap (not excluded)"
        )
        self.assertTrue(
            'panROUTINGRoutedBGPPeerEnterEstablishedTrap' not in os_paloalto_traps_cfg,
            "pa_3 should NOT have panROUTINGRoutedBGPPeerEnterEstablishedTrap (not in NODES)"
        )
        self.assertTrue(
            'panROUTINGRoutedBGPPeerLeftEstablishedTrap' not in os_paloalto_traps_cfg,
            "pa_3 should NOT have panROUTINGRoutedBGPPeerLeftEstablishedTrap (not in NODES)"
        )

        # Assert: Verify pa_a trap configuration (has all traps)
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_a/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertTrue(
            'panHWPsFailureTrap' in os_paloalto_traps_cfg,
            "pa_a should have panHWPsFailureTrap (not excluded)"
        )
        self.assertTrue(
            'panHWPsInsertedTrap' in os_paloalto_traps_cfg,
            "pa_a should have panHWPsInsertedTrap (not excluded)"
        )
        self.assertTrue(
            'panROUTINGRoutedBGPPeerEnterEstablishedTrap' in os_paloalto_traps_cfg,
            "pa_a should have panROUTINGRoutedBGPPeerEnterEstablishedTrap (included in NODES)"
        )
        self.assertTrue(
            'panROUTINGRoutedBGPPeerLeftEstablishedTrap' in os_paloalto_traps_cfg,
            "pa_a should have panROUTINGRoutedBGPPeerLeftEstablishedTrap (included in NODES)"
        )

        # Assert: Verify pa_b trap configuration (has all traps)
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_b/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertTrue(
            'panHWPsFailureTrap' in os_paloalto_traps_cfg,
            "pa_b should have panHWPsFailureTrap (not excluded)"
        )
        self.assertTrue(
            'panHWPsInsertedTrap' in os_paloalto_traps_cfg,
            "pa_b should have panHWPsInsertedTrap (not excluded)"
        )
        self.assertTrue(
            'panROUTINGRoutedBGPPeerEnterEstablishedTrap' in os_paloalto_traps_cfg,
            "pa_b should have panROUTINGRoutedBGPPeerEnterEstablishedTrap (included in NODES)"
        )
        self.assertTrue(
            'panROUTINGRoutedBGPPeerLeftEstablishedTrap' in os_paloalto_traps_cfg,
            "pa_b should have panROUTINGRoutedBGPPeerLeftEstablishedTrap (included in NODES)"
        )

        # Assert: Verify pa_c trap configuration (has HWPs but not BGP traps)
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_c/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertTrue(
            'panHWPsFailureTrap' in os_paloalto_traps_cfg,
            "pa_c should have panHWPsFailureTrap (not excluded)"
        )
        self.assertTrue(
            'panHWPsInsertedTrap' in os_paloalto_traps_cfg,
            "pa_c should have panHWPsInsertedTrap (not excluded)"
        )
        self.assertTrue(
            'panROUTINGRoutedBGPPeerEnterEstablishedTrap' not in os_paloalto_traps_cfg,
            "pa_c should NOT have panROUTINGRoutedBGPPeerEnterEstablishedTrap (not in NODES)"
        )
        self.assertTrue(
            'panROUTINGRoutedBGPPeerLeftEstablishedTrap' not in os_paloalto_traps_cfg,
            "pa_c should NOT have panROUTINGRoutedBGPPeerLeftEstablishedTrap (not in NODES)"
        )

        # Assert: Verify service description format
        self.assertTrue(
            'os_paloalto_traps_PAN-TRAPS-MIB_panHWPsFailureTrap' in os_paloalto_traps_cfg,
            "Trap service name should include MIB name and trap name"
        )

        # Assert: Verify panConfigTrap is excluded (NODES MODE=NEG only)
        self.assertFalse(
            'panConfigTrap' in os_paloalto_traps_cfg,
            "panConfigTrap should not appear (has only NODES MODE=NEG)"
        )

        # Assert: Verify MIB version-specific OIDs
        # pa_b has version 8, all others have version 7
        # pa_b gets PAN-TRAPS-8-MIB with different OID: .1.3.6.1.4.1.25461.2.1.3.2.0.51531
        # others get PAN-TRAPS-7-MIB with OID: .1.3.6.1.4.1.25461.2.1.3.2.0.1531
        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_a/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertTrue(
            'PAN-TRAPS-7-MIB' in os_paloalto_traps_cfg,
            "pa_a (version 7) should use PAN-TRAPS-7-MIB"
        )
        self.assertTrue(
            '_OID                            .1.3.6.1.4.1.25461.2.1.3.2.0.1531' in os_paloalto_traps_cfg,
            "pa_a (version 7) should have OID ending in 1531"
        )

        with io.open("var/objects/testsnmptt/dynamic/hosts/pa_b/os_paloalto_traps.cfg") as f:
            os_paloalto_traps_cfg = f.read()
        self.assertTrue(
            'PAN-TRAPS-8-MIB' in os_paloalto_traps_cfg,
            "pa_b (version 8) should use PAN-TRAPS-8-MIB"
        )
        self.assertTrue(
            '_OID                            .1.3.6.1.4.1.25461.2.1.3.2.0.51531' in os_paloalto_traps_cfg,
            "pa_b (version 8) should have OID ending in 51531"
        )

    def test_snmptt_hidden_traps_are_excluded(self) -> None:
        """Test that HIDDEN traps are completely excluded from configuration.

        SNMPTT supports a HIDDEN severity level which means:
        - Trap should be completely ignored
        - No service definition will be created
        - OID will not be checked in check_logfiles scan

        Test Scenario:
            PAN-TRAPS-8-MIB.snmptt has:
                EVENT panBFDSessionStateChangeTrap ... HIDDEN
            PAN-TRAPS-7-MIB.snmptt has:
                EVENT panBFDSessionStateChangeTrap ... Normal

            Also testing panBFDAdminDownTrap visibility.

        Expected Behavior:
            - Version 7 MIB: panBFDSessionStateChangeTrap appears (Normal severity)
            - Version 8 MIB: panBFDSessionStateChangeTrap does NOT appear (HIDDEN)
            - panBFDAdminDownTrap appears in version 8, not in version 7

        Test Setup:
            1. Load testsnmptt_nodes recipe
            2. Generate check_logfiles configurations
            3. Verify HIDDEN traps are excluded
            4. Verify normal traps are included
        """
        # Arrange: Load recipe
        self.setUpConfig("etc/coshsh.cfg", "testsnmptt_nodes")
        r = self.generator.get_recipe("testsnmptt_nodes")

        # Act: Execute full pipeline
        r.count_before_objects()
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        r.assemble()
        r.render()
        r.output()

        # Assert: Verify PAN-TRAPS-7-MIB check_logfiles configuration
        with io.open("etc/check_logfiles/snmptt/PAN-TRAPS-7-MIB.cfg") as f:
            check_logfiles_cfg = f.read()
        self.assertTrue(
            'panBFDSessionStateChangeTrap' in check_logfiles_cfg,
            "panBFDSessionStateChangeTrap should appear in version 7 (Normal severity)"
        )
        self.assertFalse(
            'panBFDAdminDownTrap' in check_logfiles_cfg,
            "panBFDAdminDownTrap should NOT appear in version 7"
        )

        # Assert: Verify PAN-TRAPS-8-MIB check_logfiles configuration
        with io.open("etc/check_logfiles/snmptt/PAN-TRAPS-8-MIB.cfg") as f:
            check_logfiles_cfg = f.read()
        self.assertFalse(
            'panBFDSessionStateChangeTrap' in check_logfiles_cfg,
            "panBFDSessionStateChangeTrap should NOT appear in version 8 (HIDDEN severity)"
        )
        self.assertTrue(
            'panBFDAdminDownTrap' in check_logfiles_cfg,
            "panBFDAdminDownTrap should appear in version 8"
        )

    def tearDown(self) -> None:
        """Clean up test artifacts.

        Note:
            Currently no cleanup is performed. This may be intentional
            for manual inspection of test outputs.
        """
        pass
