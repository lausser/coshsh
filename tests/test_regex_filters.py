import os
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def test_filters(self):
        self.setUpConfig("etc/coshsh7.cfg", None)
        r1 = self.generator.get_recipe("test1")
        r2 = self.generator.get_recipe("test2")
        r3 = self.generator.get_recipe("test3")
        r4 = self.generator.get_recipe("test4")
        r5 = self.generator.get_recipe("test5")
        print(self.generator.recipes.keys())
        self.assertTrue(r1.datasource_filters.get("ds1") == "kaas,koos")
        self.assertTrue(r1.datasource_filters.get("ds2") == "kees,kiis")

        self.assertTrue(r2.datasource_filters.get("ds1") == "kaas,koos")
        self.assertTrue(r2.datasource_filters.get("ds2") == None)
        self.assertTrue(r2.datasource_filters.get("dsa") == "alnuma")

        self.assertTrue(r3.datasource_filters.get("ds1") == "kaas,koos")
        self.assertTrue(r3.datasource_filters.get("ds2") == "numro")
        self.assertTrue(r3.datasource_filters.get("dsa") == "alnuma")
        self.assertTrue(r3.datasource_filters.get("ds3") == "numro")
        self.assertTrue(r3.datasource_filters.get("ds4") == None)

        self.assertTrue(r4.datasource_filters.get("ds1") == "kaas,koos")
        self.assertTrue(r4.datasource_filters.get("ds2") == "all*")
        self.assertTrue(r4.datasource_filters.get("dsa") == "all*")
        self.assertTrue(r4.datasource_filters.get("ds3") == "all*")
        self.assertTrue(r4.datasource_filters.get("ds4") == "all*")
        self.assertTrue(r4.datasource_filters.get("ds5") == "all*")

        self.assertTrue(r5.datasource_filters.get("ds1") == "kaas,koos")
        self.assertTrue(r5.datasource_filters.get("ds2") == "numro")
        self.assertTrue(r5.datasource_filters.get("dsa") == "alnuma")
        self.assertTrue(r5.datasource_filters.get("ds3") == "numro")
        self.assertTrue(r5.datasource_filters.get("ds4") == "all*")
        self.assertTrue(r5.datasource_filters.get("ds5") == "all*")

