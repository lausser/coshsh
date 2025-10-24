#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Common base class for coshsh test suite.

This module provides CommonCoshshTest, a base class for all coshsh tests.
It handles common setup/teardown operations including:
- Clearing class factories between tests
- Setting up the generator and config
- Managing test directories
- Configuring logging
"""

from __future__ import annotations

import logging
import os
import pprint
import shutil
import sys
import unittest
from pathlib import Path
from typing import List, Optional, Union

# Prevent bytecode generation in tests
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import coshsh
from coshsh.application import Application
from coshsh.configparser import CoshshConfigParser
from coshsh.contact import Contact
from coshsh.datarecipient import Datarecipient
from coshsh.datasource import Datasource
from coshsh.generator import Generator
from coshsh.host import Host
from coshsh.monitoringdetail import MonitoringDetail
from coshsh.util import setup_logging

logger = logging.getLogger('coshsh')


class CommonCoshshTest(unittest.TestCase):
    """Base class for all coshsh unit tests.

    This class provides common functionality for testing coshsh:
    - Automatic cleanup of class factories between tests
    - Setup of generator and configuration
    - Directory management for test outputs
    - Logging configuration
    - Pretty printing utilities

    Attributes:
        generator: The coshsh Generator instance
        called_from_dir: Directory from which tests were called
        tests_run_in_dir: Directory containing test files
        coshsh_base_dir: Base directory of coshsh installation
        pp: PrettyPrinter for debugging output

    Subclass Hooks:
        mySetUp(): Called early in setUp() for custom initialization
        mySetUpRm(): Called to remove directories before test
        mySetUpMk(): Called to create directories before test
        _configfile: If set, automatically loads this config file
        _objectsdir: If set, automatically creates/cleans this directory
    """

    # Test configuration
    generator: Generator
    called_from_dir: str
    tests_run_in_dir: str
    coshsh_base_dir: str
    pp: pprint.PrettyPrinter

    def print_header(self) -> None:
        """Print a formatted header showing the current test name.

        Creates a 80-character box with the test ID centered inside.
        Useful for visually separating test output.
        """
        print("#" * 80 + "\n" + "#" + " " * 78 + "#")
        print("#" + str.center(self.id(), 78) + "#")
        print("#" + " " * 78 + "#\n" + "#" * 80 + "\n")

    def setUp(self) -> None:
        """Set up the test environment before each test.

        This method:
        1. Prints a header with the test name
        2. Clears all class factories to ensure test isolation
        3. Sets up directory paths and working directory
        4. Configures Python path
        5. Creates a fresh Generator instance
        6. Sets up logging
        7. Calls custom setup hooks if defined
        8. Loads config file if _configfile is set
        9. Sets up objects directory if _objectsdir is set
        """
        self.print_header()

        # Clear class factories to ensure test isolation
        # This prevents plugins loaded in one test from affecting another
        Application.class_factory = []
        MonitoringDetail.class_factory = []
        Contact.class_factory = []
        Datasource.class_factory = []
        Datarecipient.class_factory = []

        # Set up directory paths
        self.called_from_dir = os.getcwd()
        self.tests_run_in_dir = os.path.dirname(os.path.realpath(__file__))
        self.coshsh_base_dir = os.path.dirname(self.tests_run_in_dir)

        # Change to test directory for relative path resolution
        os.chdir(self.tests_run_in_dir)

        # Configure Python path to include coshsh base directory
        if self.coshsh_base_dir not in sys.path:
            sys.path.append(self.coshsh_base_dir)

        # Remove test directory from path to avoid conflicts
        sys.path = list(set([
            p for p in sys.path
            if self.tests_run_in_dir not in os.path.realpath(p)
        ]))

        # Create fresh generator and configure logging
        self.generator = coshsh.generator.Generator()
        setup_logging(scrnloglevel=logging.DEBUG)

        # Call custom setup hook if defined
        if hasattr(self, "mySetUp"):
            getattr(self, "mySetUp")()

        # Automatically load config file if _configfile attribute is set
        if hasattr(self, "_configfile"):
            # Set defaults if not already defined
            default_recipe = getattr(self, "default_recipe", None)
            default_log_level = getattr(self, "default_log_level", "info")
            force = getattr(self, "force", False)
            safe_output = getattr(self, "safe_output", False)

            self.setUpConfig(
                self._configfile,
                default_recipe,
                default_log_level,
                force,
                safe_output
            )

        # Automatically set up objects directory if _objectsdir is set
        if hasattr(self, "_objectsdir"):
            self.setUpObjectsDir()

        # Call custom directory removal hook
        if hasattr(self, "mySetUpRm"):
            getattr(self, "mySetUpRm")()

        # Call custom directory creation hook
        if hasattr(self, "mySetUpMk"):
            getattr(self, "mySetUpMk")()

        # Set up pretty printer for debugging
        self.pp = pprint.PrettyPrinter(indent=4)


    def setUpConfig(
        self,
        configfile: str,
        default_recipe: Optional[str],
        default_log_level: str = "info",
        force: bool = False,
        safe_output: bool = False
    ) -> None:
        """Load and configure a cookbook file.

        Args:
            configfile: Path to the cookbook configuration file
            default_recipe: Name of the default recipe to use, or None for all
            default_log_level: Log level (debug, info, warning, error)
            force: Force regeneration even if output is up to date
            safe_output: Use safe output mode
        """
        self.generator.set_default_log_level(default_log_level)
        self.generator.read_cookbook(
            [configfile],
            default_recipe,
            force,
            safe_output
        )

    def setUpObjectsDir(self) -> None:
        """Set up the objects directory for test output.

        Creates/cleans the directory specified in _objectsdir attribute.
        Supports both single directory (string) and multiple directories (list).
        """
        # Ensure _objectsdir is a list
        if not isinstance(self._objectsdir, list):
            self._objectsdir = [self._objectsdir]

        # Remove and recreate each directory
        for obj_dir in self._objectsdir:
            shutil.rmtree(obj_dir, ignore_errors=True)
            os.makedirs(obj_dir, exist_ok=True)

    def tearDown(self) -> None:
        """Clean up after each test.

        This method:
        1. Removes objects directories created by recipes
        2. Removes log directories created by the generator
        3. Cleans up _objectsdir directories
        4. Restores the original working directory
        """
        # Clean up recipe output directories
        if hasattr(self, "generator"):
            for recipe in self.generator.recipes.values():
                if hasattr(recipe, "objects_dir"):
                    objects_dir = os.path.realpath(recipe.objects_dir)

                    # Only remove if it's in the test directory (safety check)
                    is_in_test_dir = objects_dir.startswith(self.tests_run_in_dir)
                    is_not_test_dir_itself = len(objects_dir) > len(self.tests_run_in_dir)

                    if is_in_test_dir and is_not_test_dir_itself:
                        shutil.rmtree(objects_dir, ignore_errors=True)

            # Clean up log directory
            if hasattr(self.generator, "log_dir"):
                shutil.rmtree(self.generator.log_dir, ignore_errors=True)

        # Clean up _objectsdir directories
        if hasattr(self, '_objectsdir'):
            if not isinstance(self._objectsdir, list):
                self._objectsdir = [self._objectsdir]

            for obj_dir in self._objectsdir:
                shutil.rmtree(obj_dir, ignore_errors=True)
                os.makedirs(obj_dir, exist_ok=True)

        # Restore original working directory
        os.chdir(self.called_from_dir)

    def clean_generator(self) -> None:
        """Reset the generator to a fresh state.

        Creates a new Generator instance and resets logging.
        Useful when you need to test multiple configurations in one test.
        """
        self.generator = coshsh.generator.Generator()
        setup_logging()

    # Helper methods for better assertions

    def assertFileExists(self, filepath: str, msg: Optional[str] = None) -> None:
        """Assert that a file exists.

        Args:
            filepath: Path to the file
            msg: Optional custom error message
        """
        if not os.path.exists(filepath):
            error_msg = msg or f"File does not exist: {filepath}"
            self.fail(error_msg)

    def assertFileContains(
        self,
        filepath: str,
        content: str,
        msg: Optional[str] = None
    ) -> None:
        """Assert that a file contains specific content.

        Args:
            filepath: Path to the file
            content: Content that should be in the file
            msg: Optional custom error message
        """
        self.assertFileExists(filepath)

        with open(filepath, 'r') as f:
            file_content = f.read()

        if content not in file_content:
            error_msg = msg or f"File {filepath} does not contain: {content}"
            self.fail(error_msg)

    def assertDictHasKey(
        self,
        dictionary: dict,
        key: str,
        msg: Optional[str] = None
    ) -> None:
        """Assert that a dictionary has a specific key.

        Args:
            dictionary: Dictionary to check
            key: Key that should exist
            msg: Optional custom error message
        """
        if key not in dictionary:
            error_msg = msg or f"Dictionary does not have key: {key}"
            self.fail(error_msg)

