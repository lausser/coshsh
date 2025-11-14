"""Test suite for core recipe functionality.

This module tests the core recipe behavior including recipe configuration,
multiple datasource handling, git integration, max_delta settings, environment
variable substitution, and template error handling. These tests verify the
complete recipe lifecycle from collect to output.
"""

from __future__ import annotations

import io
import os
import shutil

from tests.common_coshsh_test import CommonCoshshTest


class RecipeMaxDeltaConfigurationTest(CommonCoshshTest):
    """Test suite for recipe max_delta configuration.

    This suite verifies that:
    - Default max_delta is an empty tuple
    - Single max_delta value is converted to tuple (value, value)
    - Colon-separated max_delta values create tuple with different values
    - max_delta configuration is correctly parsed and stored

    Test Configuration:
        Uses recipe: test10
        Config file: etc/coshsh.cfg

    Background:
        max_delta controls the time window for incremental updates.
        Format: single_value or min_value:max_value
    """

    def test_recipe_max_delta_defaults_to_empty_tuple(self) -> None:
        """Test that recipe max_delta defaults to empty tuple.

        When no max_delta is configured, the recipe should have
        an empty tuple as the default value.

        Expected Behavior:
            - max_delta should be ()
        """
        # Arrange & Act: Load recipe without max_delta configuration
        self.setUpConfig("etc/coshsh.cfg", "test10")
        r = self.generator.get_recipe("test10")

        # Assert: Verify default max_delta
        self.assertTrue(
            r.max_delta == (),
            "Recipe max_delta should default to empty tuple when not configured"
        )

    def test_recipe_max_delta_single_value_creates_tuple(self) -> None:
        """Test that single max_delta value creates tuple with same min and max.

        When max_delta is configured with a single value, it should be
        converted to a tuple with that value used for both min and max.

        Test Setup:
            1. Create recipe with max_delta='101'
            2. Verify tuple conversion

        Expected Behavior:
            - max_delta='101' should become (101, 101)
        """
        # Arrange: Load base config and create recipe with single max_delta
        self.setUpConfig("etc/coshsh.cfg", "test10")
        recipe = {
            'classes_dir': '/tmp',
            'objects_dir': '/tmp',
            'templates_dir': '/tmp',
            'datasources': 'datasource',
            'max_delta': '101'
        }
        self.generator.add_recipe(name='recp', **recipe)

        # Act: Get the created recipe
        r = self.generator.get_recipe('recp')

        # Assert: Verify max_delta is tuple with same values
        self.assertTrue(
            r.max_delta == (101, 101),
            "Single max_delta value should create tuple (value, value)"
        )

    def test_recipe_max_delta_colon_separated_creates_different_tuple(self) -> None:
        """Test that colon-separated max_delta creates tuple with different values.

        When max_delta is configured with colon-separated values, it should
        create a tuple with different min and max values.

        Test Setup:
            1. Create recipe with max_delta='101:202'
            2. Verify tuple conversion

        Expected Behavior:
            - max_delta='101:202' should become (101, 202)
        """
        # Arrange: Load base config and create recipe with colon-separated max_delta
        self.setUpConfig("etc/coshsh.cfg", "test10")
        recipe = {
            'classes_dir': '/tmp',
            'objects_dir': '/tmp',
            'templates_dir': '/tmp',
            'datasources': 'datasource',
            'max_delta': '101:202'
        }
        self.generator.add_recipe(name='recp', **recipe)

        # Act: Get the created recipe
        r = self.generator.get_recipe('recp')

        # Assert: Verify max_delta is tuple with different values
        self.assertTrue(
            r.max_delta == (101, 202),
            "Colon-separated max_delta values should create tuple (min, max)"
        )


