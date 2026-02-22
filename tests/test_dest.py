"""Tests for Datarecipient class factory loading and fallback datarecipient behaviour."""
from tests.common_coshsh_test import CommonCoshshTest


class DatarecipientTest(CommonCoshshTest):

    def test_factories(self):
        """Datasource and datarecipient class factories load the correct plugin classes."""
        self.setUpConfig("etc/coshsh.cfg", "test9")
        r = self.generator.get_recipe("test9")
        ds = r.get_datasource("simplesample")
        self.assertTrue(hasattr(ds, 'only_the_test_simplesample'))
        dr = r.get_datarecipient("simplesample")
        self.assertTrue(hasattr(dr, 'only_the_test_simplesample'))
        self.assertFalse(dr.only_the_test_simplesample)

    def test_create_recipe_fallback_datarecipient(self):
        """Recipe without explicit datarecipient gets a default one inheriting the recipe's objects_dir."""
        self.setUpConfig("etc/coshsh.cfg", "test9a")
        r = self.generator.get_recipe("test9a")
        self.assertEqual(r.datarecipients[0].name, "datarecipient_coshsh_default")
        self.assertEqual(r.datarecipients[0].objects_dir, self.generator.recipes['test9a'].objects_dir)

    def test_create_recipe_fallback_datarecipient_write(self):
        """Default datarecipient counts objects before and after a full pipeline run."""
        self.setUpConfig("etc/coshsh.cfg", "test9a")
        r = self.generator.get_recipe("test9a")
        self.assertEqual(r.datarecipients[0].name, "datarecipient_coshsh_default")
        exporter = r.datarecipients[0]
        exporter.count_before_objects()
        self.assertEqual(exporter.old_objects, (0, 0))
        r.collect()
        r.assemble()
        r.render()
        r.output()
        exporter.count_after_objects()
        self.assertEqual(exporter.new_objects, (1, 2))
