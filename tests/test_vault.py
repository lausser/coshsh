"""Test suite for vault integration and secret management.

This module tests the vault functionality which provides secure storage and
retrieval of secrets (passwords, credentials) for use in coshsh configurations.
Tests verify vault encryption, decryption, secret substitution, and error
handling for incorrect passwords or missing vault files.
"""

from __future__ import annotations

import io
import os
import unittest

import coshsh
import pytest

from tests.common_coshsh_test import CommonCoshshTest


class VaultSecretManagementTest(CommonCoshshTest):
    """Test suite for vault secret management.

    This suite verifies that:
    - Vaults can be opened with correct master password
    - Secrets are retrieved correctly from vaults
    - Vault secrets can be used in recipe configurations
    - Invalid passwords prevent vault access
    - Missing vault files are handled gracefully
    - Multiple vaults can be used in different recipes

    Test Configuration:
        Uses recipes: prod, nonprod, nagios
        Config file: etc/coshsh20.cfg
        Vault file: Contains encrypted secrets

    Vault Format:
        Vaults store secrets in encrypted form:
        - $VAULT1$=test
        - $VAULT2$=example
        - $VAULT:EXAMPLE$=not only numbers...
        - $VAULT:passnonprod$=geheim
        - $VAULT:passprod$=streng geheim

    Environment Variables:
        NAEMON_VIM_MASTER_PASSWORD: Password to decrypt vault secrets

    Security Note:
        Vaults use encryption to protect sensitive data. The master password
        should be provided via environment variable, never hardcoded.

    Related:
        Vault functionality is part of OMD (Open Monitoring Distribution)
    """

    def test_vault_can_be_opened_and_secrets_retrieved(self) -> None:
        """Test that vault can be opened and secrets retrieved correctly.

        This test verifies the basic vault functionality: opening a vault
        with the correct master password and retrieving secret values.

        Test Setup:
            1. Set NAEMON_VIM_MASTER_PASSWORD environment variable
            2. Load prod recipe which uses vault
            3. Verify recipe paths are configured correctly
            4. Retrieve secret from vault
            5. Verify secret value matches expected

        Expected Behavior:
            - Recipe loads successfully with vault
            - Classes and templates paths are correct
            - Jinja2 loader searchpath is configured
            - Vault secret retrieval works
            - $VAULT1$ returns "test"

        Environment:
            NAEMON_VIM_MASTER_PASSWORD=niemonfault

        Secrets:
            $VAULT1$ should decrypt to "test"

        Assertions:
            - Classes path is correct
            - Templates path is correct
            - Jinja2 searchpath is correct
            - Vault secret $VAULT1$ equals "test"
        """
        # Arrange: Set master password environment variable
        os.environ["NAEMON_VIM_MASTER_PASSWORD"] = "niemonfault"

        # Act: Load recipe with vault
        self.setUpConfig("etc/coshsh20.cfg", "prod")
        r_prod = self.generator.get_recipe("prod")

        # Assert: Verify recipe paths
        self.assertTrue(
            os.path.abspath(r_prod.classes_path[0]) == os.path.abspath('./recipes/vault/classes'),
            "Recipe classes_path should point to vault classes directory"
        )
        self.assertTrue(
            os.path.abspath(r_prod.templates_path[0]) == os.path.abspath('recipes/vault/templates'),
            "Recipe templates_path should point to vault templates directory"
        )
        self.assertTrue(
            os.path.abspath(r_prod.jinja2.loader.searchpath[0]) == os.path.abspath('recipes/vault/templates'),
            "Jinja2 loader searchpath should point to vault templates directory"
        )

        # Debug output
        print(r_prod.vaults[0].__dict__)
        print(r_prod.vaults[0].__dict__)

        # Act: Retrieve secrets from vault
        secrets = r_prod.vaults[0].__dict__
        print(secrets)

        # Assert: Verify secret value
        self.assertTrue(
            r_prod.vaults[0].get('$VAULT1$') == "test",
            "Vault secret $VAULT1$ should decrypt to 'test'"
        )

    def test_vault_secrets_used_in_nonprod_datasource_configuration(self) -> None:
        """Test that vault secrets are used in nonprod datasource configuration.

        This test verifies that secrets from a vault are correctly substituted
        into datasource configuration for the nonprod recipe.

        Test Setup:
            1. Set NAEMON_VIM_MASTER_PASSWORD environment variable
            2. Load nonprod recipe which uses vault
            3. Verify datasource configuration uses vault secret

        Expected Behavior:
            - Recipe loads successfully
            - Datasource uses vault secret for directory path
            - Vault secret is substituted correctly

        Datasource Configuration:
            The nonprod datasource should have dir="/tmp/.hidden"
            which comes from a vault secret.

        Assertions:
            - Datasource dir equals "/tmp/.hidden"
        """
        # Arrange: Set master password environment variable
        os.environ["NAEMON_VIM_MASTER_PASSWORD"] = "niemonfault"

        # Act: Load nonprod recipe
        self.setUpConfig("etc/coshsh20.cfg", "nonprod")
        r_nonprod = self.generator.get_recipe("nonprod")

        # Assert: Verify vault secret in datasource configuration
        self.assertTrue(
            r_nonprod.datasources[0].dir == "/tmp/.hidden",
            "Nonprod datasource directory should be '/tmp/.hidden' from vault secret"
        )

    def test_vault_secrets_used_in_prod_datasource_configuration(self) -> None:
        """Test that vault secrets are used in prod datasource configuration.

        This test verifies that multiple vault secrets are correctly
        substituted into datasource configuration for the prod recipe,
        including directory paths and usernames.

        Test Setup:
            1. Set NAEMON_VIM_MASTER_PASSWORD environment variable
            2. Load prod recipe which uses vault
            3. Verify datasource configuration uses vault secrets

        Expected Behavior:
            - Recipe loads successfully
            - Datasource uses vault secrets for directory and username
            - Multiple vault secrets are substituted correctly

        Datasource Configuration:
            - dir should be "/tmp/.h1dd3n" (from vault secret)
            - username should be "monitoring" (from vault secret)

        Assertions:
            - Datasource dir equals "/tmp/.h1dd3n"
            - Datasource username equals "monitoring"
        """
        # Arrange: Set master password environment variable
        os.environ["NAEMON_VIM_MASTER_PASSWORD"] = "niemonfault"

        # Act: Load prod recipe
        self.setUpConfig("etc/coshsh20.cfg", "prod")
        r_prod = self.generator.get_recipe("prod")

        # Debug output
        print(r_prod.datasources[0].__dict__)

        # Assert: Verify vault secrets in datasource configuration
        self.assertTrue(
            r_prod.datasources[0].dir == "/tmp/.h1dd3n",
            "Prod datasource directory should be '/tmp/.h1dd3n' from vault secret"
        )
        self.assertTrue(
            r_prod.datasources[0].username == "monitoring",
            "Prod datasource username should be 'monitoring' from vault secret"
        )

    def test_vault_fails_to_open_with_incorrect_password(self) -> None:
        """Test that vault fails to open with incorrect master password.

        When an incorrect master password is provided, the vault should
        fail to decrypt, resulting in a VaultNotAvailable exception.
        The generator should handle this gracefully by not loading the
        affected recipe.

        Test Setup:
            1. Set incorrect NAEMON_VIM_MASTER_PASSWORD
            2. Attempt to load prod recipe
            3. Verify recipe loading fails

        Expected Behavior:
            - VaultNotAvailable exception is raised internally
            - Generator does not load the recipe
            - get_recipe returns None for the failed recipe

        Security:
            This behavior prevents unauthorized access to encrypted secrets
            and ensures that recipes requiring vault secrets don't run with
            partial or incorrect configuration.

        Assertions:
            - Recipe is None (not loaded)
        """
        # Arrange: Set incorrect master password
        os.environ["NAEMON_VIM_MASTER_PASSWORD"] = "naemonvault"  # Wrong password

        # Act: Attempt to load recipe with vault
        # Internally there is a VaultNotAvailable and the generator loads no recipes
        self.setUpConfig("etc/coshsh20.cfg", "prod")
        r_prod = self.generator.get_recipe("prod")

        # Assert: Verify recipe was not loaded
        self.assertTrue(
            r_prod == None,
            "Recipe should not load when vault password is incorrect"
        )

    def test_vault_fails_when_vault_file_does_not_exist(self) -> None:
        """Test that vault fails gracefully when vault file does not exist.

        When a recipe references a vault file that doesn't exist, the
        generator should handle this gracefully by not loading the recipe.

        Test Setup:
            1. Set correct NAEMON_VIM_MASTER_PASSWORD
            2. Attempt to load recipe with non-existent vault file
            3. Verify recipe loading fails

        Expected Behavior:
            - VaultNotAvailable exception is raised internally
            - Generator does not load the recipe
            - get_recipe returns None for the failed recipe

        File System:
            The nagios recipe references a vault file that doesn't exist
            in the test environment.

        Assertions:
            - Recipe is None (not loaded)
        """
        # Arrange: Set correct master password
        os.environ["NAEMON_VIM_MASTER_PASSWORD"] = "niemonfault"

        # Act: Attempt to load recipe with non-existent vault file
        # Internally there is a VaultNotAvailable and the generator loads no recipes
        self.setUpConfig("etc/coshsh20.cfg", "nagios")
        r_nagios = self.generator.get_recipe("nagios")

        # Assert: Verify recipe was not loaded
        self.assertTrue(
            r_nagios == None,
            "Recipe should not load when vault file does not exist"
        )


if __name__ == '__main__':
    unittest.main()
