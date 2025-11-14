#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Vault module for coshsh secret management.

This module provides the base class for all vault implementations - components
that securely store and retrieve secrets (passwords, API keys, certificates, etc.).

Vaults use the plugin pattern to dynamically load specific implementations
at runtime (e.g., encrypted files, HashiCorp Vault, AWS Secrets Manager).
"""

from __future__ import annotations

import sys
import os
import re
import logging
from typing import Dict, Any, Optional, List
import coshsh

logger = logging.getLogger('coshsh')


class VaultNotImplemented(Exception):
    """Raised when a vault implementation is not found."""
    pass


class VaultNotReady(Exception):
    """Raised when vault is currently being updated."""
    pass


class VaultNotCurrent(Exception):
    """Raised when vault was not updated recently.

    It makes no sense to continue with outdated vault data.
    """
    pass


class VaultNotAvailable(Exception):
    """Raised when vault is not available."""
    pass


class VaultCorrupt(Exception):
    """Raised when vault data is corrupted."""
    pass


class Vault(coshsh.datainterface.CoshshDatainterface):
    """Base class for all vault implementations.

    Vaults provide secure storage and retrieval of secrets. The class uses
    the factory pattern to dynamically load the appropriate vault implementation
    based on the __vault_ident__ function in plugin files.

    Typical workflow:
        1. Create vault instance: vault = Vault(name="my_vault", ...)
        2. Open connection: vault.open()
        3. Read secrets: vault.read()
        4. Access secrets: value = vault.get("secret_key")
        5. Close connection: vault.close()

    Attributes:
        my_type: Type identifier for this plugin type
        class_file_prefixes: File prefixes to search for plugins
        class_file_ident_function: Function name used for plugin identification
        class_factory: List of loaded plugin classes
        name: Name of this vault instance
        _data: Internal key-value store for secrets
    """

    my_type: str = 'vault'
    class_file_prefixes: List[str] = ["vault"]
    class_file_ident_function: str = "__vault_ident__"
    class_factory: List[type] = []

    def __init__(self, **params: Any) -> None:
        """Initialize the vault.

        Args:
            **params: Configuration parameters for the vault.
                Must include 'name' for concrete implementations.

        Raises:
            VaultNotImplemented: If no matching implementation is found.
        """
        # Handle recipe_ prefixed parameters
        for key in [k for k in params if k.startswith("recipe_")]:
            setattr(self, key, params[key])
            short = key.replace("recipe_", "")
            if short not in params:
                params[short] = params[key]

        # Substitute environment variables in string parameters
        for key in params.keys():
            if isinstance(params[key], str):
                params[key] = re.sub('%.*?%', coshsh.util.substenv, params[key])

        # Factory pattern: if called on base class, find and instantiate the right subclass
        if self.__class__ == Vault:
            newcls = self.__class__.get_class(params)
            if newcls:
                self.__class__ = newcls
                self.__init__(**params)
            else:
                logger.critical(f'vault for {params} is not implemented', exc_info=1)
                raise VaultNotImplemented
        else:
            # Concrete implementation initialization
            self.name: str = params["name"]
            # The key-value store for secrets
            self._data: Dict[str, Any] = {}

    def open(self, **kwargs: Any) -> None:
        """Open connection to the vault. Override in subclasses.

        Args:
            **kwargs: Implementation-specific connection parameters
        """
        pass

    def read(self, **kwargs: Any) -> None:
        """Read secrets from the vault. Override in subclasses.

        Implementations should populate self._data with key-value pairs.

        Args:
            **kwargs: Implementation-specific read parameters
        """
        pass

    def close(self) -> None:
        """Close connection to the vault. Override in subclasses."""
        pass

    def get(self, key: str) -> Optional[Any]:
        """Get a secret value by key.

        Args:
            key: Secret key to retrieve

        Returns:
            Secret value if found, None otherwise
        """
        try:
            return self._data[key]
        except Exception:
            return None

    def getall(self) -> List[Any]:
        """Get all secret values.

        Returns:
            List of all secret values (without keys)
        """
        try:
            return list(self._data.values())
        except Exception:
            return []

