"""Tests for datasource class factory loading and run-through pipeline."""

from tests.common_coshsh_test import CommonCoshshTest


class DatainterfaceTest(CommonCoshshTest):

    def test_create_recipe_check_factories(self):
        """Verify datasource-specific class factories are loaded and flag is set after a full run."""
        self.setUpConfig("etc/coshsh.cfg", "test4")
        self.generator.run()
        self.assertEqual(self.generator.recipes['test4'].datasources[0].only_the_test_simplesample, True)
