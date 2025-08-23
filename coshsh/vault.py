#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import sys
import os
import re
import logging
from typing import Dict, Any
import coshsh

logger = logging.getLogger('coshsh')


class VaultNotImplemented(Exception):
    pass


class VaultNotReady(Exception):
    # vault is currently being updated?
    pass


class VaultNotCurrent(Exception):
    # vaults was not updated lately.
    # it makes no sense to continue.
    pass


class VaultNotAvailable(Exception):
    pass


class VaultCorrupt(Exception):
    pass


class Vault(coshsh.datainterface.CoshshDatainterface):

    my_type = 'vault'
    class_file_prefixes = ["vault"]
    class_file_ident_function = "__vault_ident__"
    class_factory = []

    def __init__(self, **params: Any) -> None:
        #print("vaultinit with", self.__class__)
        for key in [k for k in params if k.startswith("recipe_")]:
            setattr(self, key, params[key])
            short = key.replace("recipe_", "")
            if not short in params:
                params[short] = params[key]
        for key in params.keys():
            if isinstance(params[key], str):
                params[key] = re.sub('%.*?%', coshsh.util.substenv, params[key])
        if self.__class__ == Vault:
            newcls = self.__class__.get_class(params)
            if newcls:
                self.__class__ = newcls
                self.__init__(**params)
            else:
                logger.critical('vault for %s is not implemented' % params, exc_info=1)
                raise VaultNotImplemented
        else:
            setattr(self, 'name', params["name"])
            # the key-value store
            self._data = {}
            pass
        # i am a generic vault
        # i find a suitable class
        # i rebless
        # i call __init__

    def open(self, **kwargs):
        pass

    def read(self, **kwargs):
        pass

    def close(self):
        pass

    def get(self, key):
        try:
            return self._data[key]
        except Exception:
            return None

    def getall(self):
        try:
            return list(self._data.values())
        except Exception:
            return []

