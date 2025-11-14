"""Test suite for recipe inheritance functionality.

This module tests the recipe inheritance feature which allows recipes to
inherit configuration from parent recipes using the 'inherit' directive.
"""

from __future__ import annotations

from tests.common_coshsh_test import CommonCoshshTest


class RecipeInheritanceTest(CommonCoshshTest):
    """Test suite for recipe configuration inheritance.

    This suite verifies that:
    - Recipes can inherit datasource configurations from parent recipes
    - Child recipes can override parent datasource filters
    - Template recipes (with __ prefix) are not instantiated as real recipes
    - Multiple levels of inheritance work correctly
    - Class paths are inherited from parent recipes

    Test Configuration:
        Uses recipes: cust, cust1, cust2 (template), cust3
        Configuration file: etc/coshsh2.cfg

    Recipe Inheritance Rules:
        - Regular recipes: [recipe_name]
        - Template recipes: [recipe__name] (double underscore, not instantiated)
        - Child recipe: inherit = parent_recipe_name
        - Child can override any parent settings

    Context:
        Recipe inheritance allows for DRY (Don't Repeat Yourself) configuration
        where common settings can be defined once in a parent recipe and
        inherited by multiple child recipes. This is useful for managing
        multiple customers or environments with similar configurations.
    """

    def test_recipe_inheritance_preserves_and_overrides_correctly(self) -> None:
        """Test that recipe inheritance works correctly for datasources and filters.

        This test verifies the complete inheritance mechanism:
        1. Base recipe (cust) has datasources and filters
        2. Child recipe (cust1) inherits datasources but overrides filter
        3. Template recipe (cust2) with __ prefix is not instantiated
        4. Another child (cust3) inherits and overrides correctly
        5. Class paths are inherited

        Test Setup:
            - Loads config with multiple recipes in inheritance hierarchy
            - cust: base recipe with 3 datasources
            - cust1: inherits from cust, overrides filter for csv10.1
            - cust2: template recipe (recipe__cust2), should not exist
            - cust3: inherits from cust, overrides filter, has custom class path

        Expected Behavior:
            - cust has datasources ['csv10.1', 'csv10.2', 'csv10.3']
            - cust has filter 'fff' for csv10.1
            - cust1 inherits same datasources
            - cust1 overrides filter to 'fff1' for csv10.1
            - cust2 is None (template recipes are not instantiated)
            - cust3 inherits same datasources
            - cust3 overrides filter to 'fff3' for csv10.1
            - cust3 has custom class path './recipes/test12/classes'

        Assertions:
            - Base recipe has correct datasources
            - Base recipe has correct filter
            - Child recipe inherits datasources
            - Child recipe overrides filter correctly
            - Template recipe is not instantiated (None)
            - Second child recipe inherits datasources
            - Second child recipe overrides filter correctly
            - Second child recipe has custom class path
        """
        # Arrange: Load configuration with recipe inheritance
        self.setUpConfig("etc/coshsh2.cfg", None)

        # Act: Get recipes (inheritance is processed during config loading)
        recipe_cust = self.generator.get_recipe("cust")
        recipe_cust1 = self.generator.get_recipe("cust1")
        recipe_cust2 = self.generator.get_recipe("cust2")
        recipe_cust3 = self.generator.get_recipe("cust3")

        # Assert: Verify base recipe (cust) configuration
        self.assertTrue(
            recipe_cust.datasource_names == ['csv10.1', 'csv10.2', 'csv10.3'],
            "Base recipe should have datasources ['csv10.1', 'csv10.2', 'csv10.3']"
        )
        self.assertTrue(
            recipe_cust.datasource_filters['csv10.1'] == 'fff',
            "Base recipe should have filter 'fff' for datasource csv10.1"
        )

        # Assert: Verify first child recipe (cust1) inherits and overrides
        self.assertTrue(
            recipe_cust1.datasource_names == ['csv10.1', 'csv10.2', 'csv10.3'],
            "Child recipe cust1 should inherit datasources from parent"
        )
        self.assertTrue(
            recipe_cust1.datasource_filters['csv10.1'] == 'fff1',
            "Child recipe cust1 should override filter to 'fff1' for datasource csv10.1"
        )

        # Assert: Verify template recipe (recipe__cust2) is not instantiated
        self.assertTrue(
            recipe_cust2 == None,
            "Template recipe with __ prefix (recipe__cust2) should not be instantiated"
        )

        # Assert: Verify second child recipe (cust3) inherits and overrides
        self.assertTrue(
            recipe_cust3.datasource_names == ['csv10.1', 'csv10.2', 'csv10.3'],
            "Child recipe cust3 should inherit datasources from parent"
        )
        self.assertTrue(
            recipe_cust3.datasource_filters['csv10.1'] == 'fff3',
            "Child recipe cust3 should override filter to 'fff3' for datasource csv10.1"
        )
        self.assertTrue(
            './recipes/test12/classes' in recipe_cust3.classes_path,
            "Child recipe cust3 should have custom classes path './recipes/test12/classes'"
        )
