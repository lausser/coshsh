import os
import io
import coshsh
from tests.common_coshsh_test import CommonCoshshTest

#NAEMON_VIM_MASTER_PASSWORD = "niemonfault"
class CoshshTest(CommonCoshshTest):

    def test_open_vault(self):
        os.environ["NAEMON_VIM_MASTER_PASSWORD"] = "niemonfault"
        self.setUpConfig("etc/coshsh20.cfg", "prod")
        r_prod = self.generator.get_recipe("prod")
        self.assertTrue(os.path.abspath(r_prod.classes_path[0]) == os.path.abspath('./recipes/vault/classes'))
        self.assertTrue(os.path.abspath(r_prod.templates_path[0]) == os.path.abspath('recipes/vault/templates'))
        self.assertTrue(os.path.abspath(r_prod.jinja2.loader.searchpath[0]) == os.path.abspath('recipes/vault/templates'))
        print(r_prod.vaults[0].__dict__)
        secrets = r_prod.vaults[0].read()
        secrets = r_prod.vaults[0].__dict__
        self.assertTrue(r_prod.vaults[0].get('$VAULT1$') == "test")
        print(secrets)
        #raise



if __name__ == '__main__':
    unittest.main()


