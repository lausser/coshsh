"""Test suite for datasource factory and interface functionality.

This module tests the datasource factory pattern and datasource interface,
verifying that custom datasource classes can be instantiated with their
specific attributes.
"""

from __future__ import annotations

from tests.common_coshsh_test import CommonCoshshTest


class DatasourceFactoryTest(CommonCoshshTest):
    """Test suite for datasource factory pattern and custom datasource loading.

    This test suite verifies that:
    - Datasource factory correctly instantiates datasource classes
    - Custom datasource attributes are properly set
    - Datasource classes can define custom properties
    - Test-specific datasource implementations work correctly

    Test Configuration:
        Uses test recipe in tests/recipes/test4/
        Config file: etc/coshsh.cfg

    Datasource Types Tested:
        - simplesample: Custom test datasource with specific attributes
    """

    def test_create_recipe_and_verify_datasource_factory_attributes(self) -> None:
        """Test that datasource factory creates instances with custom attributes.

        This test verifies that the datasource factory pattern correctly
        instantiates datasource classes and that custom attributes defined
        in the datasource class are accessible after instantiation.

        The test uses a custom 'simplesample' datasource that has a special
        attribute 'only_the_test_simplesample' to verify factory behavior.

        Setup:
            - Loads test4 recipe configuration
            - Runs the complete recipe generation pipeline

        Expected Behavior:
            - Recipe is created successfully
            - Datasource is instantiated through the factory
            - Custom attribute 'only_the_test_simplesample' exists on datasource
            - Custom attribute has the expected value (True)

        Assertions:
            - Datasource has the custom test attribute
            - Attribute value is True
        """
        # Arrange: Set up configuration and get recipe
        self.setUpConfig("etc/coshsh.cfg", "test4")

        # Act: Run the complete recipe pipeline
        self.generator.run()

        # Assert: Verify datasource was created with custom factory attribute
        recipe = self.generator.recipes['test4']
        datasource = recipe.datasources[0]

        self.assertTrue(
            datasource.only_the_test_simplesample == True,
            "Datasource created by factory should have custom attribute 'only_the_test_simplesample' set to True"
        )
