#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""
Base class for reading inventory data from external sources and creating
Host, Application, and Contact objects.

This module defines the Datasource base class, which all datasource plugins
must subclass. A datasource is responsible for *reading* inventory data
(hosts, applications, contacts, monitoring details, etc.) from an external
source such as a CSV file, a CMDB database, or an LDAP directory. It does
NOT write output files -- that is the responsibility of Datarecipient
(see coshsh/datarecipient.py).

Key classes:
    Datasource              -- Abstract base for all datasource plugins.
    DatasourceNotAvailable  -- Raised when the source cannot be reached.
    DatasourceNotCurrent    -- Raised when the source data is stale.
    DatasourceNotReady      -- Raised when the source is temporarily busy.
    DatasourceNotImplemented -- Raised when no matching plugin is found.
    DatasourceCorrupt       -- Raised when the source data is structurally invalid.

AI agent note:
    Every datasource plugin module must implement a module-level function
    called ``__ds_ident__`` that returns a dict describing the datasource
    type it handles. The Datasource factory uses this function to discover
    and match plugins to datasource configurations at runtime.
"""

import sys
import os
import re
import logging
import socket
import coshsh

logger = logging.getLogger('coshsh')


# WHY: The exception hierarchy below encodes distinct failure semantics so that
# the recipe runner can decide how to react to each case:
#   - DatasourceNotAvailable  -- the source is unreachable (network down, file
#     missing, credentials rejected). The recipe may skip this datasource and
#     continue with others.
#   - DatasourceNotCurrent    -- the source *is* reachable but its data has not
#     been refreshed within an acceptable time window. Continuing would produce
#     stale monitoring configuration, so the recipe should abort.
#   - DatasourceNotReady      -- the source is temporarily busy (e.g. another
#     process is writing to it). The recipe can retry later.

class DatasourceNotImplemented(Exception):
    pass


class DatasourceNotReady(Exception):
    # WHY: Raised when the datasource is currently being updated by another
    # process. The caller should back off and retry rather than abort.
    pass


class DatasourceNotCurrent(Exception):
    # WHY: Raised when the datasource has not been updated recently enough.
    # Continuing with stale data would produce incorrect monitoring configs,
    # so the recipe should treat this as a fatal error.
    pass


class DatasourceNotAvailable(Exception):
    # WHY: Raised when the datasource cannot be contacted at all (e.g. the
    # database is down, the CSV file is missing). The recipe may choose to
    # skip this datasource and proceed with the remaining ones.
    pass


class DatasourceCorrupt(Exception):
    # WHY: Raised when the datasource data is structurally invalid and cannot
    # be parsed meaningfully.
    pass


class Datasource(coshsh.datainterface.CoshshDatainterface):
    """Base class for all datasource plugins.

    A Datasource reads inventory data from an external source and populates
    an internal ``objects`` dict with Host, Application, Contact (and other)
    objects. The recipe later merges these objects across all configured
    datasources.

    Subclasses must override ``open()``, ``read()``, and ``close()`` to
    implement source-specific logic.
    """

    my_type = 'datasource'
    class_file_prefixes = ["datasource"]
    # WHY: class_file_ident_function names the module-level function that every
    # datasource plugin must define. The factory in CoshshDatainterface calls
    # this function to decide which plugin class handles a given datasource
    # configuration block.
    class_file_ident_function = "__ds_ident__"
    class_factory = []

    def __init__(self, **params):
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
            # WHY: hostname_transform_ops is a list of string operations
            # (e.g. "strip_domain", "to_lower") parsed from the config's
            # comma-separated "hostname_transform" value. Transforms are
            # applied in left-to-right order as configured, so the user
            # controls the pipeline precisely. For example,
            # "strip_domain,to_lower" first removes the domain suffix and
            # *then* lowercases, which differs from the reverse order when
            # the domain contains uppercase characters.
            self.hostname_transform_ops = []
            if "hostname_transform" in params and params["hostname_transform"]:
                self.hostname_transform_ops = [op.strip() for op in params["hostname_transform"].split(",")]
            # WHY: objects is a two-level dict: {type_string: {fingerprint: object}}.
            # The outer key is a type tag such as "hosts", "applications", or
            # "contacts". The inner key is the object's fingerprint (typically
            # the hostname or a composite key). Using fingerprints as inner
            # keys provides automatic deduplication: if the same host appears
            # in two datasources, the later one silently overwrites the
            # earlier entry, ensuring each logical entity exists exactly once
            # in the final merged result.
            self.objects = {}
            pass
        # i am a generic datasource
        # i find a suitable class
        # i rebless
        # i call __init__

    # WHY: open(), read(), and close() are separate methods rather than a single
    # load() because some datasources require explicit connection lifecycle
    # management. For example, a database datasource must open a connection
    # (or acquire one from a pool), execute queries in read(), and then release
    # the connection in close(). An LDAP datasource must bind before searching
    # and unbind afterwards. Splitting the lifecycle lets the recipe runner
    # guarantee cleanup (close) even when read() raises an exception.

    def open(self, **kwargs):
        """Establish a connection or prepare the datasource for reading.

        Subclasses override this to perform setup such as opening a database
        connection, binding to an LDAP server, or verifying that a CSV file
        exists and is readable. The base implementation is a no-op.
        """
        pass

    def read(self, **kwargs):
        """Read inventory data from the source and populate ``self.objects``.

        Subclasses override this to fetch hosts, applications, contacts, and
        other objects from the external source, instantiate the corresponding
        coshsh model objects, and store them via ``self.add()``. The base
        implementation is a no-op.
        """
        pass

    def close(self):
        """Release resources acquired by ``open()``.

        Subclasses override this to close database connections, unbind from
        LDAP, or perform any other cleanup. The recipe runner calls this even
        when ``read()`` raises an exception, so implementations should be
        tolerant of partially-initialised state. The base implementation is
        a no-op.
        """
        pass

    def add(self, objtype, obj):
        """Store an inventory object in this datasource's objects dict.

        Args:
            objtype: A type tag string such as ``"hosts"``, ``"applications"``,
                or ``"contacts"``.
            obj: A coshsh model object that implements ``fingerprint()``
                (returning a deduplication key, typically the hostname or a
                composite identifier).

        The object is filed under ``self.objects[objtype][obj.fingerprint()]``.
        If an object with the same fingerprint already exists, it is silently
        overwritten (this is the intended deduplication behaviour). When adding
        an application, the method also links it to its host object if the
        host has already been added.
        """
        try:
            self.objects[objtype][obj.fingerprint()] = obj
        except Exception:
            self.objects[objtype] = {}
            self.objects[objtype][obj.fingerprint()] = obj
        if objtype == 'applications':
            if self.find('hosts', obj.host_name):
                setattr(obj, 'host', self.get('hosts', obj.host_name))
        obj.record_in_chronicle(f"added to {objtype} in datasource {self.name}")

    def get(self, objtype, fingerprint):
        """Retrieve a single object by type and fingerprint.

        Args:
            objtype: The type tag string (e.g. ``"hosts"``).
            fingerprint: The deduplication key returned by the object's
                ``fingerprint()`` method.

        Returns:
            The matching object, or ``None`` if not found.
        """
        try:
            return self.objects[objtype][fingerprint]
        except Exception:
            # should be None
            return None
            return 'i do not exist. no. no!'

    def getall(self, objtype):
        try:
            return list(self.objects[objtype].values())
        except Exception:
            return []

    def find(self, objtype, fingerprint):
        return objtype in self.objects and fingerprint in self.objects[objtype]

    def transform_hostname(self, hostname):
        """Apply the configured chain of hostname transformations.

        Transforms are executed in the left-to-right order specified by the
        ``hostname_transform`` configuration parameter. Each operation
        receives the result of the previous one, forming a pipeline.

        Supported operations:
            strip_domain  -- Remove everything after the first dot (skipped
                             for bare IP addresses).
            to_lower      -- Lowercase the entire hostname.
            to_upper      -- Uppercase the entire hostname.
            append_domain -- Resolve the FQDN via ``socket.getfqdn()``.
            resolve_ip    -- Reverse-resolve an IP address to a hostname.
            resolve_dns   -- Forward-resolve to FQDN via ``socket.getfqdn()``.

        Args:
            hostname: The raw hostname string as read from the datasource.

        Returns:
            The transformed hostname string.
        """
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
