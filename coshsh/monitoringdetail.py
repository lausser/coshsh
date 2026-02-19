#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Base class for monitoring detail objects -- typed key/value bundles that
carry datasource-specific monitoring parameters (filesystems, URLs, ports,
credentials, custom macros, etc.) from a datasource into an Application or
Host.

Sole responsibility: accept a flat ``params`` dict from a datasource row,
look up the correct detail subclass via the class factory, and instantiate
it so that ``Item.resolve_monitoring_details()`` can later merge the detail's
payload onto the parent object.

Does NOT: render templates, discover plugin files (that is
``CoshshDatainterface.init_class_factory``), or decide *which* details
belong to which application (that is the datasource's job).

Key classes:
    MonitoringDetail -- dispatching base class. Constructing
        ``MonitoringDetail(params)`` mutates ``self.__class__`` to the
        matching subclass found via ``get_class(params)``.
    MonitoringDetailNotImplemented -- raised when no registered subclass
        matches the given ``monitoring_type``.

Subclass protocol (implemented in ``detail_*.py`` plugin files):
    Each subclass sets class-level attributes that control how
    ``Item.resolve_monitoring_details()`` merges the detail onto its parent:

    ``property``           Target attribute name on the parent object (e.g.
                           ``"filesystems"``, ``"login"``).  The special
                           value ``"generic"`` bypasses the normal merge and
                           sets/extends arbitrary attributes via a
                           ``dictionary`` mapping.
    ``property_type``      One of ``str``, ``list``, or ``dict``:
                           - ``str``  -- the detail object (or, with
                             ``property_flat``, one of its attributes) is
                             assigned directly: ``parent.<property> = detail``.
                           - ``list`` -- the detail is appended to a list:
                             ``parent.<property>.append(detail)``.
                           - ``dict`` -- the detail's ``key``/``value`` pair
                             is inserted: ``parent.<property>[key] = value``.
    ``property_attr``      (optional) When set on a list-typed detail, only
                           this single attribute is appended instead of the
                           whole detail object.  Example:
                           ``MonitoringDetailTag`` has ``property_attr = "tag"``
                           so ``application.tags`` becomes a flat list of
                           strings, not a list of detail objects.
    ``property_flat``      (optional, bool) When True and ``property_type``
                           is ``str``, assigns ``getattr(detail, property)``
                           instead of the detail object itself.
    ``unique_attribute``   (optional) When set on a list-typed detail,
                           deduplicates entries: if an existing element in
                           the list has the same value for this attribute,
                           it is replaced rather than duplicated.  Example:
                           ``MonitoringDetailFilesystem`` sets
                           ``unique_attribute = "path"`` so that a second
                           FILESYSTEM row for the same mount point overwrites
                           the first.

AI agent note:
    The ``monitoring_0`` through ``monitoring_N`` positional params are the
    canonical transport format.  Datasources (CSV files, CMDB queries, etc.)
    provide a fixed set of generic columns; each detail subclass maps those
    positional columns to meaningful attribute names in its own ``__init__``.
    The base-class comparison operators use ``monitoring_0`` because it is
    the only positional column guaranteed to exist across all detail types.
"""

import sys
import os
import logging
from urllib.parse import urlparse
import coshsh

logger = logging.getLogger('coshsh')


class MonitoringDetailNotImplemented(Exception):
    """Raised when no registered detail subclass matches the ``monitoring_type``
    in the params dict passed to ``MonitoringDetail.__init__``."""
    pass


# WHY: MonitoringDetail uses a class factory pattern (inherited from
# CoshshDatainterface) instead of a simple subclass registry because detail
# types are defined in external plugin files (``detail_*.py``) that may live
# in recipe-specific directories.  The ``__detail_ident__`` function in each
# plugin file inspects ``params["monitoring_type"]`` and returns the
# appropriate subclass (or None).  This allows new detail types to be added
# without modifying this module -- just drop a ``detail_*.py`` file into the
# recipe's classes directory.
class MonitoringDetail(coshsh.item.Item):
    """Dispatching base class for all monitoring detail types.

    When ``MonitoringDetail(params)`` is called directly, ``__init__``
    queries the class factory to find the subclass matching
    ``params["monitoring_type"]`` (e.g. ``"FILESYSTEM"``, ``"URL"``,
    ``"LOGIN"``).  It then mutates ``self.__class__`` to that subclass
    and re-invokes ``__init__`` so that the subclass can unpack the
    positional ``monitoring_0..N`` params into named attributes.

    When a subclass ``__init__`` is called (the ``else: pass`` branch),
    no dispatching occurs -- the subclass is responsible for its own
    initialisation.
    """

    # WHY: class_factory is a class-level list populated by
    # CoshshDatainterface.init_class_factory() from ``detail_*.py`` plugin
    # files.  Each entry is a [path, module, ident_func] triple.  The base
    # class get_class() iterates this list, calling each ident_func(params)
    # until one returns a class.
    class_factory = []
    class_file_prefixes = ["detail_"]
    class_file_ident_function = "__detail_ident__"
    my_type = "detail"
    lower_columns = ['name', 'type', 'application_name', 'application_type']

    def __init__(self, params):
        """Dispatch to the correct detail subclass based on ``monitoring_type``.

        When called on the base ``MonitoringDetail`` class, this method:
        1. Lowercases identification columns (name, type, etc.).
        2. Normalises ``name``/``type`` to ``application_name``/``application_type``.
        3. Looks up the matching subclass via ``get_class(params)``.
        4. Mutates ``self.__class__`` and re-invokes ``__init__`` so the
           subclass can unpack ``monitoring_0..N`` into named attributes.

        Raises ``MonitoringDetailNotImplemented`` if no subclass matches.

        When called on a subclass (the ``else: pass`` branch), does nothing
        -- the subclass ``__init__`` handles its own setup.
        """
        if self.__class__.__name__ == "MonitoringDetail":
            for c in self.__class__.lower_columns:
                try:
                    params[c] = params[c].lower()
                except Exception:
                    if c in params:
                        params[c] = None
            # name, type is preferred, because a detail can also be a host detail
            # application_name, application_type is ok too. in any case these will be internally used
            if 'name' in params:
                params['application_name'] = params['name']
                del params['name']
            if 'type' in params:
                params['application_type'] = params['type']
                del params['type']
            newcls = self.__class__.get_class(params)
            if newcls:
                # WHY: self.__class__ is mutated in-place rather than
                # constructing a new object because the caller already holds
                # a reference to this instance (e.g. datasource code does
                # ``MonitoringDetail(params)`` and immediately appends the
                # result).  Mutating the class lets the same object become
                # the correct subclass transparently.
                self.__class__ = newcls
                super(MonitoringDetail, self).__init__(params)
                self.__init__(params)
            else:
                logger.info("monitoring detail of type %s for host %s / appl %s had a problem" % (params["monitoring_type"], params.get("host_name", "unkn. host"), params.get("application_name", "unkn. application")))
                raise MonitoringDetailNotImplemented
        else:
            pass

    def fingerprint(self):
        """Return a unique identity for this detail instance.

        Unlike Host or Application, details have no stable natural key
        (their attributes are type-specific and unpredictable), so this
        returns the Python object id.  The fingerprint is used by
        ``Item.add('details', ...)`` for deduplication in the recipe's
        detail collection.
        """
        # it does not make sense to construct an id from the random attributes
        # id is used in self.add('details')
        return id(self)

    def application_fingerprint(self):
        """Return the fingerprint of the application (or host) this detail belongs to.

        Used by the recipe to route a detail to the correct application
        object after the datasource has collected all details.  Falls back
        to host_name alone when no application identity is available (i.e.
        the detail is a host-level detail rather than an application-level
        detail).
        """
        if hasattr(self, 'application_name') and self.application_name and hasattr(self, 'application_type') and self.application_type:
            return "%s+%s+%s" % (self.host_name, self.application_name, self.application_type)
        elif self.host_name:
            return "%s" % (self.host_name, )
        raise "impossible fingerprint"

    # WHY: comparison operators use the tuple (monitoring_type, monitoring_0)
    # instead of named attributes because named attributes vary by subclass
    # (e.g. "path" for FILESYSTEM, "url" for URL, "port" for PORT).  The
    # positional monitoring_0 is the only payload column guaranteed to exist
    # across all detail types, making it the lowest common denominator for
    # sorting and equality.  This matters because recipe.py sorts detail
    # lists after resolution to produce deterministic output order.
    def __eq__(self, other):
        return ((self.monitoring_type, str(self.monitoring_0)) == (other.monitoring_type, str(other.monitoring_0)))

    def __ne__(self, other):
        return ((self.monitoring_type, str(self.monitoring_0)) != (other.monitoring_type, str(other.monitoring_0)))

    def __lt__(self, other):
        return ((self.monitoring_type, str(self.monitoring_0)) < (other.monitoring_type, str(other.monitoring_0)))

    def __le__(self, other):
        return ((self.monitoring_type, str(self.monitoring_0)) <= (other.monitoring_type, str(other.monitoring_0)))

    def __gt__(self, other):
        return ((self.monitoring_type, str(self.monitoring_0)) > (other.monitoring_type, str(other.monitoring_0)))

    def __ge__(self, other):
        return ((self.monitoring_type, str(self.monitoring_0)) >= (other.monitoring_type, str(other.monitoring_0)))

    def __repr__(self):
        return "%s %s" % (self.monitoring_type, str(self.monitoring_0))

