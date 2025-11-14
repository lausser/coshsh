"""Test suite for logging functionality.

This module tests the Coshsh logging system which provides both screen
and file logging with configurable log levels.
"""

from __future__ import annotations

import logging
import os
import shutil

from coshsh.util import setup_logging
from tests.common_coshsh_test import CommonCoshshTest


class LoggingTest(CommonCoshshTest):
    """Test suite for Coshsh logging configuration and output.

    This suite verifies that:
    - Logging can be configured with custom log files and directories
    - Log levels can be set independently for screen and file output
    - Log messages are written to the correct log files
    - Log level filtering works correctly (DEBUG vs INFO vs WARNING)
    - Recipe processing generates appropriate log entries

    Test Configuration:
        Uses test recipe: test4
        Configuration file: etc/coshsh.cfg
        Log directory: var/log/

    Context:
        Coshsh uses Python's logging module with custom configuration.
        Different log levels can be set for console output (screen) and
        file output (text). This allows for verbose file logs while
        keeping console output clean.
    """

    def tearDown(self) -> None:
        """Clean up after logging tests.

        Outputs:
            Prints a blank line for test output formatting.
        """
        print()

    def test_logging_configuration_and_level_filtering(self) -> None:
        """Test that logging setup works with correct level filtering.

        Verifies that the setup_logging() utility function correctly
        configures logging with:
        - Custom log file names
        - Custom log directories
        - Different log levels for screen vs file output
        - Proper filtering based on log levels

        Test Setup:
            - Cleans and recreates var/log directory
            - First call: Custom config with DEBUG screen, INFO file
            - Second call: Default config with INFO screen level
            - Creates logger named 'zishsh'
            - Logs messages at WARNING, INFO, and DEBUG levels

        Expected Behavior:
            - Log file is created at var/log/zishsh.log
            - WARNING messages appear in file
            - INFO messages appear in file
            - DEBUG messages do NOT appear in file (filtered by INFO level)

        Assertions:
            - Log file exists at expected path
            - Log file contains WARNING messages
            - Log file contains INFO messages
            - Log file does NOT contain DEBUG messages (level filtering works)
        """
        # Arrange: Clean and prepare log directory
        shutil.rmtree("./var/log", True)
        os.makedirs("./var/log")

        # Configure logging with custom settings
        setup_logging(
            logfile="zishsh.log",
            logdir="./var/log",
            scrnloglevel=logging.DEBUG,
            txtloglevel=logging.INFO
        )

        # Reconfigure with default settings (screen level INFO)
        setup_logging(logdir="./var/log", scrnloglevel=logging.INFO)

        # Act: Create logger and log messages at different levels
        logger = logging.getLogger('zishsh')

        # Debug output: print logger configuration
        print(logger.__dict__)
        print()
        for handler in logger.handlers:
            print(handler.__dict__)
            print()

        # Log messages at different levels
        logger.warning("i warn you")
        logger.info("i inform you")
        logger.debug("i spam you")

        # Assert: Verify log file was created
        self.assertTrue(
            os.path.exists("./var/log/zishsh.log"),
            "Log file should be created at ./var/log/zishsh.log"
        )

        # Read log file content
        with open('./var/log/zishsh.log') as log_file:
            log_content = log_file.read()

        # Assert: Verify log level filtering
        self.assertTrue(
            "WARNING" in log_content,
            "Log file should contain WARNING level messages"
        )
        self.assertTrue(
            "INFO" in log_content,
            "Log file should contain INFO level messages"
        )
        self.assertTrue(
            "DEBUG" not in log_content,
            "Log file should NOT contain DEBUG messages when txtloglevel=INFO"
        )

    def test_recipe_processing_generates_log_entries(self) -> None:
        """Test that recipe processing writes to the Coshsh log file.

        Verifies that when a recipe is executed via generator.run(), log
        messages are written to the coshsh.log file including information
        about processed hosts.

        Test Setup:
            - Loads recipe 'test4' from etc/coshsh.cfg
            - Runs full generator pipeline
            - Processes hosts through collect/assemble/render/output

        Expected Behavior:
            - Host config files are generated correctly
            - coshsh.log file is created
            - Log contains entries about processed hosts

        Assertions:
            - Host has config_files attribute
            - host.cfg exists in config_files
            - All expected output directories are created
            - All expected config files are generated
            - Config files contain expected content
            - coshsh.log file exists
            - Log file contains hostname (showing recipe was logged)
        """
        # Arrange: Set up recipe configuration
        self.setUpConfig("etc/coshsh.cfg", "test4")
        recipe = self.generator.get_recipe("test4")

        # Act: Run full generator pipeline
        self.generator.run()

        # Assert: Verify recipe processing results
        self.assertTrue(
            hasattr(recipe.objects['hosts']['test_host_0'], 'config_files'),
            "Host should have config_files attribute after processing"
        )
        self.assertTrue(
            'host.cfg' in recipe.objects['hosts']['test_host_0'].config_files['nagios'],
            "Host should have host.cfg in Nagios config files"
        )

        # Verify output directory structure
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts"),
            "Hosts output directory should be created"
        )
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"),
            "Host-specific directory should be created"
        )

        # Verify output config files exist
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"),
            "Linux application config should be generated"
        )
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg"),
            "Windows application config should be generated"
        )

        # Verify config file content
        with open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue(
            'os_windows_default_check_unittest' in os_windows_default_cfg,
            "Windows config should contain os_windows_default_check_unittest"
        )

        # Assert: Verify logging output
        self.assertTrue(
            os.path.exists("./var/log/coshsh.log"),
            "Coshsh log file should be created during recipe processing"
        )

        # Read log file content
        with open('./var/log/coshsh.log') as log_file:
            coshsh_log = log_file.read()

        self.assertTrue(
            "test_host_0" in coshsh_log,
            "Log file should contain entries about processed host 'test_host_0'"
        )
