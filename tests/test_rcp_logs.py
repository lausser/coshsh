"""Test suite for recipe logging functionality.

This module tests the logging configuration and behavior for coshsh recipes.
Tests verify that log files are created correctly in various configurations,
including default log directories, custom log directories, and OMD-specific
logging setups.
"""

from __future__ import annotations

import io
import os
import shutil

from coshsh.application import Application, GenericApplication
from coshsh.host import Host
from coshsh.monitoringdetail import MonitoringDetail
from tests.common_coshsh_test import CommonCoshshTest


class RecipeLoggingTest(CommonCoshshTest):
    """Test suite for recipe logging functionality.

    This suite verifies that:
    - Recipe logs are created in the correct directories
    - Generic applications are handled correctly
    - Default logging configuration works as expected
    - Custom log directories are respected
    - Applications without specific classes use GenericApplication

    Test Configuration:
        Uses recipes: test33, test35, test36
        Config file: etc/coshsh5.cfg
        Log directories: ./var/log/coshshlogs/, /tmp/coshsh5/

    Related:
        See also: test_recipes.py for general recipe behavior
    """

    def setUpLogfile(self) -> None:
        """Set up logging configuration for tests.

        This method configures the logging system based on recipe
        configuration or environment variables. It checks for:
        1. Explicit log_dir in config defaults section
        2. OMD_ROOT environment variable (for OMD installations)
        3. Fallback to temporary directory

        Sets up:
            - Log directory path
            - Screen logging level (DEBUG)
        """
        super(RecipeLoggingTest, self).setUp()
        if "defaults" in self.config.sections() and "log_dir" in [c[0] for c in self.config.items("defaults")]:
            log_dir = dict(self.config.items("defaults"))["log_dir"]
            log_dir = re.sub('%.*?%', coshsh.util.substenv, log_dir)
        elif 'OMD_ROOT' in os.environ:
            log_dir = os.path.join(os.environ['OMD_ROOT'], "var", "coshsh")
        else:
            log_dir = gettempdir()
        setup_logging(logdir=log_dir, scrnloglevel=logging.DEBUG)

    def test_generic_application_class_is_used_for_unknown_types(self) -> None:
        """Test that unknown application types use GenericApplication class.

        When an application type doesn't match any specific application class,
        coshsh should automatically use the GenericApplication class instead
        of failing. This test verifies this fallback behavior.

        Test Setup:
            1. Load recipe test33 configuration
            2. Create a host with standard properties
            3. Create an application with unknown type 'arschknarsch'
            4. Process through collect, assemble, render pipeline
            5. Verify GenericApplication was used

        Expected Behavior:
            - Recipe log file should be created at ./var/log/coshshlogs/coshsh_test33.log
            - Application should be created with GenericApplication class
            - Standard templates should NOT be rendered (no filesystem or port configs)
            - Basic host configuration should be generated

        Assertions:
            - Log file exists for recipe
            - Application count is correct
            - Application uses GenericApplication class
            - Host configuration file is created
            - Generic templates are not rendered
        """
        # Arrange: Set up recipe and verify logging
        self.setUpConfig("etc/coshsh5.cfg", "test33")
        r = self.generator.get_recipe("test33")
        r.update_item_class_factories()
        ds = self.generator.get_recipe("test33").get_datasource("simplesample")
        ds.objects = r.objects

        self.assertTrue(
            os.path.exists("./var/log/coshshlogs/coshsh_test33.log"),
            "Recipe log file should be created at ./var/log/coshshlogs/coshsh_test33.log"
        )

        # Arrange: Create test host and application with unknown type
        host = Host({
            'host_name': 'testhost',
            'address': '127.0.0.1',
        })
        ds.add('hosts', host)

        app = Application({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',  # Unknown type - should trigger GenericApplication
        })
        self.generator.recipes['test33'].datasources[0].add('applications', app)

        # Act: Process the recipe
        self.generator.recipes['test33'].collect()
        self.generator.recipes['test33'].assemble()
        self.generator.recipes['test33'].render()

        # Assert: Verify application was created with GenericApplication class
        self.assertTrue(
            len(self.generator.recipes['test33'].objects['applications']) == 1,
            "Should have exactly 1 application in recipe objects"
        )

        retrieved_app = list(self.generator.recipes['test33'].datasources[0].getall('applications'))[0]

        self.assertTrue(
            retrieved_app == app,
            "Retrieved application should be the same as the created application"
        )
        self.assertTrue(
            retrieved_app.__class__ == GenericApplication,
            "Unknown application type should use GenericApplication class"
        )

        # Act: Output the configuration
        self.generator.recipes['test33'].output()

        # Assert: Verify host config exists but generic templates don't
        self.assertTrue(
            os.path.exists("var/objects/test33/dynamic/hosts/testhost/host.cfg"),
            "Host configuration file should be created"
        )
        self.assertTrue(
            not os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_fs.cfg"),
            "Generic filesystem configuration should not be created for GenericApplication"
        )
        self.assertTrue(
            not os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_ports.cfg"),
            "Generic ports configuration should not be created for GenericApplication"
        )

    def test_default_logging_configuration_creates_log_file(self) -> None:
        """Test that default logging configuration creates log file.

        When no custom logging is configured, coshsh should create
        a default log file. This test verifies the default behavior.

        Test Setup:
            1. Load recipe test35 with default logging
            2. Check for default log file creation

        Expected Behavior:
            - Default log file should be created at ./var/log/coshshlogs/coshsh.log
        """
        # Arrange & Act: Set up recipe with default logging
        self.setUpConfig("etc/coshsh5.cfg", "test35")

        # Assert: Verify default log file was created
        self.assertTrue(
            os.path.exists("./var/log/coshshlogs/coshsh.log"),
            "Default coshsh log file should be created at ./var/log/coshshlogs/coshsh.log"
        )

    def test_custom_log_directory_is_respected(self) -> None:
        """Test that custom log directory configuration is respected.

        When a recipe specifies a custom log directory, coshsh should
        create log files in that directory instead of the default.

        Test Setup:
            1. Load recipe test36 with custom log directory /tmp/coshsh5/
            2. Check for log file in custom directory

        Expected Behavior:
            - Log file should be created in custom directory /tmp/coshsh5/coshsh.log
            - Custom directory should take precedence over defaults

        Note:
            The generator logs only errors, so generator-level log file
            may not always exist even when recipe logs do.
        """
        # Arrange & Act: Set up recipe with custom log directory
        self.setUpConfig("etc/coshsh5.cfg", "test36")

        # Assert: Verify log file was created in custom directory
        self.assertTrue(
            os.path.exists("/tmp/coshsh5/coshsh.log"),
            "Custom log file should be created at /tmp/coshsh5/coshsh.log"
        )
