"""Test suite for attribute whitespace stripping functionality.

This module tests the automatic whitespace stripping behavior for application
attributes based on attribute type definitions:
- String attributes strip whitespace by default
- Boolean attributes preserve whitespace
- List attributes strip whitespace from list items
"""

from __future__ import annotations

import os
import coshsh
from coshsh.host import Host
from coshsh.application import Application
from coshsh.monitoringdetail import MonitoringDetail
from tests.common_coshsh_test import CommonCoshshTest


class AttributeStripTest(CommonCoshshTest):
    """Test suite for application attribute whitespace stripping.

    This test suite verifies that application attributes correctly handle
    whitespace stripping based on their type definitions:
    - String attributes: Leading and trailing whitespace is stripped
    - Boolean attributes: Whitespace is preserved
    - List attributes: Whitespace is stripped from individual list items

    This is important for data quality and consistent attribute handling
    when loading data from CSV files or other sources that may have
    inconsistent whitespace.

    Test Configuration:
        Uses test recipe: test33
        Config file: etc/coshsh5.cfg
        Custom application plugins:
            - AppWithBlanks (default string stripping)
            - AppWithBlanksBool (boolean, preserves whitespace)
            - AppWithBlanksList (list, strips item whitespace)

    Related:
        See coshsh/item.py for attribute type definitions
        See recipes/test33/classes/ for test application plugins
    """

    def test_application_attributes_strip_whitespace_by_type(self) -> None:
        """Test that application attributes strip whitespace based on type.

        Verifies that the application attribute type system correctly handles
        whitespace stripping for different attribute types (string, boolean, list).

        This is critical for data quality when loading from CSV files where
        whitespace inconsistencies are common.

        Test Setup:
            1. Configure recipe test33 with attribute stripping plugins
            2. Create three applications with identical input values:
               - appwithblanks: Uses default string attributes
               - appwithblanksbool: Uses boolean-type attributes
               - appwithblankslist: Uses list-type attributes
            3. Add applications to datasource
            4. Collect, assemble, and render

        Expected Behavior:
            AppWithBlanks (string attributes):
                - 'prefix': '    prefix ' → 'prefix' (stripped)
                - 'suffix': '    suffix ' → 'suffix' (stripped)
                - 'swisscheese': ' gruezi i am a swiss cheese ' → 'gruezi i am a swiss cheese' (stripped)

            AppWithBlanksBool (boolean-type attributes):
                - All attributes preserve whitespace exactly as input
                - 'prefix': '    prefix ' (unchanged)
                - 'suffix': '    suffix ' (unchanged)
                - 'swisscheese': ' gruezi i am a swiss cheese ' (unchanged)

            AppWithBlanksList (list-type attributes):
                - 'prefix': '    prefix ' (preserved as single item)
                - 'suffix': '    suffix ' (preserved as single item)
                - 'swisscheese': ' gruezi i am a swiss cheese ' → 'gruezi i am a swiss cheese' (items stripped)

        Assertions:
            - Exactly 3 applications are created
            - Applications are correctly typed to their plugin classes
            - Attribute values match expected stripping behavior
        """
        # Arrange: Set up recipe with attribute stripping plugins
        self.setUpConfig("etc/coshsh5.cfg", "test33")
        recipe = self.generator.get_recipe("test33")
        recipe.update_item_class_factories()

        # Configure simplesample datasource
        self.generator.cookbook.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.generator.cookbook.items("datasource_SIMPLESAMPLE")
        recipe.add_datasource(**dict(cfg))

        datasource = recipe.get_datasource("simplesample")
        datasource.objects = recipe.objects

        # Create host
        host = Host({
            'host_name': 'testhost',
            'address': '127.0.0.1',
        })
        datasource.add('hosts', host)

        # Create three applications with identical inputs but different types
        # App 1: Default string attributes (should strip whitespace)
        app1 = Application({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'appwithblanks',
            'prefix': '    prefix ',
            'suffix': '    suffix ',
            'swisscheese': ' gruezi i am a swiss cheese ',
        })

        # App 2: Boolean-type attributes (should preserve whitespace)
        app2 = Application({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'appwithblanksbool',
            'prefix': '    prefix ',
            'suffix': '    suffix ',
            'swisscheese': ' gruezi i am a swiss cheese ',
        })

        # App 3: List-type attributes (should strip list items)
        app3 = Application({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'appwithblankslist',
            'prefix': '    prefix ',
            'suffix': '    suffix ',
            'swisscheese': ' gruezi i am a swiss cheese ',
        })

        datasource.add('applications', app1)
        datasource.add('applications', app2)
        datasource.add('applications', app3)

        # Act: Process applications through the recipe workflow
        recipe.collect()
        recipe.assemble()
        recipe.render()

        # Assert: Verify applications were created and typed correctly
        self.assertEqual(
            len(recipe.objects['applications']), 3,
            "Should have exactly 3 applications created"
        )

        applications_list = list(datasource.getall('applications'))

        # Verify first application is the same object and correct type
        self.assertIs(
            applications_list[0], app1,
            "First application should be app1"
        )
        self.assertEqual(
            applications_list[0].__class__.__name__, "AppWithBlanks",
            "First application should be typed as AppWithBlanks"
        )

        # Verify second application type
        recipe_apps = list(self.generator.recipes['test33'].datasources[0].getall('applications'))
        self.assertEqual(
            recipe_apps[1].__class__.__name__, "AppWithBlanksBool",
            "Second application should be typed as AppWithBlanksBool"
        )

        # Verify third application type
        self.assertEqual(
            recipe_apps[2].__class__.__name__, "AppWithBlanksList",
            "Third application should be typed as AppWithBlanksList"
        )

        # Assert: Verify whitespace stripping for string attributes (app1)
        self.assertEqual(
            app1.prefix, "prefix",
            "AppWithBlanks string attribute 'prefix' should have whitespace stripped"
        )
        self.assertEqual(
            app1.suffix, "suffix",
            "AppWithBlanks string attribute 'suffix' should have whitespace stripped"
        )
        self.assertEqual(
            app1.swisscheese, "gruezi i am a swiss cheese",
            "AppWithBlanks string attribute 'swisscheese' should have whitespace stripped"
        )

        # Assert: Verify whitespace preservation for boolean-type attributes (app2)
        self.assertEqual(
            app2.prefix, "    prefix ",
            "AppWithBlanksBool boolean attribute 'prefix' should preserve whitespace"
        )
        self.assertEqual(
            app2.suffix, "    suffix ",
            "AppWithBlanksBool boolean attribute 'suffix' should preserve whitespace"
        )
        self.assertEqual(
            app2.swisscheese, " gruezi i am a swiss cheese ",
            "AppWithBlanksBool boolean attribute 'swisscheese' should preserve whitespace"
        )

        # Assert: Verify list-type attribute behavior (app3)
        self.assertEqual(
            app3.prefix, "    prefix ",
            "AppWithBlanksList list attribute 'prefix' should preserve whitespace for single item"
        )
        self.assertEqual(
            app3.suffix, "    suffix ",
            "AppWithBlanksList list attribute 'suffix' should preserve whitespace for single item"
        )
        self.assertEqual(
            app3.swisscheese, "gruezi i am a swiss cheese",
            "AppWithBlanksList list attribute 'swisscheese' should strip whitespace from list items"
        )

