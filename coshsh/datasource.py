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
import socket
from typing import Dict, Any, List, Optional
import coshsh

logger = logging.getLogger('coshsh')


class DatasourceNotImplemented(Exception):
    pass


class DatasourceNotReady(Exception):
    # datasource is currently being updated
    pass


class DatasourceNotCurrent(Exception):
    # datasources was not updated lately.
    # it makes no sense to continue.
    pass


class DatasourceNotAvailable(Exception):
    pass


class DatasourceCorrupt(Exception):
    pass


class Datasource(coshsh.datainterface.CoshshDatainterface):

    my_type = 'datasource'
    class_file_prefixes = ["datasource"]
    class_file_ident_function = "__ds_ident__"
    class_factory = []

    def __init__(self, **params: Any) -> None:
        #print "datasourceinit with", self.__class__
        for key in [k for k in params if k.startswith("recipe_")]:
            setattr(self, key, params[key])
            short = key.replace("recipe_", "")
            if not short in params:
                params[short] = params[key]
        for key in params.keys():
            if isinstance(params[key], str):
                params[key] = re.sub('%.*?%', coshsh.util.substenv, params[key])
        if self.__class__ == Datasource:
            #print "generic ds", params
            newcls = self.__class__.get_class(params)
            if newcls:
                #print "i rebless anon datasource to", newcls, params
                self.__class__ = newcls
                self.__init__(**params)
            else:
                logger.critical('datasource for %s is not implemented' % params, exc_info=1)
                #print "i raise DatasourceNotImplemented"
                raise DatasourceNotImplemented
        else:
            setattr(self, 'name', params["name"])
            self.hostname_transform_ops = []
            if "hostname_transform" in params and params["hostname_transform"]:
                self.hostname_transform_ops = [op.strip() for op in params["hostname_transform"].split(",")]
            self.objects = {}
            pass
        # i am a generic datasource
        # i find a suitable class
        # i rebless
        # i call __init__

    def open(self, **kwargs: Any) -> None:
        pass

    def read(self, **kwargs: Any) -> None:
        pass

    def close(self) -> None:
        pass

    def add(self, objtype: str, obj: Any) -> None:
        try:
            self.objects[objtype][obj.fingerprint()] = obj
        except Exception:
            self.objects[objtype] = {}
            self.objects[objtype][obj.fingerprint()] = obj
        if objtype == 'applications':
            if self.find('hosts', obj.host_name):
                setattr(obj, 'host', self.get('hosts', obj.host_name))
        obj.record_in_chronicle(f"added to {objtype} in datasource {self.name}")

    def get(self, objtype: str, fingerprint: str) -> Optional[Any]:
        try:
            return self.objects[objtype][fingerprint]
        except Exception:
            # should be None
            return None
            return 'i do not exist. no. no!'

    def getall(self, objtype: str) -> List[Any]:
        try:
            return list(self.objects[objtype].values())
        except Exception:
            return []

    def find(self, objtype: str, fingerprint: str) -> bool:
        return objtype in self.objects and fingerprint in self.objects[objtype]

    def transform_hostname(self, hostname: str) -> str:
        original = hostname

        def is_ip(s):
            try:
                socket.inet_aton(s)
                return True
            except socket.error:
                return False

        for op in self.hostname_transform_ops:
            if op == "strip_domain":
                if not is_ip(hostname):
                    hostname = hostname.split('.')[0]
            elif op == "to_lower":
                hostname = hostname.lower()
            elif op == "to_upper":
                hostname = hostname.upper()
            elif op == "append_domain":
                try:
                    fqdn = socket.getfqdn(hostname)
                    hostname = fqdn
                except Exception as e:
                    logger.warning(f"append_domain failed for {hostname}: {e}")
            elif op == "resolve_ip":
                if is_ip(hostname):
                    try:
                        hostname = socket.gethostbyaddr(hostname)[0]
                    except Exception as e:
                        logger.warning(f"resolve_ip failed for {hostname}: {e}")
            elif op == "resolve_dns":
                try:
                    hostname = socket.getfqdn(hostname)
                except Exception as e:
                    logger.warning(f"resolve_dns failed for {hostname}: {e}")
            else:
                logger.warning(f"Unknown hostname transform operation: {op}")

        logger.debug(f"Transformed hostname: {original} -> {hostname}")
        return hostname
