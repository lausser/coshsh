"""Test suite for Git integration functionality.

This module tests the Git repository initialization and management features
that Coshsh uses to track changes in generated configuration files.
"""

from __future__ import annotations

import os
import shutil

from tests.common_coshsh_test import CommonCoshshTest


class GitIntegrationTest(CommonCoshshTest):
    """Test suite for Git repository initialization in output directories.

    This suite verifies that:
    - Git repositories are initialized in output directories when enabled
    - Git initialization can be disabled via configuration
    - Git repositories are created even with zero objects (empty output)
    - Multiple output directories can have independent Git repos
    - Git initialization works with multiple data recipients

    Test Configuration:
        Uses test recipes: test10, test10nogit, test20gitno, test20gityes
        Configuration files: etc/coshsh.cfg, etc/coshsh13.cfg
        Output directories: var/objects/test10, var/objects/test20*

    Related:
        See also: Git update tracking tests in test_git_updates.py
    """

    def test_recipe_creates_git_repo_in_output_directory(self) -> None:
        """Test that recipe output directory is initialized as Git repo.

        By default, Coshsh initializes output directories as Git repositories
        to track configuration changes. This test verifies the basic Git
        initialization behavior.

        Test Setup:
            - Recipe 'test10' with multiple datasources
            - Loads hosts from CSV files
            - Processes through full recipe pipeline

        Expected Behavior:
            - Configuration files are generated for all hosts
            - Windows filesystems are loaded and sorted correctly
            - Git repository (.git directory) is created in output directory

        Assertions:
            - Host objects have config_files attribute
            - host.cfg file exists in config_files
            - Output directories are created
            - Windows host config exists
            - Windows config contains expected content
            - 5 filesystems are loaded for Windows host
            - Filesystems are sorted alphabetically
            - .git directory exists (git_init=yes is default)
        """
        # Arrange: Set up recipe with Git initialization (default)
        self.setUpConfig("etc/coshsh.cfg", "test10")
        recipe = self.generator.get_recipe("test10")

        # Act: Process recipe through full pipeline
        recipe.count_before_objects()
        recipe.cleanup_target_dir()
        recipe.prepare_target_dir()
        recipe.collect()
        recipe.assemble()
        recipe.render()
        recipe.output()

        # Assert: Verify configuration generation
        self.assertTrue(
            hasattr(recipe.objects['hosts']['test_host_0'], 'config_files'),
            "Host should have config_files attribute after rendering"
        )
        self.assertTrue(
            'host.cfg' in recipe.objects['hosts']['test_host_0'].config_files['nagios'],
            "Host should have host.cfg in Nagios config files"
        )
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts"),
            "Hosts output directory should be created"
        )
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts/test_host_0"),
            "Host-specific directory should be created"
        )
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts/test_host_0/os_linux_default.cfg"),
            "Linux host config should be generated"
        )
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg"),
            "Windows host config should be generated"
        )

        # Verify Windows config content
        with open("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue(
            'os_windows_default_check_' in os_windows_default_cfg,
            "Windows config should contain os_windows_default_check_ directives"
        )

        # Verify filesystems are loaded and sorted
        self.assertTrue(
            len(recipe.objects['applications']['test_host_1+os+windows2k8r2'].filesystems) == 5,
            "Windows application should have exactly 5 filesystems loaded"
        )
        self.assertTrue(
            [f.path for f in recipe.objects['applications']['test_host_1+os+windows2k8r2'].filesystems] == ['C', 'D', 'F', 'G', 'Z'],
            "Filesystems should be sorted alphabetically"
        )

        # Assert: Verify Git repository is initialized (default behavior)
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/.git"),
            "Git repository should be initialized when git_init=yes (default)"
        )

    def test_recipe_without_git_initialization(self) -> None:
        """Test that Git initialization can be disabled in recipe config.

        When git_init is explicitly set to 'no' in the recipe configuration,
        no Git repository should be created in the output directory.

        Test Setup:
            - Recipe 'test10nogit' with git_init=no
            - Processes same data as test10 but without Git

        Expected Behavior:
            - Configuration files are generated normally
            - NO .git directory is created

        Assertions:
            - Windows host config exists (normal processing works)
            - .git directory does NOT exist
        """
        # Arrange: Set up recipe with git_init=no
        self.setUpConfig("etc/coshsh.cfg", "test10nogit")
        recipe = self.generator.get_recipe("test10nogit")

        # Act: Run full generator pipeline
        self.generator.run()

        # Assert: Verify config generation but no Git repo
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg"),
            "Config files should still be generated when git_init=no"
        )
        self.assertTrue(
            not os.path.exists("var/objects/test10/dynamic/.git"),
            "Git repository should NOT be initialized when git_init=no"
        )

    def test_empty_recipe_creates_directory_without_git(self) -> None:
        """Test that empty recipes create directories without Git when disabled.

        When a recipe generates zero objects but git_init=no, the output
        directory structure should still be created but without Git
        initialization. This ensures directory structure is consistent.

        Test Setup:
            - Recipe 'test20gitno' with git_init=no
            - Two data recipients (Nagios and Prometheus formats)
            - Empty datasources (no objects generated)
            - Manually creates output directories

        Expected Behavior:
            - Output directories are created
            - NO Git repositories are initialized

        Assertions:
            - Both output directories exist
            - Neither directory has .git subdirectory
        """
        # Arrange: Set up recipe with no Git and clean directories
        self.setUpConfig("etc/coshsh13.cfg", "test20gitno")
        super(GitIntegrationTest, self).tearDown()

        test20 = self.generator.recipes['test20gitno'].datarecipients[0].objects_dir
        test20prom = self.generator.recipes['test20gitno'].datarecipients[1].objects_dir

        if os.path.exists(test20prom):
            shutil.rmtree(test20prom, True)
        if os.path.exists(test20):
            shutil.rmtree(test20, True)

        recipe = self.generator.get_recipe("test20gitno")

        # Act: Process empty recipe and create directories
        recipe.collect()
        recipe.assemble()
        recipe.render()
        os.makedirs(test20, 0o755)
        os.makedirs(test20prom, 0o755)
        recipe.output()

        # Assert: Verify directories exist but no Git repos
        self.assertTrue(
            os.path.exists(test20),
            "Nagios output directory should exist"
        )
        self.assertTrue(
            os.path.exists(test20prom),
            "Prometheus output directory should exist"
        )
        self.assertTrue(
            os.path.exists(os.path.join(test20, "dynamic")),
            "Nagios dynamic subdirectory should exist"
        )
        self.assertTrue(
            os.path.exists(os.path.join(test20prom, "dynamic")),
            "Prometheus dynamic subdirectory should exist"
        )
        self.assertFalse(
            os.path.exists(os.path.join(test20, "dynamic", ".git")),
            "Nagios directory should NOT have Git repo when git_init=no"
        )
        self.assertFalse(
            os.path.exists(os.path.join(test20prom, "dynamic", "targets", ".git")),
            "Prometheus directory should NOT have Git repo when git_init=no"
        )

    def test_empty_recipe_creates_git_repositories_when_enabled(self) -> None:
        """Test that empty recipes create Git repos when git_init=yes.

        Even when a recipe generates zero objects, if git_init=yes (default),
        Git repositories must be initialized in the output directories. This
        is critical for check_git_updates to work correctly - empty repos
        prevent errors when checking for updates.

        Test Setup:
            - Recipe 'test20gityes' with git_init=yes
            - Two data recipients (Nagios and Prometheus formats)
            - Empty datasources (no objects generated)
            - Manually creates output directories

        Expected Behavior:
            - Output directories are created
            - Git repositories are initialized in appropriate locations
            - Even empty directories have proper Git structure

        Assertions:
            - Both output directories exist
            - Nagios directory has .git subdirectory
            - Note: Prometheus targets may not have git_init support
        """
        # Arrange: Set up recipe with Git enabled and clean directories
        self.setUpConfig("etc/coshsh13.cfg", "test20gityes")
        super(GitIntegrationTest, self).tearDown()

        test20 = self.generator.recipes['test20gityes'].datarecipients[0].objects_dir
        test20prom = self.generator.recipes['test20gityes'].datarecipients[1].objects_dir

        if os.path.exists(test20prom):
            shutil.rmtree(test20prom, True)
        if os.path.exists(test20):
            shutil.rmtree(test20, True)

        recipe = self.generator.get_recipe("test20gityes")

        # Act: Process empty recipe and create directories
        recipe.collect()
        recipe.assemble()
        recipe.render()
        os.makedirs(test20, 0o755)
        os.makedirs(test20prom, 0o755)
        recipe.output()

        # Assert: Verify directories and Git repos exist
        self.assertTrue(
            os.path.exists(test20),
            "Nagios output directory should exist"
        )
        self.assertTrue(
            os.path.exists(test20prom),
            "Prometheus output directory should exist"
        )
        self.assertTrue(
            os.path.exists(os.path.join(test20, "dynamic")),
            "Nagios dynamic subdirectory should exist"
        )
        self.assertTrue(
            os.path.exists(os.path.join(test20prom, "dynamic")),
            "Prometheus dynamic subdirectory should exist"
        )
        self.assertTrue(
            os.path.exists(os.path.join(test20, "dynamic", ".git")),
            "Nagios directory should have Git repo when git_init=yes, "
            "even with zero objects (prevents check_git_updates errors)"
        )
        # Note: Prometheus targets directory doesn't support git_init
        # self.assertTrue(os.path.exists(os.path.join(test20prom, "dynamic", "targets", ".git")))
