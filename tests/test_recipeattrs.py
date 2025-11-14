"""Test suite for recipe attribute handling and configuration.

This module tests how recipe attributes are defined, inherited, and passed
through the coshsh system. Tests verify datasource attribute substitution
in templates, data recipient configuration, and attribute inheritance from
recipes to their components.
"""

from __future__ import annotations

import io
import os
import urllib

from coshsh.application import Application
from coshsh.host import Host
from tests.common_coshsh_test import CommonCoshshTest


class RecipeAttributesTest(CommonCoshshTest):
    """Test suite for recipe attribute handling.

    This suite verifies that:
    - Recipe attributes are correctly passed to data recipients
    - Data recipients can override recipe-level attributes
    - Datasource attributes are available in templates
    - Special characters in datasource attributes are properly encoded
    - Implicit default data recipients work correctly

    Test Configuration:
        Uses recipes: test12, test12a, oracleds2tpl
        Config file: etc/coshsh.cfg

    Test Scenarios:
        - objects_dir inheritance and override
        - Datasource attributes in Jinja2 templates
        - RFC3986 URL encoding for special characters
        - Multiple data recipients with different configurations

    Related:
        See also: test_recipes.py for general recipe behavior
    """

    def test_recipe_attributes_handed_down_to_data_recipients(self) -> None:
        """Test that recipe attributes are handed down to data recipients.

        This test verifies that data recipients inherit attributes from
        their parent recipe, but can also override them with their own
        configuration. Specifically tests objects_dir inheritance.

        Test Setup:
            1. Load recipe test12 with multiple data recipients
            2. Check objects_dir for each data recipient
            3. Verify inheritance and override behavior
            4. Execute full recipe pipeline
            5. Verify output in correct directories

        Expected Behavior:
            - simplesample data recipient overrides objects_dir to /tmp
            - simplesample2 data recipient overrides objects_dir to ./var/objects/test1
            - default data recipient inherits objects_dir from recipe (./var/objects/test12)
            - All data recipients maintain reference to recipe_objects_dir
            - Configurations are written to correct directories

        Assertions:
            - Data recipient objects_dir values are correct
            - recipe_objects_dir references are maintained
            - Output files are created in correct directories
            - Template content is rendered correctly
        """
        # Arrange: Load recipe and get data recipients
        self.setUpConfig("etc/coshsh.cfg", "test12")
        r = self.generator.get_recipe("test12")

        dr_simplesample = r.get_datarecipient('simplesample')
        dr_simplesample2 = r.get_datarecipient('simplesample2')
        dr_default = r.get_datarecipient('default')

        # Assert: Verify objects_dir inheritance and override
        self.assertTrue(
            dr_simplesample.objects_dir == "/tmp",
            "simplesample data recipient should override objects_dir to /tmp"
        )
        self.assertTrue(
            dr_simplesample.recipe_objects_dir == r.objects_dir,
            "simplesample data recipient should maintain reference to recipe objects_dir"
        )

        self.assertTrue(
            dr_simplesample2.objects_dir == "./var/objects/test1",
            "simplesample2 data recipient should override objects_dir to ./var/objects/test1"
        )
        self.assertTrue(
            dr_simplesample2.recipe_objects_dir == r.objects_dir,
            "simplesample2 data recipient should maintain reference to recipe objects_dir"
        )

        self.assertTrue(
            dr_default.objects_dir == "./var/objects/test12",
            "default data recipient should inherit objects_dir from recipe"
        )
        self.assertTrue(
            dr_default.recipe_objects_dir == r.objects_dir,
            "default data recipient should maintain reference to recipe objects_dir"
        )

        # Act: Execute recipe pipeline
        r.collect()
        r.assemble()
        r.render()
        r.output()

        # Assert: Verify output files in default data recipient directory
        self.assertTrue(
            os.path.exists("var/objects/test12/dynamic/hosts"),
            "Dynamic hosts directory should be created in default objects_dir"
        )
        self.assertTrue(
            os.path.exists("var/objects/test12/dynamic/hosts/test_host_0"),
            "Host directory should be created for test_host_0"
        )
        self.assertTrue(
            os.path.exists("var/objects/test12/dynamic/hosts/test_host_0/os_linux_default.cfg"),
            "Linux OS configuration should be created for test_host_0"
        )
        self.assertTrue(
            os.path.exists("var/objects/test12/dynamic/hosts/test_host_1/os_windows_default.cfg"),
            "Windows OS configuration should be created for test_host_1"
        )

        # Assert: Verify template content
        with io.open("var/objects/test12/dynamic/hosts/test_host_1/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue(
            'os_windows_default_check_unittest' in os_windows_default_cfg,
            "Windows OS configuration should contain unittest check command"
        )

        # Assert: Verify output files in simplesample2 custom directory
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts"),
            "Dynamic hosts directory should be created in simplesample2 objects_dir"
        )
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"),
            "Host directory should be created for test_host_0 in custom location"
        )
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"),
            "Linux OS configuration should be created in custom location"
        )
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_1/os_windows_default.cfg"),
            "Windows OS configuration should be created in custom location"
        )

    def test_recipe_with_implicit_default_data_recipient(self) -> None:
        """Test recipe with implicit default data recipient.

        When a recipe doesn't explicitly define data recipients, coshsh
        should automatically create a default data recipient. This test
        verifies that implicit data recipients work correctly.

        Test Setup:
            1. Load recipe test12a without explicit data recipients
            2. Get datasources and data recipients
            3. Verify default data recipient was created
            4. Check attribute inheritance
            5. Execute recipe and verify output

        Expected Behavior:
            - Default data recipient is automatically created
            - Attribute inheritance works as in explicit case
            - Output is generated correctly
            - Multiple datasources work with implicit recipient

        Assertions:
            - Data recipient objects_dir values are correct
            - recipe_objects_dir references are maintained
            - Output files are created in correct directories
            - Template content is rendered correctly
        """
        # Arrange: Load recipe and get components
        self.setUpConfig("etc/coshsh.cfg", "test12a")
        r = self.generator.get_recipe("test12a")

        ds1 = r.get_datasource('csv10.1')
        ds2 = r.get_datasource('csv10.2')
        ds3 = r.get_datasource('csv10.3')
        ds1.objects = r.objects
        ds2.objects = r.objects
        ds3.objects = r.objects

        dr_simplesample = r.get_datarecipient("simplesample")
        dr_simplesample2 = r.get_datarecipient("simplesample2")
        dr_default = r.get_datarecipient("datarecipient_coshsh_default")

        # Assert: Verify objects_dir inheritance with implicit default
        self.assertTrue(
            dr_simplesample.objects_dir == "/tmp",
            "simplesample data recipient should override objects_dir to /tmp"
        )
        self.assertTrue(
            dr_simplesample.recipe_objects_dir == self.generator.recipes['test12a'].objects_dir,
            "simplesample data recipient should maintain reference to recipe objects_dir"
        )

        self.assertTrue(
            dr_simplesample2.objects_dir == "./var/objects/test1",
            "simplesample2 data recipient should override objects_dir to ./var/objects/test1"
        )
        self.assertTrue(
            dr_simplesample2.recipe_objects_dir == self.generator.recipes['test12a'].objects_dir,
            "simplesample2 data recipient should maintain reference to recipe objects_dir"
        )

        self.assertTrue(
            dr_default.objects_dir == "./var/objects/test12",
            "Implicit default data recipient should inherit objects_dir from recipe"
        )
        self.assertTrue(
            dr_default.recipe_objects_dir == self.generator.recipes['test12a'].objects_dir,
            "Implicit default data recipient should maintain reference to recipe objects_dir"
        )

        # Act: Execute recipe pipeline
        r.collect()
        r.assemble()
        r.render()
        r.output()

        # Assert: Verify output files in default data recipient directory
        self.assertTrue(
            os.path.exists("var/objects/test12/dynamic/hosts"),
            "Dynamic hosts directory should be created in default objects_dir"
        )
        self.assertTrue(
            os.path.exists("var/objects/test12/dynamic/hosts/test_host_0"),
            "Host directory should be created for test_host_0"
        )
        self.assertTrue(
            os.path.exists("var/objects/test12/dynamic/hosts/test_host_0/os_linux_default.cfg"),
            "Linux OS configuration should be created for test_host_0"
        )
        self.assertTrue(
            os.path.exists("var/objects/test12/dynamic/hosts/test_host_1/os_windows_default.cfg"),
            "Windows OS configuration should be created for test_host_1"
        )

        # Assert: Verify template content
        with io.open("var/objects/test12/dynamic/hosts/test_host_1/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
            self.assertTrue(
                'os_windows_default_check_unittest' in os_windows_default_cfg,
                "Windows OS configuration should contain unittest check command"
            )

        # Assert: Verify output files in simplesample2 custom directory
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts"),
            "Dynamic hosts directory should be created in simplesample2 objects_dir"
        )
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"),
            "Host directory should be created for test_host_0 in custom location"
        )
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"),
            "Linux OS configuration should be created in custom location"
        )
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/test_host_1/os_windows_default.cfg"),
            "Windows OS configuration should be created in custom location"
        )

    def test_datasource_attributes_available_in_templates(self) -> None:
        """Test that datasource attributes are available in templates.

        Datasource-specific attributes (like database credentials) should
        be accessible in Jinja2 templates. This test verifies attribute
        substitution and proper encoding of special characters.

        Test Setup:
            1. Load recipe oracleds2tpl
            2. Set datasource attributes (sid, username, password)
            3. Use password with special shell characters
            4. Create host and application
            5. Render templates
            6. Verify attributes appear correctly in output

        Expected Behavior:
            - Datasource attributes are accessible in templates
            - Special characters in passwords are RFC3986 URL-encoded
            - Encoded values appear in rendered configuration
            - Shell-breaking characters don't cause issues

        Special Test Case:
            Password with shell-breaking characters:
            "*(;!&haha,friss!das!du!blöde!shell!"
            Should be encoded as: rfc3986://...

        Assertions:
            - Application is created
            - Configuration file is rendered
            - Encoded password appears in output with correct prefix
        """
        # Arrange: Load recipe and datasource
        self.setUpConfig("etc/coshsh.cfg", "oracleds2tpl")
        r = self.generator.get_recipe("oracleds2tpl")
        ds = r.get_datasource('csv10.1')
        ds.objects = r.objects

        # Arrange: Set datasource attributes with shell-breaking password
        bash_breaker = u"*(;!&haha,friss!das!du!blöde!shell!"
        bash_breaker_encoded = 'rfc3986://' + urllib.request.pathname2url(bash_breaker.encode('utf-8'))

        setattr(ds, "sid", "ORCL1234")
        setattr(ds, "username", "zosch")
        setattr(ds, "password", bash_breaker)

        # Arrange: Create host and application
        host = Host({
            'host_name': 'testhost',
            'address': '127.0.0.1',
            'alias': 'hosttest',
        })
        app = Application({
            'host_name': 'testhost',
            'name': 'eventhandlerdb',
            'type': 'oraappindsdb',
        })

        # Act: Collect, add objects, and process
        r.collect()
        ds.add('hosts', host)
        ds.add('applications', app)
        r.assemble()
        r.render()

        # Assert: Verify application count
        self.assertTrue(
            len(self.generator.recipes['oracleds2tpl'].objects['applications']) == 3,
            "Should have 3 applications (2 from datasource + 1 added manually)"
        )

        # Act: Output configuration
        self.generator.recipes['oracleds2tpl'].output()

        # Assert: Verify configuration file and content
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts/testhost/app_oraappindsdb_default.cfg"),
            "Application configuration file should be created"
        )

        with io.open("var/objects/test1/dynamic/hosts/testhost/app_oraappindsdb_default.cfg") as f:
            app_oraappindsdb_default_cfg = f.read()

        self.assertTrue(
            "!"+bash_breaker_encoded+" --sql" in app_oraappindsdb_default_cfg,
            f"Configuration should contain RFC3986-encoded password: !{bash_breaker_encoded} --sql"
        )
