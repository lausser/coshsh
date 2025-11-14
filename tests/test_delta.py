"""Test suite for host delta monitoring and threshold enforcement.

This module tests the delta monitoring functionality that tracks changes in
the number of hosts between recipe runs and enforces thresholds to prevent
accidental mass deletions or additions of hosts.
"""

from __future__ import annotations

import io
import os
import shutil
from subprocess import PIPE, STDOUT, Popen

import coshsh
from tests.common_coshsh_test import CommonCoshshTest


class HostDeltaMonitoringTest(CommonCoshshTest):
    """Test suite for host delta monitoring and threshold enforcement.

    This test suite verifies that:
    - Delta monitoring detects significant changes in host count
    - Max delta thresholds prevent accidental mass host changes
    - Growing host counts within threshold are accepted
    - Shrinking host counts exceeding threshold are rejected
    - Delta violations trigger configured actions (reset, cleanup)
    - Git integration tracks host configuration changes

    Test Configuration:
        Uses test recipes in tests/recipes/test15/ and test16/
        Config file: etc/coshsh.cfg
        Output directories: ./var/objects/test15, ./var/objects/test16

    Delta Scenarios Tested:
        - test15 (csvgrow): Growing hosts exceeding positive delta threshold
        - test16 (csvshrink): Shrinking hosts exceeding negative delta threshold
        - test16 (csvshrink): Growing hosts within threshold (allowed)

    Delta Actions:
        - max_delta_action: What to do when delta threshold is exceeded
        - Usually involves resetting/cleaning output to prevent bad changes
    """

    _configfile = 'etc/coshsh.cfg'
    _objectsdir = "./var/objects/test1"

    def test_growing_hosts_exceeds_delta_threshold_triggers_reset(self) -> None:
        """Test that growing host count exceeding delta threshold triggers reset action.

        This test verifies the delta monitoring functionality when hosts grow
        beyond the configured threshold. When too many hosts are added in a
        single run, the system should detect this and trigger the configured
        max_delta_action to prevent accidental mass additions.

        Setup:
            - Creates initial CSV with 10 hosts
            - Runs recipe and commits to git
            - Adds 10 more hosts to CSV (100% growth)
            - Re-runs recipe

        Expected Behavior:
            - Initial 10 hosts are created successfully
            - Git tracks the initial configuration
            - Adding 10 more hosts exceeds the delta threshold
            - max_delta_action prevents new hosts from being written
            - Only original 10 hosts remain in output directory
            - New hosts (10-19) are not written to filesystem

        Assertions:
            - Initial hosts (0-9) have config files
            - Initial hosts have rendered configuration
            - After delta violation, original hosts still exist
            - New hosts (10-19) are rendered but not written to disk
            - New host directories don't exist in output
        """
        # Arrange: Set up configuration and prepare test environment
        self.setUpConfig("etc/coshsh.cfg", "test15")
        recipe = self.generator.get_recipe("test15")

        # Get datasource configuration
        datasource = recipe.get_datasource("csvgrow")
        dir = datasource.dir
        name = datasource.name
        hosts = os.path.join(dir, name + '_hosts.csv')
        print("hosts file is " + hosts)

        targetdir = './var/objects/test15'

        # Clean up any existing test data
        shutil.rmtree(dir, True)
        shutil.rmtree(targetdir, True)
        print("removed", dir)
        os.makedirs(dir)

        # Act: Create initial CSV with 10 hosts
        with io.open(hosts, 'w') as f:
            f.write('host_name,address,type,os,hardware,virtual,notification_period,location,department\n')
            for i in range(0, 10):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        # Run recipe with initial 10 hosts
        self.generator.run()

        # Assert: Verify initial hosts were created
        self.assertTrue(
            hasattr(recipe.objects['hosts']['test_host_000'], 'config_files'),
            "Initial host test_host_000 should have config_files attribute"
        )
        self.assertTrue(
            'host.cfg' in recipe.objects['hosts']['test_host_000'].config_files['nagios'],
            "Initial host test_host_000 should have rendered host.cfg"
        )
        self.assertTrue(
            hasattr(recipe.objects['hosts']['test_host_009'], 'config_files'),
            "Initial host test_host_009 should have config_files attribute"
        )
        self.assertTrue(
            'host.cfg' in recipe.objects['hosts']['test_host_009'].config_files['nagios'],
            "Initial host test_host_009 should have rendered host.cfg"
        )
        self.assertTrue(
            os.path.exists("var/objects/test15/dynamic/hosts"),
            "Output hosts directory should exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test15/dynamic/hosts/test_host_000"),
            "Initial host test_host_000 directory should exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test15/dynamic/hosts/test_host_000/host.cfg"),
            "Initial host test_host_000 config file should exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test15/dynamic/hosts/test_host_009"),
            "Initial host test_host_009 directory should exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test15/dynamic/hosts/test_host_009/host.cfg"),
            "Initial host test_host_009 config file should exist"
        )

        # Initialize git repository to track changes
        save_dir = os.getcwd()
        os.chdir('./var/objects/test15/dynamic')
        process = Popen(["git", "init", "."], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        process = Popen(["git", "add", "."], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        process = Popen(["git", "commit", "-a", "-m", "commit init"], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        os.chdir(save_dir)

        # Act: Add 10 more hosts (exceeding delta threshold)
        with io.open(hosts, 'a') as f:
            for i in range(10, 20):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        # Reset generator and run again with more hosts
        self.clean_generator()
        self.setUpConfig("etc/coshsh.cfg", "test15")
        recipe = self.generator.get_recipe("test15")
        datasource = recipe.get_datasource("csvgrow")

        self.generator.run()

        # Assert: Verify new hosts were rendered but not written (delta violation)
        self.assertTrue(
            hasattr(recipe.objects['hosts']['test_host_010'], 'config_files'),
            "New host test_host_010 should be rendered in memory"
        )
        self.assertTrue(
            'host.cfg' in recipe.objects['hosts']['test_host_010'].config_files['nagios'],
            "New host test_host_010 should have rendered host.cfg in memory"
        )
        self.assertTrue(
            hasattr(recipe.objects['hosts']['test_host_019'], 'config_files'),
            "New host test_host_019 should be rendered in memory"
        )
        self.assertTrue(
            'host.cfg' in recipe.objects['hosts']['test_host_019'].config_files['nagios'],
            "New host test_host_019 should have rendered host.cfg in memory"
        )

        # Assert: Verify delta violation prevented writing new hosts
        self.assertTrue(
            os.path.exists("var/objects/test15/dynamic/hosts"),
            "Output hosts directory should still exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test15/dynamic/hosts/test_host_000"),
            "Original host test_host_000 should still exist after delta violation"
        )
        self.assertTrue(
            os.path.exists("var/objects/test15/dynamic/hosts/test_host_000/host.cfg"),
            "Original host test_host_000 config should still exist after delta violation"
        )
        self.assertTrue(
            os.path.exists("var/objects/test15/dynamic/hosts/test_host_009/host.cfg"),
            "Original host test_host_009 config should still exist after delta violation"
        )
        self.assertTrue(
            not os.path.exists("var/objects/test15/dynamic/hosts/test_host_019"),
            "New host test_host_019 should not be written due to delta violation (max_delta_action triggered)"
        )

    def test_growing_hosts_within_threshold_succeeds(self) -> None:
        """Test that growing host count within threshold is accepted.

        This test verifies that when hosts grow but stay within the configured
        negative delta threshold, the changes are accepted and written to disk.
        The threshold is configured to allow growth (negative threshold) but
        prevent shrinkage.

        Setup:
            - Creates initial CSV with 10 hosts
            - Runs recipe and commits to git
            - Adds 10 more hosts to CSV (100% growth)
            - Re-runs recipe with threshold that allows growth

        Expected Behavior:
            - Initial 10 hosts are created successfully
            - Git tracks the initial configuration
            - Adding 10 more hosts is within the threshold (growth allowed)
            - All 20 hosts are written to filesystem
            - New hosts appear in output directory

        Assertions:
            - Initial hosts (0-9) have config files
            - Initial hosts are written to disk
            - New hosts (10-19) have config files
            - New hosts (10-19) are written to disk
            - All host directories exist in output
        """
        # Arrange: Set up configuration with negative threshold (allows growth)
        self.setUpConfig("etc/coshsh.cfg", "test16")
        recipe = self.generator.get_recipe("test16")

        # Get datasource configuration
        datasource = recipe.get_datasource("csvshrink")
        dir = datasource.dir
        name = datasource.name
        hosts = os.path.join(dir, name + '_hosts.csv')
        print("hosts file is " + hosts)

        targetdir = './var/objects/test16'

        # Clean up any existing test data
        shutil.rmtree(dir, True)
        shutil.rmtree(targetdir, True)
        print("removed", dir)
        os.makedirs(dir)

        # Act: Create initial CSV with 10 hosts
        with io.open(hosts, 'w') as f:
            f.write('host_name,address,type,os,hardware,virtual,notification_period,location,department\n')
            for i in range(0, 10):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        # Run recipe with initial 10 hosts
        self.generator.run()

        # Assert: Verify initial hosts were created
        self.assertTrue(
            hasattr(recipe.objects['hosts']['test_host_000'], 'config_files'),
            "Initial host test_host_000 should have config_files attribute"
        )
        self.assertTrue(
            'host.cfg' in recipe.objects['hosts']['test_host_000'].config_files['nagios'],
            "Initial host test_host_000 should have rendered host.cfg"
        )
        self.assertTrue(
            hasattr(recipe.objects['hosts']['test_host_009'], 'config_files'),
            "Initial host test_host_009 should have config_files attribute"
        )
        self.assertTrue(
            'host.cfg' in recipe.objects['hosts']['test_host_009'].config_files['nagios'],
            "Initial host test_host_009 should have rendered host.cfg"
        )
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic/hosts"),
            "Output hosts directory should exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic/hosts/test_host_000"),
            "Initial host test_host_000 directory should exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic/hosts/test_host_000/host.cfg"),
            "Initial host test_host_000 config file should exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic/hosts/test_host_009"),
            "Initial host test_host_009 directory should exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic/hosts/test_host_009/host.cfg"),
            "Initial host test_host_009 config file should exist"
        )

        # Initialize git repository to track changes
        save_dir = os.getcwd()
        os.chdir('./var/objects/test16/dynamic')
        process = Popen(["git", "init", "."], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        process = Popen(["git", "add", "."], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        process = Popen(["git", "commit", "-a", "-m", "commit init"], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        os.chdir(save_dir)

        # Act: Add 10 more hosts (within negative threshold - growth allowed)
        with io.open(hosts, 'a') as f:
            for i in range(10, 20):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        # Reset generator and run again
        self.clean_generator()
        self.setUpConfig("etc/coshsh.cfg", "test16")
        recipe = self.generator.get_recipe("test16")
        datasource = recipe.get_datasource("csvshrink")

        self.generator.run()

        # Assert: Verify new hosts were rendered and written (within threshold)
        self.assertTrue(
            hasattr(recipe.objects['hosts']['test_host_010'], 'config_files'),
            "New host test_host_010 should have config_files attribute"
        )
        self.assertTrue(
            'host.cfg' in recipe.objects['hosts']['test_host_010'].config_files['nagios'],
            "New host test_host_010 should have rendered host.cfg"
        )
        self.assertTrue(
            hasattr(recipe.objects['hosts']['test_host_019'], 'config_files'),
            "New host test_host_019 should have config_files attribute"
        )
        self.assertTrue(
            'host.cfg' in recipe.objects['hosts']['test_host_019'].config_files['nagios'],
            "New host test_host_019 should have rendered host.cfg"
        )

        # Assert: Verify all hosts were written to disk (growth allowed)
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic/hosts"),
            "Output hosts directory should exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic/hosts/test_host_000"),
            "Original host test_host_000 directory should exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic/hosts/test_host_000/host.cfg"),
            "Original host test_host_000 config file should exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic/hosts/test_host_009/host.cfg"),
            "Original host test_host_009 config file should exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic/hosts/test_host_019"),
            "New host test_host_019 directory should exist (growth within threshold)"
        )

    def test_shrinking_hosts_exceeds_threshold_triggers_reset(self) -> None:
        """Test that shrinking host count exceeding threshold triggers reset action.

        This test verifies the delta monitoring functionality when hosts shrink
        beyond the configured threshold. When too many hosts are removed in a
        single run, the system should detect this and trigger the configured
        max_delta_action to prevent accidental mass deletions.

        Setup:
            - Creates initial CSV with 10 hosts
            - Runs recipe and commits to git
            - Reduces CSV to 2 hosts (80% reduction)
            - Re-runs recipe with negative threshold of -10

        Expected Behavior:
            - Initial 10 hosts are created successfully
            - Git tracks the initial configuration
            - Reducing to 2 hosts exceeds the shrink threshold
            - max_delta_action prevents deletion of existing hosts
            - Original 10 hosts remain in output directory
            - Reduced host set is not written to filesystem

        Assertions:
            - Initial hosts (0-9) are created
            - Reduced host set (0-1) is rendered but not written
            - Original hosts (0-9) still exist on disk after delta violation
            - New configuration is not written due to threshold violation
        """
        # Arrange: Set up configuration with shrink threshold
        self.setUpConfig("etc/coshsh.cfg", "test16")
        recipe = self.generator.get_recipe("test16")

        # Get datasource configuration
        datasource = recipe.get_datasource("csvshrink")
        dir = datasource.dir
        name = datasource.name
        hosts = os.path.join(dir, name + '_hosts.csv')
        print("hosts file is " + hosts)

        targetdir = './var/objects/test16'

        # Clean up any existing test data
        shutil.rmtree(dir, True)
        shutil.rmtree(targetdir, True)
        print("removed", dir)
        os.makedirs(dir)

        # Act: Create initial CSV with 10 hosts
        with io.open(hosts, 'w') as f:
            f.write('host_name,address,type,os,hardware,virtual,notification_period,location,department\n')
            for i in range(0, 10):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        # Run recipe with initial 10 hosts
        self.generator.run()

        # Assert: Verify initial hosts were created
        self.assertTrue(
            hasattr(recipe.objects['hosts']['test_host_000'], 'config_files'),
            "Initial host test_host_000 should have config_files attribute"
        )
        self.assertTrue(
            'host.cfg' in recipe.objects['hosts']['test_host_000'].config_files['nagios'],
            "Initial host test_host_000 should have rendered host.cfg"
        )
        self.assertTrue(
            hasattr(recipe.objects['hosts']['test_host_009'], 'config_files'),
            "Initial host test_host_009 should have config_files attribute"
        )
        self.assertTrue(
            'host.cfg' in recipe.objects['hosts']['test_host_009'].config_files['nagios'],
            "Initial host test_host_009 should have rendered host.cfg"
        )
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic/hosts"),
            "Output hosts directory should exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic/hosts/test_host_000"),
            "Initial host test_host_000 directory should exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic/hosts/test_host_000/host.cfg"),
            "Initial host test_host_000 config file should exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic/hosts/test_host_009"),
            "Initial host test_host_009 directory should exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic/hosts/test_host_009/host.cfg"),
            "Initial host test_host_009 config file should exist"
        )

        # Initialize git repository to track changes
        save_dir = os.getcwd()
        os.chdir('./var/objects/test16/dynamic')
        process = Popen(["git", "init", "."], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        process = Popen(["git", "add", "."], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        process = Popen(["git", "commit", "-a", "-m", "commit init"], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        os.chdir(save_dir)

        # Act: Reduce hosts to 2 (exceeding shrink threshold of -10)
        with io.open(hosts, 'w') as f:
            f.write('host_name,address,type,os,hardware,virtual,notification_period,location,department\n')
            for i in range(0, 2):
                f.write('test_host_%03d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,versandverpackung\n' % i)

        # Reset generator and run again
        self.clean_generator()
        self.setUpConfig("etc/coshsh.cfg", "test16")
        recipe = self.generator.get_recipe("test16")
        datasource = recipe.get_datasource("csvshrink")

        self.generator.run()

        # Assert: Verify reduced host set was rendered
        self.assertTrue(
            hasattr(recipe.objects['hosts']['test_host_000'], 'config_files'),
            "Reduced set host test_host_000 should be rendered in memory"
        )
        self.assertTrue(
            'host.cfg' in recipe.objects['hosts']['test_host_000'].config_files['nagios'],
            "Reduced set host test_host_000 should have rendered host.cfg"
        )
        self.assertTrue(
            'test_host_001' in recipe.objects['hosts'],
            "Reduced set host test_host_001 should be in memory"
        )
        self.assertTrue(
            'test_host_002' not in recipe.objects['hosts'],
            "Host test_host_002 should not be in memory (only 2 hosts in reduced set)"
        )

        # Assert: Verify delta violation prevented writing (original 10 hosts still exist)
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic/hosts"),
            "Output hosts directory should still exist"
        )
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic/hosts/test_host_000"),
            "Original host test_host_000 should still exist after delta violation"
        )
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic/hosts/test_host_000/host.cfg"),
            "Original host test_host_000 config should still exist after delta violation"
        )
        self.assertTrue(
            os.path.exists("var/objects/test16/dynamic/hosts/test_host_009/host.cfg"),
            "Original host test_host_009 should still exist after delta violation (shrink prevented)"
        )
        self.assertTrue(
            not os.path.exists("var/objects/test16/dynamic/hosts/test_host_019"),
            "Host test_host_019 should not exist (was never created)"
        )
