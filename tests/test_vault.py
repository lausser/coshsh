import pytest
import os
import io
import coshsh
from tests.common_coshsh_test import CommonCoshshTest

#NAEMON_VIM_MASTER_PASSWORD = "niemonfault"
#$VAULT1$=test
#$VAULT2$=example
#$VAULT:EXAMPLE$=not only numbers...
#$VAULT:passnonprod$=geheim
#$VAULT:passprod$ = streng geheim

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

    def test_open_vault_nonprod(self):
        os.environ["NAEMON_VIM_MASTER_PASSWORD"] = "niemonfault"
        self.setUpConfig("etc/coshsh20.cfg", "nonprod")
        r_nonprod = self.generator.get_recipe("nonprod")
        self.assertTrue(r_nonprod.datasources[0].dir == "/tmp/.hidden")

    def test_open_vault_prod(self):
        os.environ["NAEMON_VIM_MASTER_PASSWORD"] = "niemonfault"
        self.setUpConfig("etc/coshsh20.cfg", "prod")
        r_prod = self.generator.get_recipe("prod")
        print(r_prod.datasources[0].__dict__)
        self.assertTrue(r_prod.datasources[0].dir == "/tmp/.h1dd3n")

    def test_open_vault_fails_bad_password(self):
        os.environ["NAEMON_VIM_MASTER_PASSWORD"] = "naemonvault"
        # internally there is a VaultNotAvailable and the generator
        # loads no recipes
        self.setUpConfig("etc/coshsh20.cfg", "prod")
        r_prod = self.generator.get_recipe("prod")
        self.assertTrue(r_prod == None)

    def test_open_vault_fails_no_such_file(self):
        os.environ["NAEMON_VIM_MASTER_PASSWORD"] = "niemonfault"
        # internally there is a VaultNotAvailable and the generator
        # loads no recipes
        self.setUpConfig("etc/coshsh20.cfg", "nagios")
        r_nagios = self.generator.get_recipe("nagios")
        self.assertTrue(r_nagios == None)



if __name__ == '__main__':
    unittest.main()


