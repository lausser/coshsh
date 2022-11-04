from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def test_create_recipe_check_factories(self):
        self.setUpConfig("etc/coshsh.cfg", "test4")
        self.generator.run()
        self.assertTrue(self.generator.recipes['test4'].datasources[0].only_the_test_simplesample == True)

