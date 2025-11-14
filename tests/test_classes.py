"""Test suite for class loading, factories, and recipe configuration.

This module tests the core coshsh class loading and factory system:
- Recipe path configuration (classes_path, templates_path)
- Class factory creation and updating
- Datasource factory configuration
- Environment variable substitution in paths
- Plugin loading and instantiation
- Recipe workflow (collect, assemble, render, output)
- Jinja2 template environment setup
- Error handling and datasource availability
"""

from __future__ import annotations

import os
import io
import coshsh
from tests.common_coshsh_test import CommonCoshshTest


class ClassLoadingTest(CommonCoshshTest):
    """Test suite for class loading and recipe configuration.

    This test suite verifies the core coshsh class loading system:
    - Recipe path configuration (classes, templates)
    - Class factory creation and management
    - Datasource factory configuration
    - Environment variable substitution
    - Plugin discovery and loading
    - Complete recipe workflow execution
    - Jinja2 template environment configuration

    The class loading system is critical for coshsh's extensibility,
    allowing custom plugins for hosts, applications, and datasources.

    Test Configuration:
        Uses test recipes: test4, test4a, test4b, test5, test7, test8
        Config files: etc/coshsh.cfg
        Test datasources: simplesample, csvsample, envdirds

    Related:
        See coshsh/generator.py for recipe management
        See coshsh/recipe.py for class factory logic
        See coshsh/datasource.py for datasource factories
    """

    def test_recipe_paths_configured_correctly(self) -> None:
        """Test that recipe paths are configured correctly from config file.

        Each recipe should have its classes_path and templates_path configured
        correctly based on the recipe configuration. The Jinja2 template loader
        should also be initialized with the correct search paths.

        Test Setup:
            1. Load configuration with two recipes: test4 and test5
            2. Retrieve both recipes
            3. Verify path configuration for each

        Expected Behavior:
            test4:
                - classes_path: ./recipes/test4/classes
                - templates_path: recipes/test4/templates
                - Jinja2 search path: recipes/test4/templates

            test5:
                - classes_path: ./recipes/test5/classes
                - templates_path: ./recipes/test5/templates
                - Jinja2 search path: ./recipes/test5/templates
                - Custom Jinja2 filters and tests should be loaded

        Assertions:
            - All path configurations match expected values
            - Jinja2 environment has custom filters and tests
        """
        # Arrange & Act: Load configuration with multiple recipes
        self.setUpConfig("etc/coshsh.cfg", "test4,test5")

        recipe_test4 = self.generator.get_recipe("test4")
        recipe_test5 = self.generator.get_recipe("test5")

        # Assert: Verify test4 paths
        self.assertEqual(
            os.path.abspath(recipe_test4.classes_path[0]),
            os.path.abspath('./recipes/test4/classes'),
            "test4 classes_path should point to recipes/test4/classes"
        )
        self.assertEqual(
            os.path.abspath(recipe_test4.templates_path[0]),
            os.path.abspath('recipes/test4/templates'),
            "test4 templates_path should point to recipes/test4/templates"
        )
        self.assertEqual(
            os.path.abspath(recipe_test4.jinja2.loader.searchpath[0]),
            os.path.abspath('recipes/test4/templates'),
            "test4 Jinja2 loader search path should include templates directory"
        )

        # Assert: Verify test5 paths
        self.assertEqual(
            os.path.abspath(recipe_test5.classes_path[0]),
            os.path.abspath('./recipes/test5/classes'),
            "test5 classes_path should point to recipes/test5/classes"
        )
        self.assertEqual(
            os.path.abspath(recipe_test5.templates_path[0]),
            os.path.abspath('./recipes/test5/templates'),
            "test5 templates_path should point to recipes/test5/templates"
        )
        self.assertEqual(
            os.path.abspath(recipe_test5.jinja2.loader.searchpath[0]),
            os.path.abspath('./recipes/test5/templates'),
            "test5 Jinja2 loader search path should include templates directory"
        )

        # Assert: Verify Jinja2 environment has custom filters and tests
        self.assertIn(
            're_match', recipe_test5.jinja2.env.tests,
            "Jinja2 environment should have custom 're_match' test"
        )
        self.assertIn(
            'service', recipe_test5.jinja2.env.filters,
            "Jinja2 environment should have custom 'service' filter"
        )

    def test_datasource_class_factory_creates_custom_datasources(self) -> None:
        """Test that datasource class factories create custom datasource classes.

        The class factory system should allow creating custom datasource
        classes with additional attributes and methods specific to the recipe.

        Test Setup:
            1. Load test4 recipe configuration
            2. Get simplesample datasource
            3. Verify custom attributes exist
            4. Create csvsample datasource from config
            5. Verify configuration values

        Expected Behavior:
            - simplesample datasource has custom 'only_the_test_simplesample' attribute
            - csvsample datasource has correct 'dir' configuration
            - Factory pattern allows extending base datasource classes

        Assertions:
            - simplesample has custom attribute
            - csvsample has correct directory path
        """
        # Arrange & Act: Load configuration and get datasource
        self.setUpConfig("etc/coshsh.cfg", "test4")
        datasource = self.generator.get_recipe("test4").get_datasource("simplesample")

        # Assert: Verify custom datasource attribute
        self.assertTrue(
            hasattr(datasource, 'only_the_test_simplesample'),
            "simplesample datasource should have custom 'only_the_test_simplesample' attribute"
        )

        # Arrange: Configure and create csvsample datasource
        self.generator.cookbook.set("datasource_CSVSAMPLE", "name", "csvsample")
        csvsample_config = self.generator.cookbook.items("datasource_CSVSAMPLE")
        csvsample_ds = coshsh.datasource.Datasource(**dict(csvsample_config))

        # Assert: Verify datasource configuration
        self.assertEqual(
            csvsample_ds.dir, "./recipes/test1/data",
            "csvsample datasource should have correct data directory configured"
        )

    def test_recipe_substitutes_environment_variables_in_paths(self) -> None:
        """Test that recipe configuration substitutes environment variables.

        The configuration system should support environment variable substitution
        using %VAR% syntax in paths. This allows flexible deployment configurations.

        Test Setup:
            1. Set environment variables COSHSHDIR and ZISSSSSSCHDIR
            2. Load test7 recipe which uses %COSHSHDIR% and %ZISSSSSSCHDIR%
            3. Verify paths were substituted correctly

        Expected Behavior:
            - %COSHSHDIR% in datasource.dir is replaced with /opt/coshsh
            - %COSHSHDIR% and %ZISSSSSSCHDIR% in classes_path are replaced
            - Resulting paths contain actual environment variable values

        Assertions:
            - Datasource directory path has substituted variable
            - classes_path entries have substituted variables
        """
        # Arrange: Set environment variables
        os.environ['COSHSHDIR'] = '/opt/coshsh'
        os.environ['ZISSSSSSCHDIR'] = '/opt/zisch'

        # Act: Load configuration that uses environment variables
        self.setUpConfig("etc/coshsh.cfg", "test7")
        recipe_test7 = self.generator.get_recipe("test7")
        datasource = recipe_test7.get_datasource("envdirds")

        # Assert: Verify environment variable substitution in datasource
        self.assertEqual(
            datasource.dir, "/opt/coshsh/recipes/test7/data",
            "Datasource directory should have %COSHSHDIR% substituted with /opt/coshsh"
        )

        # Assert: Verify environment variable substitution in classes_path
        self.assertEqual(
            recipe_test7.classes_path[0:2],
            ['/opt/coshsh/recipes/test7/classes', '/opt/zisch/tmp'],
            "classes_path should have environment variables substituted"
        )

    def test_datasource_reads_data_and_applies_custom_attributes(self) -> None:
        """Test that datasource reads data and custom class attributes are applied.

        When a datasource reads data, the created objects (hosts, applications)
        should be instances of custom classes with custom attributes defined
        in the recipe's class factories.

        Test Setup:
            1. Load test4 recipe configuration
            2. Create simplesample datasource
            3. Read data into objects collection
            4. Verify custom attributes on created objects

        Expected Behavior:
            - Datasource has custom attributes
            - Reading datasource creates Host and Application objects
            - Created objects have custom attributes from class factories:
              * Host: my_host = True
              * Linux app: test4_linux = True
              * Windows app: test4_windows = True

        Assertions:
            - Datasource has custom attribute
            - Host has custom my_host attribute
            - First application has test4_linux attribute
            - Second application has test4_windows attribute
        """
        # Arrange: Load configuration and create datasource
        self.setUpConfig("etc/coshsh.cfg", "test4")
        recipe_test4 = self.generator.get_recipe("test4")

        self.generator.cookbook.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        config = self.generator.cookbook.items("datasource_SIMPLESAMPLE")
        datasource = coshsh.datasource.Datasource(**dict(config))

        # Verify datasource has custom attribute
        self.assertTrue(
            hasattr(datasource, 'only_the_test_simplesample'),
            "Datasource should have custom attribute from factory"
        )

        # Act: Read data from datasource
        objects = recipe_test4.objects
        datasource.read(objects=objects)

        # Assert: Verify custom attributes on created objects
        self.assertTrue(
            objects['hosts']['test_host_0'].my_host == True,
            "Host object should have custom 'my_host' attribute set to True"
        )

        applications = list(objects['applications'].values())

        self.assertTrue(
            applications[0].test4_linux == True,
            "First application should have custom 'test4_linux' attribute"
        )

        self.assertTrue(
            applications[1].test4_windows == True,
            "Second application should have custom 'test4_windows' attribute"
        )


    def test_multiple_class_factories_apply_different_attributes(self) -> None:
        """Test that multiple class factories can apply different attributes.

        When a recipe has multiple class paths, custom classes from all paths
        should be loaded, and their attributes should be applied correctly
        based on application type matching.

        Test Setup:
            1. Load test4a recipe (has multiple class paths)
            2. Create and read simplesample datasource
            3. Verify different applications get different custom attributes

        Expected Behavior:
            - Host gets custom my_host attribute
            - Windows application gets test4_windows attribute
            - Red Hat application gets mycorp_linux attribute
            - Different class factories apply based on type matching

        Assertions:
            - Host has my_host attribute
            - Windows application has test4_windows attribute
            - Red Hat application has mycorp_linux attribute
        """
        # Arrange: Load configuration with multiple class factories
        self.setUpConfig("etc/coshsh.cfg", "test4a")

        self.generator.cookbook.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        config = self.generator.cookbook.items("datasource_SIMPLESAMPLE")
        datasource = coshsh.datasource.Datasource(**dict(config))

        # Verify datasource has custom attribute
        self.assertTrue(
            hasattr(datasource, 'only_the_test_simplesample'),
            "Datasource should have custom attribute from factory"
        )

        # Act: Read data from datasource
        objects = self.generator.recipes['test4a'].objects
        datasource.read(objects=objects)

        # Assert: Verify custom attributes from multiple factories
        self.assertTrue(
            objects['hosts']['test_host_0'].my_host == True,
            "Host should have custom 'my_host' attribute"
        )

        self.assertTrue(
            objects['applications']['test_host_0+os+windows'].test4_windows == True,
            "Windows application should have 'test4_windows' attribute from test4 factory"
        )

        self.assertTrue(
            objects['applications']['test_host_0+os+red hat'].mycorp_linux == True,
            "Red Hat application should have 'mycorp_linux' attribute from alternate factory"
        )

    def test_complete_recipe_workflow_generates_configuration_files(self) -> None:
        """Test complete recipe workflow from data reading to file output.

        This integration test verifies the entire coshsh workflow:
        collect -> assemble -> render -> output

        Test Setup:
            1. Configure test4 recipe with simplesample datasource
            2. Prepare target directory
            3. Execute complete workflow
            4. Verify generated files

        Expected Behavior:
            Collect phase:
                - Reads data from datasources

            Assemble phase:
                - Assigns applications to hosts
                - Creates object relationships

            Render phase:
                - Processes Jinja2 templates
                - Attaches config_files to objects
                - May have some render errors (intentional for testing)

            Output phase:
                - Writes configuration files to filesystem
                - Creates directory structure
                - Files contain expected content

        Assertions:
            - Host has config_files attribute after render
            - host.cfg is in config_files
            - Output directory structure exists
            - Configuration files are created
            - Files contain expected content
            - Render errors are tracked correctly
        """
        # Arrange: Set up recipe and datasource
        self.setUpConfig("etc/coshsh.cfg", "test4")
        recipe_test4 = self.generator.get_recipe("test4")

        self.generator.cookbook.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        config = self.generator.cookbook.items("datasource_SIMPLESAMPLE")
        recipe_test4.add_datasource(**dict(config))

        # Prepare target directory
        recipe_test4.count_before_objects()
        recipe_test4.cleanup_target_dir()
        recipe_test4.prepare_target_dir()

        # Act: Execute complete recipe workflow
        # Collect: Read data from datasources
        recipe_test4.collect()

        # Assemble: Assign applications to hosts
        recipe_test4.assemble()

        # Render: Process templates and generate configuration content
        recipe_test4.render()

        # Assert: Verify render phase results
        self.assertTrue(
            hasattr(recipe_test4.objects['hosts']['test_host_0'], 'config_files'),
            "Host should have 'config_files' attribute after rendering"
        )

        self.assertIn(
            'host.cfg',
            recipe_test4.objects['hosts']['test_host_0'].config_files['nagios'],
            "Host config_files should contain 'host.cfg'"
        )

        # Act: Output - Write files to filesystem
        recipe_test4.output()

        # Assert: Verify file system output
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts"),
            "Dynamic hosts directory should be created"
        )

        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"),
            "test_host_0 directory should be created"
        )

        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"),
            "Linux OS configuration file should be generated"
        )

        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg"),
            "Windows OS configuration file should be generated"
        )

        # Assert: Verify file content
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()

        self.assertIn(
            'os_windows_default_check_unittest',
            os_windows_default_cfg,
            "Windows config should contain expected check directive"
        )

        # Assert: Verify render errors are tracked
        # Note: os_windows_kaas template intentionally fails due to jinja neighbor_applications_as_tuple
        self.assertEqual(
            recipe_test4.render_errors, 1,
            "Recipe should have 1 render error from os_windows_kaas template"
        )


    def test_recipe_workflow_with_alternative_configuration(self) -> None:
        """Test recipe workflow with alternative configuration (test4b).

        This test verifies that the recipe workflow works correctly with
        different configurations. Test4b is similar to test4 but may have
        different template or class configurations.

        Test Setup:
            1. Configure test4b recipe
            2. Execute complete workflow without adding datasource explicitly
            3. Verify configuration files are generated

        Expected Behavior:
            - Recipe processes successfully with test4b configuration
            - All workflow phases complete without critical errors
            - Configuration files are generated correctly
            - No render errors (unlike test4)

        Assertions:
            - Host has config_files after rendering
            - host.cfg is present in config_files
            - Output directory structure exists
            - Configuration files are created
            - Files contain expected content
        """
        # Arrange: Set up recipe with alternative configuration
        self.setUpConfig("etc/coshsh.cfg", "test4b")
        recipe_test4b = self.generator.get_recipe("test4b")

        self.generator.cookbook.set("datasource_SIMPLESAMPLE", "name", "simplesample")

        # Prepare target directory
        recipe_test4b.count_before_objects()
        recipe_test4b.cleanup_target_dir()
        recipe_test4b.prepare_target_dir()

        # Act: Execute complete recipe workflow
        recipe_test4b.collect()
        recipe_test4b.assemble()
        recipe_test4b.render()

        # Assert: Verify render phase results
        self.assertTrue(
            hasattr(recipe_test4b.objects['hosts']['test_host_0'], 'config_files'),
            "Host should have 'config_files' attribute after rendering"
        )

        self.assertIn(
            'host.cfg',
            recipe_test4b.objects['hosts']['test_host_0'].config_files["nagios"],
            "Host config_files should contain 'host.cfg'"
        )

        # Act: Write configuration files
        recipe_test4b.output()

        # Assert: Verify file system output
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts"),
            "Dynamic hosts directory should be created"
        )

        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"),
            "test_host_0 directory should be created"
        )

        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"),
            "Linux OS configuration file should be generated"
        )

        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg"),
            "Windows OS configuration file should be generated"
        )

        # Assert: Verify file content
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()

        self.assertIn(
            'os_windows_default_check_unittest',
            os_windows_default_cfg,
            "Windows config should contain expected check directive"
        )

    def test_datasource_handshake_raises_exception_when_not_current(self) -> None:
        """Test that datasource raises DatasourceNotCurrent when handshake fails.

        Some datasources implement a handshake mechanism to check if they
        are current/available before reading data. When the handshake fails,
        the datasource should raise DatasourceNotCurrent exception.

        Test Setup:
            1. Load test8 recipe with handshake datasource
            2. Attempt to read from datasource
            3. Verify exception is raised
            4. Verify recipe.collect() fails gracefully

        Expected Behavior:
            - Reading datasource directly raises DatasourceNotCurrent
            - Recipe.collect() returns False (collection failed)
            - Recipe continues to assemble phase (graceful handling)
            - No crash or unhandled exception

        Assertions:
            - ds.read() raises DatasourceNotCurrent exception
            - Exception class name matches expected
            - recipe.collect() returns False
        """
        # Arrange: Load configuration with handshake datasource
        self.setUpConfig("etc/coshsh.cfg", "test8")
        recipe_test8 = self.generator.get_recipe("test8")
        datasource = recipe_test8.get_datasource("handsh")

        # Act & Assert: Verify datasource raises exception
        exception_raised = False
        exception_class = None

        try:
            hosts, applications, contacts, contactgroups, appdetails, dependencies, bps = datasource.read()
        except Exception as exp:
            exception_raised = True
            exception_class = exp.__class__.__name__

        self.assertTrue(
            exception_raised,
            "Datasource should raise exception when handshake fails"
        )

        self.assertEqual(
            exception_class, "DatasourceNotCurrent",
            "Exception should be DatasourceNotCurrent when handshake fails"
        )

        # Act: Attempt to collect with failing datasource
        collection_success = recipe_test8.collect()

        # Assert: Verify collection fails gracefully
        self.assertFalse(
            collection_success,
            "Recipe.collect() should return False when datasource is not current"
        )

        # Act: Verify recipe can continue to assemble phase
        # This should not crash even though collection failed
        recipe_test8.assemble()



if __name__ == '__main__':
    unittest.main()


