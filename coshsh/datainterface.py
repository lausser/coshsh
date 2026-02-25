#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""
Class factory framework for runtime plugin discovery and registration.

This module provides the base class CoshshDatainterface, which implements a
pattern where plugin .py files are discovered from configurable directory paths,
loaded at runtime, and registered via their ``ident`` functions into a
class_factory list. Subclasses (Application, MonitoringDetail, Datasource, etc.)
each set their own class_file_prefixes and class_file_ident_function to control
which files are loaded and which function is used for class selection.

This module does NOT implement any specific plugin. All concrete behavior is
delegated to the ident functions found inside the discovered plugin files. The
ident function receives a params dict and returns either a class (match) or
None (no match).

Key classes:
    CoshshDatainterface -- base class providing init_class_factory() for plugin
        discovery/loading and get_class() for selecting the right class at
        runtime based on params passed to each registered ident function.

AI agent note:
    class_factory is a mutable class-level list shared across all uses of a
    given subclass. It must be reset (via init_class_factory or direct
    assignment) between tests to prevent cross-test contamination, where
    plugins loaded in one test leak into another and cause false matches.
"""

from __future__ import annotations

import importlib.util
import inspect
import logging
import os
from pathlib import Path
from typing import Any, ClassVar, Protocol

logger = logging.getLogger('coshsh')


class IdentFunction(Protocol):
    """Callable signature for plugin ident functions (__mi_ident__, __ds_ident__, etc.)."""
    def __call__(self, params: dict[str, Any] = {}) -> type | None: ...


class CoshshDatainterface(object):

    class_factory: ClassVar[list[tuple[str, str, IdentFunction]]] = []
    class_file_prefixes: ClassVar[list[str]] = []
    class_file_ident_function: ClassVar[str] = ""
    my_type: ClassVar[str] = ""

    usage_numbers: ClassVar[dict[str, int]] = {}

    @classmethod
    def init_class_factory(cls, classpath: list[str]) -> list[tuple[str, str, IdentFunction]]:
        """Discover and register plugin classes from a list of directory paths.

        Scans each directory in classpath for .py files whose names match
        cls.class_file_prefixes. Each matching file is loaded, and if it
        contains a function named cls.class_file_ident_function, that function
        is appended to the class_factory list as a [path, module, func] triple.

        Preconditions:
            - cls.class_file_prefixes must be set to a list of filename
              prefixes (e.g. ["os_", "os."]) so the scanner knows which
              .py files to inspect.
            - cls.class_file_ident_function must be set to the name of the
              function to look for inside each plugin file (e.g. "__mi_ident__").

        Side effects:
            - Replaces cls.class_factory with the newly built list via
              update_class_factory(), discarding any previously registered
              classes.
            - Executes each discovered module at load time (via
              spec.loader.exec_module), so module-level code in plugins runs.

        Args:
            classpath: list of directory paths to search, in priority order.
                Directories listed first are considered higher priority.

        Returns:
            The new class_factory list.
        """
        # WHY: classpath is a list of paths rather than a single directory
        # because different recipes can have different class directories.
        # Paths are searched in order with catchall/default directories
        # appended last by the caller, so recipe-specific plugins are found
        # before generic fallbacks.
        class_factory = []
        for p in [p for p in reversed(classpath) if Path(p).exists() and Path(p).is_dir()]:
            for module in [item for item in sorted(os.listdir(p), reverse=True) if item[-3:] == ".py" and (item in cls.class_file_prefixes or [prefix for prefix in cls.class_file_prefixes if item.startswith(prefix)])]:
                try:
                    path = str((Path(p) / module).resolve())
                    module_name = module.replace('.py', '')

                    # Find the module
                    # WHY: importlib.util.spec_from_file_location() is used
                    # because plugin .py files are discovered at runtime from
                    # configurable directories — they are NOT on sys.path by
                    # default, so standard import (import_module) cannot find
                    # them. spec_from_file_location accepts an absolute file
                    # path, bypassing the sys.path lookup entirely.
                    spec = importlib.util.spec_from_file_location(module_name, path)
                    if spec is not None:
                        toplevel = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(toplevel)

                        for cl in inspect.getmembers(toplevel, inspect.isfunction):
                            if cl[0] == cls.class_file_ident_function:
                                class_factory.append([path, module, cl[1]])
                except Exception as exp:
                    logger.critical("could not load %s %s from %s: %s" % (cls.my_type, module, path, exp))
        cls.update_class_factory(class_factory)
        return class_factory

    @classmethod
    def update_class_factory(cls, class_factory: list[tuple[str, str, IdentFunction]]) -> None:
        cls.class_factory = class_factory

    @classmethod
    def get_class(cls, params: dict[str, Any] = {}) -> type | None:
        """Select and return the appropriate class for the given params.

        Iterates the class_factory in reverse order, calling each registered
        ident function with params. The first ident function that returns a
        non-None class wins, and that class is returned.

        Preconditions:
            - init_class_factory() must have been called at least once so
              cls.class_factory is populated; otherwise no match is possible.
            - params should be a dict containing the attributes the ident
              functions inspect to decide whether they match (e.g. host_name,
              type, address).

        Side effects:
            - Increments cls.usage_numbers[path + "___" + classname] for the
              matched class, providing a usage counter that dump_classes_usage()
              can report on.

        Args:
            params: dict of attributes to match against registered ident
                functions. Defaults to empty dict.

        Returns:
            The matched class, or None if no ident function claimed the params.
        """
        # WHY: class_factory is iterated in reverse because during
        # init_class_factory(), user-supplied / recipe-specific classes are
        # appended last (they come from the higher-priority directories that
        # are processed last due to the reversed(classpath) iteration in
        # init_class_factory). Reversing here means user classes are checked
        # first, allowing local overrides of built-in defaults without
        # patching core plugin files.
        #
        # WHY: When two ident functions both return a class for the same
        # params, the FIRST match wins (after this reversal). This means the
        # last-registered class takes priority, giving user-supplied plugins
        # precedence over earlier-registered defaults.
        for path, module, class_func in reversed(cls.class_factory):
            try:
                newcls = class_func(params)
                if newcls:
                    try:
                        cls.usage_numbers[path+"___"+newcls.__name__] += 1
                    except Exception:
                        cls.usage_numbers[path+"___"+newcls.__name__] = 1
                    return newcls
            except Exception as exp:
                print(cls.__name__+".get_class exception", exp)
        logger.debug("found no matching class for this %s %s" % (cls.my_type, params))
        return None

    @classmethod
    def dump_classes_usage(cls) -> None:
        print("Classes usage overview")
        print("count  path__class")
        for pmc in sorted(cls.usage_numbers.items(), key=lambda x: x[1]):
            print(f"{pmc[1]:6d} {pmc[0]}")
