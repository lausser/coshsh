"""Test suite for NAGIOSCONF monitoring detail functionality.

This module tests the NAGIOSCONF monitoring detail type, which allows
dynamic injection of Nagios configuration directives for hosts and
applications via monitoring details.
"""

from __future__ import annotations

import io
import os

from coshsh.monitoringdetail import MonitoringDetail
from tests.common_coshsh_test import CommonCoshshTest


class NagiosConfigurationTest(CommonCoshshTest):
    """Test suite for NAGIOSCONF monitoring detail type.

    This suite verifies that:
    - NAGIOSCONF monitoring details can modify service configurations
    - NAGIOSCONF monitoring details can modify host configurations
    - Custom check intervals and other directives are correctly injected
    - Generated config files contain the injected directives

    NAGIOSCONF Detail Format:
        For services: host_name, app_name, app_type, NAGIOSCONF, service_name, directive, value
        For hosts: host_name, None, None, NAGIOSCONF, directive, value

    Test Configuration:
        Uses config file: etc/coshsh.cfg
        Recipe: test10
        Data: recipes/test10/
    """

    def tearDown(self) -> None:
        """Clean up after test.

        Note: Currently empty but preserved for future cleanup needs.
        """
        pass

    def test_nagiosconf_details_inject_configuration_directives(self) -> None:
        """Test that NAGIOSCONF monitoring details inject configuration directives.

        This test verifies that NAGIOSCONF monitoring details can dynamically
        add or modify Nagios configuration directives for both services and
        hosts. This is critical for allowing per-host or per-service customization
        without modifying templates.

        Test Scenario:
            1. Load a recipe with hosts and applications
            2. Add a NAGIOSCONF detail for a Windows service (check_interval=4711)
            3. Add a NAGIOSCONF detail for a host (check_interval=0815)
            4. Verify the directives appear in generated config files

        Setup:
            Creates test recipe with Linux and Windows hosts
            Adds NAGIOSCONF monitoring details for custom check intervals

        Expected Behavior:
            - Service config includes custom check_interval (4711)
            - Service config includes service description with hostname
            - Host config includes custom check_interval (0815)
            - Host config includes host name

        Assertions:
            - Config files are generated
            - Service config contains NAGIOSCONF-injected directives
            - Host config contains NAGIOSCONF-injected directives
        """
        # Arrange: Set up config and recipe
        self.setUpConfig("etc/coshsh.cfg", "test10")
        r = self.generator.get_recipe("test10")

        # Prepare target directory
        r.count_before_objects()
        r.cleanup_target_dir()
        r.prepare_target_dir()

        # Read the datasources
        r.collect()
        ds = self.generator.get_recipe("test10").get_datasource("csv10.1")
        ds.objects = r.objects

        # Find a Windows application
        win = [app for app in r.objects['applications'].values() if "windows" in app.__class__.__name__.lower()][0]

        # Act: Add NAGIOSCONF monitoring detail for service
        sci = MonitoringDetail({
            'host_name': win.host_name,
            'name': win.name,
            'type': win.type,
            'monitoring_type': 'NAGIOSCONF',
            'monitoring_0': 'os_windows_default_check_nsclient',
            'monitoring_1': 'check_interval',
            'monitoring_2': '4711',
        })
        ds.add('details', sci)

        # Act: Add NAGIOSCONF monitoring detail for host
        host = [h for h in r.objects['hosts'].values() if h.host_name == win.host_name][0]
        hci = MonitoringDetail({
            'host_name': host.host_name,
            'name': None,
            'type': None,
            'monitoring_type': 'NAGIOSCONF',
            'monitoring_1': 'check_interval',
            'monitoring_2': '0815',
        })
        ds.add('details', hci)

        # Act: Assemble and render
        r.assemble()
        r.render()

        # Assert: Verify host has config files
        self.assertTrue(
            hasattr(self.generator.recipes['test10'].objects['hosts']['test_host_0'], 'config_files'),
            "Host should have config_files attribute after rendering"
        )
        self.assertIn(
            'host.cfg',
            self.generator.recipes['test10'].objects['hosts']['test_host_0'].config_files['nagios'],
            "Host should have host.cfg in nagios config files"
        )

        # Act: Write hosts/apps to filesystem
        r.output()

        # Assert: Verify output files exist
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts"),
            "Dynamic hosts directory should be created"
        )
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts/test_host_0"),
            "test_host_0 directory should be created"
        )
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts/test_host_0/os_linux_default.cfg"),
            "Linux default config should be generated for test_host_0"
        )
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg"),
            "Windows default config should be generated for test_host_1"
        )

        # Assert: Verify NAGIOSCONF details in service config
        with io.open("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()

        self.assertIn(
            'os_windows_default_check_nsclient',
            os_windows_default_cfg,
            "Service config should contain check command name"
        )
        self.assertIn(
            'os_windows_default_check_nsclient_test_host_1',
            os_windows_default_cfg,
            "Service config should contain service description with hostname"
        )
        self.assertIn(
            '4711',
            os_windows_default_cfg,
            "Service config should contain NAGIOSCONF-injected check_interval (4711)"
        )

        # Assert: Verify NAGIOSCONF details in host config
        with io.open("var/objects/test10/dynamic/hosts/test_host_1/host.cfg") as f:
            host_cfg = f.read()

        self.assertIn(
            'test_host_1_coshsh',
            host_cfg,
            "Host config should contain host name with _coshsh suffix"
        )
        self.assertIn(
            '0815',
            host_cfg,
            "Host config should contain NAGIOSCONF-injected check_interval (0815)"
        )

