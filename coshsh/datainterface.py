#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from __future__ import annotations

import importlib.util
import inspect
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

logger = logging.getLogger('coshsh')


class CoshshDatainterface:
    """Base class for dynamically loadable coshsh plugins.

    This class implements the plugin system that allows coshsh to discover
    and load classes from Python files at runtime. It uses a factory pattern
    where:

    1. Plugin files are discovered by scanning directories for files matching
       specific prefixes (e.g., "datasource_*.py", "os_*.py")
    2. Each plugin file must export an identification function (e.g.,
       "__ds_ident__", "__mi_ident__") that examines parameters and returns
       a class if it matches
    3. When creating an object, the factory calls identification functions
       in reverse order (to support priority/override) until one returns a class

    Class Attributes:
        class_factory: List of (path, module_name, ident_function) tuples
        class_file_prefixes: List of filename prefixes to scan for (e.g., ["datasource_"])
        class_file_ident_function: Name of the identification function to look for
        my_type: Type of plugin (e.g., "datasource", "application")
        usage_numbers: Dict tracking how many times each class was used

    Example:
        >>> # In a plugin file datasource_csv.py:
        >>> def __ds_ident__(params={}):
        ...     if params.get("type") == "csv":
        ...         return CsvDatasource
        ...
        >>> # The class factory will find and register this function
    """

    class_factory: List[Tuple[str, str, Callable]] = []
    class_file_prefixes: List[str] = []
    class_file_ident_function: str = ""
    my_type: str = ""

    usage_numbers: Dict[str, int] = {}

    @classmethod
    def init_class_factory(cls, classpath: List[str]) -> List[Tuple[str, str, Callable]]:
        """Initialize the class factory by scanning classpath for plugin files.

        This method scans directories in the classpath (in reverse order to support
        priority) for Python files matching the class_file_prefixes. For each matching
        file, it dynamically imports the module and looks for the identification
        function (e.g., __ds_ident__, __mi_ident__).

        The reverse order means:
        - User plugins (later in classpath) override default plugins
        - Within a directory, files are sorted in reverse alphabetical order

        Args:
            classpath: List of directory paths to scan for plugin files

        Returns:
            List of (absolute_path, module_name, ident_function) tuples

        Note:
            This method also updates the class_factory attribute via update_class_factory().
        """
        class_factory: List[Tuple[str, str, Callable]] = []

        # Reverse order: later paths override earlier paths (user > default)
        for p in reversed(classpath):
            if not os.path.exists(p) or not os.path.isdir(p):
                continue

            # Find all .py files matching our prefixes
            module_files = [
                item for item in sorted(os.listdir(p), reverse=True)
                if item.endswith(".py") and (
                    item in cls.class_file_prefixes or
                    any(item.startswith(prefix) for prefix in cls.class_file_prefixes)
                )
            ]

            for module in module_files:
                try:
                    path = os.path.abspath(os.path.join(p, module))
                    module_name = module.replace('.py', '')

                    # Dynamically import the module
                    spec = importlib.util.spec_from_file_location(module_name, path)
                    if spec is None or spec.loader is None:
                        logger.warning(f"Could not create spec for {path}")
                        continue

                    toplevel = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(toplevel)

                    # Look for the identification function
                    for name, func in inspect.getmembers(toplevel, inspect.isfunction):
                        if name == cls.class_file_ident_function:
                            class_factory.append((path, module, func))
                            logger.debug(f"Registered {cls.my_type} plugin: {module} from {path}")
                            break

                except Exception as exp:
                    logger.critical(
                        f"Could not load {cls.my_type} {module} from {path}: {exp}",
                        exc_info=True
                    )

        cls.update_class_factory(class_factory)
        return class_factory

    @classmethod
    def update_class_factory(cls, class_factory: List[Tuple[str, str, Callable]]) -> None:
        """Update the class factory with a new list of plugin registrations.

        Args:
            class_factory: List of (path, module_name, ident_function) tuples
        """
        cls.class_factory = class_factory

    @classmethod
    def get_class(cls, params: Optional[Dict[str, Any]] = None) -> Optional[Type]:
        """Find and return the appropriate plugin class for the given parameters.

        This method iterates through the class factory in reverse order (to support
        priority/override) and calls each identification function with the params.
        The first identification function that returns a class wins.

        Args:
            params: Dictionary of parameters to match against. The exact keys
                and values depend on the plugin type (e.g., "type", "name", etc.)

        Returns:
            The matching class, or None if no match found

        Note:
            Also updates usage_numbers to track how many times each class was used.

        Example:
            >>> params = {"type": "csv", "name": "mydata"}
            >>> datasource_class = Datasource.get_class(params)
            >>> if datasource_class:
            ...     ds = datasource_class(**params)
        """
        params = params or {}

        for path, module, class_func in reversed(cls.class_factory):
            try:
                newcls = class_func(params)
                if newcls:
                    # Track usage statistics
                    usage_key = f"{path}___{newcls.__name__}"
                    cls.usage_numbers[usage_key] = cls.usage_numbers.get(usage_key, 0) + 1
                    logger.debug(f"Matched {cls.my_type} class: {newcls.__name__} from {path}")
                    return newcls
            except Exception as exp:
                logger.error(
                    f"{cls.__name__}.get_class exception in {module}: {exp}",
                    exc_info=True
                )

        logger.debug(f"Found no matching class for {cls.my_type} with params: {params}")
        return None

    @classmethod
    def dump_classes_usage(cls) -> None:
        """Print usage statistics for all loaded plugin classes.

        Outputs a sorted list of all plugin classes that were used, along with
        how many times each was instantiated. Useful for debugging and optimization.

        Example output:
            Classes usage overview
            count  path__class
                 1 /path/to/datasource_csv.py___CsvFile
                12 /path/to/os_linux.py___Linux
               123 /path/to/os_windows.py___Windows
        """
        print("Classes usage overview")
        print("count  path__class")
        for path_class, count in sorted(cls.usage_numbers.items(), key=lambda x: x[1]):
            print(f"{count:6d} {path_class}")