class RecipeExecutionTest(CommonCoshshTest):
    """Test suite for recipe execution pipeline.

    This suite verifies that:
    - Complete recipe pipeline (collect, assemble, render, output) works
    - Multiple datasources are processed correctly
    - Configuration files are generated in correct locations
    - Git initialization works (and can be disabled)
    - Application details (filesystems) are sorted correctly
    - Template rendering produces expected content

    Test Configuration:
        Uses recipes: test10, test10nogit
        Config file: etc/coshsh.cfg
        Output directory: var/objects/test10/

    Related:
        See also: test_recipeattrs.py for attribute inheritance tests
    """

    def test_recipe_with_multiple_datasources_generates_configurations(self) -> None:
        """Test that recipe with multiple datasources generates all configurations.

        This test verifies the complete recipe execution pipeline with
        multiple datasources, ensuring all hosts and applications are
        correctly processed and output files are generated.

        Test Setup:
            1. Load recipe test10 with multiple datasources
            2. Execute full pipeline: count, cleanup, prepare, collect, assemble, render, output
            3. Verify all expected files are created
            4. Check file contents and object details

        Expected Behavior:
            - Hosts are loaded from all datasources
            - Configuration files are created for each host
            - Applications are correctly associated with hosts
            - Filesystems are sorted alphabetically
            - Git repository is initialized by default
            - MySQL applications and configs are created
            - No render errors occur

        Assertions:
            - Host objects have config_files attribute
            - Host config files are created
            - OS-specific configs are rendered
            - Application details (filesystems) are sorted
            - Git repository exists
            - MySQL configuration files exist
            - No render errors
        """
        # Arrange: Load recipe
        self.setUpConfig("etc/coshsh.cfg", "test10")
        r = self.generator.get_recipe("test10")

        # Act: Execute full recipe pipeline
        r.count_before_objects()
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        r.assemble()
        r.render()

        # Assert: Verify host objects and config files attribute
        self.assertTrue(
            hasattr(self.generator.recipes['test10'].objects['hosts']['test_host_0'], 'config_files'),
            "Host objects should have config_files attribute after rendering"
        )
        self.assertTrue(
            'host.cfg' in self.generator.recipes['test10'].objects['hosts']['test_host_0'].config_files['nagios'],
            "Host should have host.cfg in nagios config_files"
        )

        # Act: Output configurations to filesystem
        r.output()

        # Assert: Verify output directory structure
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts"),
            "Dynamic hosts directory should be created"
        )
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts/test_host_0"),
            "Host directory should be created for test_host_0"
        )
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts/test_host_0/os_linux_default.cfg"),
            "Linux OS configuration should be created for test_host_0"
        )
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg"),
            "Windows OS configuration should be created for test_host_1"
        )

        # Assert: Verify configuration file content
        with io.open("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue(
            'os_windows_default_check_' in os_windows_default_cfg,
            "Windows OS configuration should contain expected check command prefix"
        )

        # Assert: Verify filesystem details are sorted
        filesystems = self.generator.recipes['test10'].objects['applications']['test_host_1+os+windows2k8r2'].filesystems
        self.assertTrue(
            len(filesystems) == 5,
            "Windows application should have 5 filesystems"
        )
        self.assertTrue(
            [f.path for f in filesystems] == ['C', 'D', 'F', 'G', 'Z'],
            "Filesystems should be sorted alphabetically by path"
        )

        # Assert: Verify git repository initialization
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/.git"),
            "Git repository should be initialized by default (git_init=yes)"
        )

        # Assert: Verify MySQL applications and configurations
        mysql_apps = [app for app in self.generator.recipes['test10'].objects['applications'].values()
                      if "mysql" in app.__class__.__name__.lower()]
        self.assertTrue(
            len(mysql_apps) == 3,
            "Should have 3 MySQL applications"
        )

        mysql_files = []
        for mysql in [app for app in r.objects['applications'].values()
                      if "mysql" in app.__class__.__name__.lower()]:
            mysql_files.extend([mysql.host_name+"/"+cfg for cfg in mysql.config_files["nagios"].keys()])

        self.assertTrue(
            len(mysql_files) == 3,
            "Should have 3 MySQL configuration files"
        )
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts/test_host_0/app_db_mysql_intranet_default.cfg"),
            "MySQL configuration file should exist for test_host_0"
        )

        for cfg in mysql_files:
            self.assertTrue(
                os.path.exists("var/objects/test10/dynamic/hosts/"+cfg),
                f"MySQL configuration file should exist at var/objects/test10/dynamic/hosts/{cfg}"
            )

        # Assert: Verify no render errors
        self.assertTrue(
            self.generator.recipes['test10'].render_errors == 0,
            "Recipe should render without errors"
        )

    def test_recipe_with_git_disabled_does_not_create_repository(self) -> None:
        """Test that recipe with git_init=no does not create git repository.

        When git_init is explicitly set to 'no', the recipe should not
        initialize a git repository in the output directory.

        Test Setup:
            1. Load recipe test10nogit with git_init=no
            2. Execute recipe
            3. Verify .git directory does not exist

        Expected Behavior:
            - Configuration files are created normally
            - No .git directory is created
            - git_init attribute is False
        """
        # Arrange: Load recipe with git disabled
        self.setUpConfig("etc/coshsh.cfg", "test10nogit")
        r = self.generator.get_recipe("test10nogit")

        # Assert: Verify git_init is False
        self.assertFalse(
            r.git_init,
            "Recipe git_init should be False when explicitly disabled"
        )

        # Act: Execute recipe
        self.generator.run()

        # Assert: Verify configuration files exist
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg"),
            "Windows OS configuration should be created even with git disabled"
        )

        # Assert: Verify git repository was not created
        self.assertTrue(
            not os.path.exists("var/objects/test10/dynamic/.git"),
            "Git repository should NOT be created when git_init=no"
        )

    def test_recipe_environment_variable_substitution(self) -> None:
        """Test that recipe correctly substitutes environment variables.

        Recipes can use environment variables in their configuration.
        This test verifies that %VAR% patterns are correctly substituted
        with environment variable values.

        Test Setup:
            1. Set environment variables: OMD_SITE, COSHSHDIR, ZISSSSSSCHDIR
            2. Load recipe that uses these variables
            3. Verify variables are substituted in datasource config
            4. Check that new environment variables are set by recipe

        Expected Behavior:
            - Environment variables are substituted in paths
            - Recipe can set new environment variables based on config
            - Variable substitution works for multiple patterns

        Environment Variables Set:
            - THERCP: Recipe name with suffix
            - THECDIR: COSHSHDIR + subdirectory
            - THEZDIR: ZISSSSSSCHDIR + subdirectory
            - MIBDIRS: Colon-separated MIB directories
        """
        # Arrange: Set environment variables
        os.environ['OMD_SITE'] = 'sitexy'
        os.environ['COSHSHDIR'] = '/opt/coshsh'
        os.environ['ZISSSSSSCHDIR'] = '/opt/zisch'

        # Act: Load recipe that uses environment variables
        self.setUpConfig("etc/coshsh.cfg", "test7inv")
        r = self.generator.get_recipe("test7inv")
        ds = r.get_datasource("test7inv")

        # Assert: Verify environment variables were set by recipe
        self.assertTrue(
            os.environ["THERCP"] == "test7inv_xyz",
            "Recipe should set THERCP to recipe name + suffix"
        )
        self.assertTrue(
            os.environ["THECDIR"] == "/opt/coshsh/i_am_the_dir",
            "Recipe should substitute COSHSHDIR and append subdirectory"
        )
        self.assertTrue(
            os.environ["THEZDIR"] == "/opt/zisch/i_am_the_dir",
            "Recipe should substitute ZISSSSSSCHDIR and append subdirectory"
        )
        self.assertTrue(
            os.environ["MIBDIRS"] == "/usr/share/snmp/mibs:/omd/sites/sitexy/etc/coshsh/data/mibs",
            "Recipe should set MIBDIRS with substituted OMD_SITE path"
        )

    def test_recipe_handles_template_rendering_errors(self) -> None:
        """Test that recipe handles template rendering errors gracefully.

        When templates have errors, the recipe should continue processing
        other objects and track the number of render errors. Objects with
        render errors should not have their config files written.

        Test Setup:
            1. Load recipe test10tplerr with broken templates
            2. Execute full pipeline
            3. Verify that most objects render successfully
            4. Verify that objects with errors don't create config files
            5. Check render_errors count

        Expected Behavior:
            - Recipe completes without crashing
            - Objects without errors are rendered normally
            - Objects with template errors don't create config files
            - render_errors counter tracks failed renders
            - Host configurations are still created
            - MySQL applications exist but don't render

        Assertions:
            - Host objects are created
            - Host config files exist
            - MySQL applications are created (3 total)
            - MySQL config files are NOT created (due to template errors)
            - render_errors equals 3 (one per MySQL app)
        """
        # Arrange: Load recipe with template errors
        self.setUpConfig("etc/coshsh.cfg", "test10tplerr")
        r = self.generator.get_recipe("test10tplerr")

        # Act: Execute recipe pipeline
        r.count_before_objects()
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        r.assemble()
        r.render()

        # Assert: Verify host objects are created
        self.assertTrue(
            hasattr(r.objects['hosts']['test_host_0'], 'config_files'),
            "Host objects should have config_files attribute even with template errors"
        )
        self.assertTrue(
            'host.cfg' in r.objects['hosts']['test_host_0'].config_files['nagios'],
            "Host should have host.cfg in nagios config_files"
        )

        # Assert: Verify MySQL applications exist
        mysql_apps = [app for app in r.objects['applications'].values()
                      if "mysql" in app.__class__.__name__.lower()]
        self.assertTrue(
            len(mysql_apps) == 3,
            "Should have 3 MySQL applications even with template errors"
        )

        # Act: Output configurations
        r.output()

        # Assert: Verify host configurations are created
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts"),
            "Dynamic hosts directory should be created"
        )
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts/test_host_0"),
            "Host directory should be created for test_host_0"
        )
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts/test_host_0/os_linux_default.cfg"),
            "Linux OS configuration should be created for test_host_0"
        )
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg"),
            "Windows OS configuration should be created for test_host_1"
        )

        # Assert: Verify configuration file content
        with io.open("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue(
            'os_windows_default_check_' in os_windows_default_cfg,
            "Windows OS configuration should contain expected check command prefix"
        )

        # Assert: Verify filesystem details are sorted
        filesystems = r.objects['applications']['test_host_1+os+windows2k8r2'].filesystems
        self.assertTrue(
            len(filesystems) == 5,
            "Windows application should have 5 filesystems"
        )
        self.assertTrue(
            [f.path for f in filesystems] == ['C', 'D', 'F', 'G', 'Z'],
            "Filesystems should be sorted alphabetically by path"
        )

        # Assert: Verify git repository initialization
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/.git"),
            "Git repository should be initialized by default"
        )

        # Assert: Verify MySQL applications don't have config files
        self.assertTrue(
            len(mysql_apps) == 3,
            "Should still have 3 MySQL applications"
        )

        for mysql in mysql_apps:
            print(mysql.__dict__)
            self.assertTrue(
                "nagios" not in mysql.config_files,
                f"MySQL application {mysql} should not have nagios config_files due to template error"
            )

        # Assert: Verify MySQL config file is not created
        self.assertFalse(
            os.path.exists("var/objects/test10/dynamic/hosts/test_host_0/app_db_mysql_intranet_default.cfg"),
            "MySQL configuration file should NOT exist due to template errors"
        )

        # Assert: Verify render errors were tracked
        self.assertTrue(
            r.render_errors == 3,
            "Recipe should track 3 render errors (one per MySQL application)"
        )
