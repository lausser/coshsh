from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def test_factories(self):
        self.setUpConfig("etc/coshsh.cfg", "test9")
        r = self.generator.get_recipe("test9")
        ds = r.get_datasource("simplesample")
        self.assertTrue(hasattr(ds, 'only_the_test_simplesample'))
        dr = r.get_datarecipient("simplesample")
        self.assertTrue(hasattr(dr, 'only_the_test_simplesample') and dr.only_the_test_simplesample == False)

    def test_create_recipe_fallback_datarecipient(self):
        self.setUpConfig("etc/coshsh.cfg", "test9a")
        r = self.generator.get_recipe("test9a")
        # there must be a recipient named "datarecipient_coshsh_default"
        self.assertTrue(r.datarecipients[0].name == "datarecipient_coshsh_default")
        # which must inherit the recipe's object_dir
        self.assertTrue(r.datarecipients[0].objects_dir == self.generator.recipes['test9a'].objects_dir)

    def test_create_recipe_fallback_datarecipient_write(self):
        self.setUpConfig("etc/coshsh.cfg", "test9a")
        r = self.generator.get_recipe("test9a")
        self.assertTrue(r.datarecipients[0].name == "datarecipient_coshsh_default")
        exporter = r.datarecipients[0]
        exporter.count_before_objects()
        self.assertTrue(exporter.old_objects == (0, 0))
        r.collect()
        r.assemble()
        # fill items.[cfgfiles]
        r.render()
        r.output()
        exporter.count_after_objects()
        self.assertTrue(exporter.new_objects == (1, 2))


