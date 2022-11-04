from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def test_inheritance(self):
        self.setUpConfig("etc/coshsh2.cfg", None)
        r_cust = self.generator.get_recipe("cust")
        r_cust1 = self.generator.get_recipe("cust1")
        r_cust2 = self.generator.get_recipe("cust2")
        r_cust3 = self.generator.get_recipe("cust3")
        self.assertTrue(r_cust.datasource_names == ['csv10.1', 'csv10.2', 'csv10.3'])
        self.assertTrue(r_cust.datasource_filters['csv10.1'] == 'fff')
        self.assertTrue(r_cust1.datasource_names == ['csv10.1', 'csv10.2', 'csv10.3'])
        self.assertTrue(r_cust1.datasource_filters['csv10.1'] == 'fff1')
        # recipe__cust2 mit 2x _ ist ein reines Template, kein Recipe
        self.assertTrue(r_cust2 == None)
        self.assertTrue(r_cust3.datasource_names == ['csv10.1', 'csv10.2', 'csv10.3'])
        self.assertTrue(r_cust3.datasource_filters['csv10.1'] == 'fff3')
        self.assertTrue('./recipes/test12/classes' in r_cust3.classes_path)

