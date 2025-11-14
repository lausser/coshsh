"""Test suite for datarecipient (destination) functionality.

This module tests the datarecipient factory pattern and datarecipient
behavior, including custom datarecipients, fallback defaults, and object
counting functionality.
"""

from __future__ import annotations

from tests.common_coshsh_test import CommonCoshshTest


class DatarecipientFactoryTest(CommonCoshshTest):
    """Test suite for datarecipient factory pattern and object counting.

    This test suite verifies that:
    - Datarecipient factory correctly instantiates datarecipient classes
    - Custom datarecipient attributes are properly set
    - Fallback default datarecipient is created when none specified
    - Default datarecipient inherits recipe's objects_dir
    - Datarecipients can count objects before and after processing
    - Object counting tracks hosts and applications correctly

    Test Configuration:
        Uses test recipes in tests/recipes/test9/ and test9a/
        Config file: etc/coshsh.cfg

    Datarecipient Types Tested:
        - simplesample: Custom test datarecipient with specific attributes
        - datarecipient_coshsh_default: Fallback default datarecipient
    """

    def test_datasource_and_datarecipient_factory_attributes(self) -> None:
        """Test that factories create instances with custom attributes.

        This test verifies that both datasource and datarecipient factory
        patterns correctly instantiate classes with custom attributes.
        It tests a custom 'simplesample' datasource and datarecipient pair.

        Setup:
            - Loads test9 recipe configuration
            - Gets datasource and datarecipient from recipe

        Expected Behavior:
            - Datasource is created with custom test attribute
            - Datarecipient is created with custom test attribute
            - Custom attributes have expected values

        Assertions:
            - Datasource has 'only_the_test_simplesample' attribute
            - Datarecipient has 'only_the_test_simplesample' attribute
            - Datarecipient attribute is False (different from datasource)
        """
        # Arrange: Set up configuration and get recipe
        self.setUpConfig("etc/coshsh.cfg", "test9")
        recipe = self.generator.get_recipe("test9")

        # Act: Get datasource and datarecipient
        datasource = recipe.get_datasource("simplesample")
        datarecipient = recipe.get_datarecipient("simplesample")

        # Assert: Verify factory created objects with custom attributes
        self.assertTrue(
            hasattr(datasource, 'only_the_test_simplesample'),
            "Datasource should have custom factory attribute 'only_the_test_simplesample'"
        )
        self.assertTrue(
            hasattr(datarecipient, 'only_the_test_simplesample') and
            datarecipient.only_the_test_simplesample == False,
            "Datarecipient should have custom factory attribute 'only_the_test_simplesample' set to False"
        )

    def test_create_recipe_with_fallback_default_datarecipient(self) -> None:
        """Test that recipe creates fallback default datarecipient when none specified.

        When a recipe is configured without an explicit datarecipient,
        coshsh should automatically create a default datarecipient named
        'datarecipient_coshsh_default' to handle output operations.

        Setup:
            - Loads test9a recipe (configured without explicit datarecipient)
            - Gets recipe and checks datarecipients

        Expected Behavior:
            - Default datarecipient is automatically created
            - Default datarecipient has the standard name
            - Default datarecipient inherits recipe's objects_dir

        Assertions:
            - First datarecipient name is 'datarecipient_coshsh_default'
            - Datarecipient's objects_dir matches recipe's objects_dir
        """
        # Arrange: Set up configuration for recipe without explicit datarecipient
        self.setUpConfig("etc/coshsh.cfg", "test9a")
        recipe = self.generator.get_recipe("test9a")

        # Assert: Verify default datarecipient was created
        self.assertTrue(
            recipe.datarecipients[0].name == "datarecipient_coshsh_default",
            "Recipe without explicit datarecipient should create default 'datarecipient_coshsh_default'"
        )

        # Assert: Verify default datarecipient inherits recipe's objects_dir
        self.assertTrue(
            recipe.datarecipients[0].objects_dir == self.generator.recipes['test9a'].objects_dir,
            "Default datarecipient should inherit objects_dir from recipe"
        )

    def test_fallback_datarecipient_counts_objects_before_and_after(self) -> None:
        """Test that default datarecipient correctly counts objects before and after.

        This test verifies the object counting functionality of datarecipients,
        which tracks the number of hosts and applications before and after
        recipe processing. This is useful for monitoring changes and validating
        that the recipe processed the expected number of objects.

        Setup:
            - Loads test9a recipe with fallback datarecipient
            - Runs complete recipe pipeline
            - Counts objects before and after processing

        Expected Behavior:
            - Before processing: 0 hosts, 0 applications
            - After processing: 1 host, 2 applications
            - Object counts reflect actual processed objects

        Assertions:
            - Default datarecipient is created
            - old_objects count is (0, 0) before processing
            - new_objects count is (1, 2) after processing
        """
        # Arrange: Set up configuration with fallback datarecipient
        self.setUpConfig("etc/coshsh.cfg", "test9a")
        recipe = self.generator.get_recipe("test9a")

        # Verify default datarecipient is created
        self.assertTrue(
            recipe.datarecipients[0].name == "datarecipient_coshsh_default",
            "Recipe should use default datarecipient"
        )

        # Act: Count objects before processing
        exporter = recipe.datarecipients[0]
        exporter.count_before_objects()

        # Assert: Verify initial count is zero
        self.assertTrue(
            exporter.old_objects == (0, 0),
            "Before processing, datarecipient should count (0, 0) objects (hosts, apps)"
        )

        # Act: Run complete recipe pipeline
        recipe.collect()
        recipe.assemble()
        recipe.render()
        recipe.output()

        # Act: Count objects after processing
        exporter.count_after_objects()

        # Assert: Verify objects were created and counted
        self.assertTrue(
            exporter.new_objects == (1, 2),
            "After processing, datarecipient should count (1, 2) objects (1 host, 2 apps)"
        )
