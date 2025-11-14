"""Test suite for timeperiod configuration handling.

This module tests the generation of Nagios timeperiod configurations from
coshsh recipes. Tests verify that timeperiod objects are created correctly
and rendered into proper configuration files.
"""

from __future__ import annotations

import os

from tests.common_coshsh_test import CommonCoshshTest


class TimeperiodConfigurationTest(CommonCoshshTest):
    """Test suite for timeperiod configuration generation.

    This suite verifies that:
    - Timeperiod objects are loaded from datasources
    - Timeperiod configurations are rendered correctly
    - Timeperiod config files are created in correct locations
    - Host objects can reference timeperiod configurations

    Test Configuration:
        Uses recipe: test10
        Config file: etc/timeperiods.cfg
        Output directory: ./var/objects/tp or var/objects/test10/
        Objects directory: ./var/objects/tp

    Timeperiods:
        Timeperiod objects define when monitoring should be active.
        They are referenced by hosts, services, and contacts.

    Related:
        See also: test_recipes.py for general configuration generation
    """

    _configfile = 'etc/timeperiods.cfg'
    _objectsdir = "./var/objects/tp"
    default_recipe = "test10"

    def print_header(self) -> None:
        """Print formatted test header to console.

        Outputs a boxed header with the test ID centered within
        80-character wide borders. Used for visual test separation
        in console output.
        """
        print("#" * 80 + "\n" + "#" + " " * 78 + "#")
        print("#" + str.center(self.id(), 78) + "#")
        print("#" + " " * 78 + "#\n" + "#" * 80 + "\n")

    def setUps(self) -> None:
        """Set up test environment for timeperiod tests.

        This method is an alternative setup (note: setUps vs setUp) that
        manually configures the test environment. Currently not used in
        active tests but kept for reference.

        Sets up:
            - Working directory
            - Config parser
            - Generator
            - Logging (DEBUG level)

        Note:
            This method uses non-standard name setUps (with 's') and is
            not called by the test framework. Tests use setUpConfig instead.
        """
        os.chdir(os.path.realpath(os.path.dirname(__file__)))
        self.config = coshsh.configparser.CoshshConfigParser()
        self.config.read('etc/timeperiods.cfg')
        self.generator = coshsh.generator.Generator()
        #setup_logging()
        setup_logging(scrnloglevel=logging.DEBUG)

    def tearDowns(self) -> None:
        """Clean up test artifacts.

        This method is an alternative tearDown (note: tearDowns vs tearDown)
        that would remove test output directories. Currently disabled.

        Note:
            This method uses non-standard name tearDowns (with 's') and is
            not called by the test framework. Cleanup is currently disabled
            to allow manual inspection of outputs.
        """
        #shutil.rmtree("./var/objects/tp", True)
        pass

    def test_timeperiod_configuration_is_generated_correctly(self) -> None:
        """Test that timeperiod configurations are generated correctly.

        This test verifies the complete pipeline for generating timeperiod
        configurations, from loading datasources through rendering and
        outputting configuration files.

        Test Setup:
            1. Load recipe test10 with timeperiod datasource
            2. Execute full pipeline: count, cleanup, prepare, collect, assemble, render
            3. Verify timeperiod objects are created
            4. Output configurations
            5. Verify timeperiod files exist in correct locations

        Expected Behavior:
            - Host object has config_files attribute after rendering
            - host.cfg exists in config_files
            - Dynamic hosts directory is created
            - Host directory exists for the timeperiod dummy host
            - Timeperiod configuration file is created

        Special Host:
            monops_tp_cmd_dummy_host: A dummy host used to hold timeperiod
            configurations in the Nagios/Naemon configuration structure.

        Output Structure:
            var/objects/test10/
                dynamic/
                    hosts/
                        monops_tp_cmd_dummy_host/
                            timeperiods_monops.cfg

        Assertions:
            - Host objects have config_files attribute
            - Host has host.cfg in nagios config_files
            - Dynamic hosts directory exists
            - Dummy host directory exists
            - Timeperiod configuration file exists
        """
        # Arrange: Load recipe with timeperiod configuration
        self.setUpConfig("etc/timeperiods.cfg", "test10")
        r = self.generator.get_recipe("test10")

        # Act: Execute recipe pipeline
        r.count_before_objects()
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        r.assemble()
        r.render()

        # Assert: Verify host objects are created with config files
        self.assertTrue(
            hasattr(r.objects['hosts']['monops_tp_cmd_dummy_host'], 'config_files'),
            "Timeperiod dummy host should have config_files attribute after rendering"
        )
        self.assertTrue(
            'host.cfg' in r.objects['hosts']['monops_tp_cmd_dummy_host'].config_files['nagios'],
            "Timeperiod dummy host should have host.cfg in nagios config_files"
        )

        # Act: Output configurations to filesystem
        self.generator.recipes['test10'].output()

        # Assert: Verify output directory structure
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts"),
            "Dynamic hosts directory should be created"
        )
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts/monops_tp_cmd_dummy_host"),
            "Timeperiod dummy host directory should be created"
        )
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts//monops_tp_cmd_dummy_host/timeperiods_monops.cfg"),
            "Timeperiod configuration file should be created at correct path"
        )
