"""Tests for vault/secrets integration — file decryption, production vs non-production mode, and failure cases."""
import pytest
import os
import coshsh
from tests.common_coshsh_test import CommonCoshshTest


class VaultTest(CommonCoshshTest):

    def test_open_vault(self):
        """Vault is decrypted with correct password and secrets are accessible."""
        os.environ["NAEMON_VIM_MASTER_PASSWORD"] = "niemonfault"
        self.setUpConfig("etc/coshsh20.cfg", "prod")
        r_prod = self.generator.get_recipe("prod")
        self.assertEqual(os.path.abspath(r_prod.classes_path[0]), os.path.abspath('./recipes/vault/classes'))
        self.assertEqual(os.path.abspath(r_prod.templates_path[0]), os.path.abspath('recipes/vault/templates'))
        self.assertEqual(os.path.abspath(r_prod.jinja2.loader.searchpath[0]), os.path.abspath('recipes/vault/templates'))
        secrets = r_prod.vaults[0].__dict__
        self.assertEqual(r_prod.vaults[0].get('$VAULT1$'), "test")

    def test_open_vault_nonprod(self):
        """Non-production vault config points datasource to the non-prod data directory."""
        os.environ["NAEMON_VIM_MASTER_PASSWORD"] = "niemonfault"
        self.setUpConfig("etc/coshsh20.cfg", "nonprod")
        r_nonprod = self.generator.get_recipe("nonprod")
        self.assertEqual(r_nonprod.datasources[0].dir, "/tmp/.hidden")

    def test_open_vault_prod(self):
        """Production vault config points datasource to the prod data directory with correct credentials."""
        os.environ["NAEMON_VIM_MASTER_PASSWORD"] = "niemonfault"
        self.setUpConfig("etc/coshsh20.cfg", "prod")
        r_prod = self.generator.get_recipe("prod")
        self.assertEqual(r_prod.datasources[0].dir, "/tmp/.h1dd3n")
        self.assertEqual(r_prod.datasources[0].username, "monitoring")

    def test_open_vault_fails_bad_password(self):
        """Wrong master password causes VaultNotAvailable and recipe is not loaded."""
        os.environ["NAEMON_VIM_MASTER_PASSWORD"] = "naemonvault"
        # internally there is a VaultNotAvailable and the generator loads no recipes
        self.setUpConfig("etc/coshsh20.cfg", "prod")
        r_prod = self.generator.get_recipe("prod")
        self.assertIsNone(r_prod)

    def test_vault_get_returns_none_for_missing_key(self):
        """vault.get() returns None for a key that does not exist."""
        os.environ["NAEMON_VIM_MASTER_PASSWORD"] = "niemonfault"
        self.setUpConfig("etc/coshsh20.cfg", "prod")
        r_prod = self.generator.get_recipe("prod")
        self.assertIsNone(r_prod.vaults[0].get('$NONEXISTENT$'))

    def test_vault_getall_returns_list_of_values(self):
        """vault.getall() returns a list of all stored values."""
        os.environ["NAEMON_VIM_MASTER_PASSWORD"] = "niemonfault"
        self.setUpConfig("etc/coshsh20.cfg", "prod")
        r_prod = self.generator.get_recipe("prod")
        values = r_prod.vaults[0].getall()
        self.assertIsInstance(values, list)
        self.assertTrue(len(values) > 0)

    def test_open_vault_fails_no_such_file(self):
        """Missing vault file causes VaultNotAvailable and recipe is not loaded."""
        os.environ["NAEMON_VIM_MASTER_PASSWORD"] = "niemonfault"
        # internally there is a VaultNotAvailable and the generator loads no recipes
        self.setUpConfig("etc/coshsh20.cfg", "nagios")
        r_nagios = self.generator.get_recipe("nagios")
        self.assertIsNone(r_nagios)
