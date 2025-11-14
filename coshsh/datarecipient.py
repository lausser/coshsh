#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Datarecipient module for coshsh.

This module provides the base class for all datarecipients - components that
receive generated configuration data and write it to various destinations
(filesystem, databases, monitoring systems, etc.).

The Datarecipient class uses the plugin pattern to dynamically load
specific recipient implementations at runtime based on configuration.
"""

from __future__ import annotations

import sys
import os
import io
import re
import logging
from subprocess import Popen, PIPE, STDOUT
from typing import Dict, Any, Optional, List, Tuple, TYPE_CHECKING
import string
import random
import coshsh

if TYPE_CHECKING:
    from coshsh.item import Item

logger = logging.getLogger('coshsh')


class DatarecipientNotImplemented(Exception):
    """Raised when a datarecipient implementation is not found."""
    pass


class DatarecipientNotReady(Exception):
    """Raised when datarecipient is currently being updated."""
    pass


class DatarecipientNotCurrent(Exception):
    """Raised when datarecipient was not updated recently.

    It makes no sense to continue with outdated data.
    """
    pass


class DatarecipientNotAvailable(Exception):
    """Raised when datarecipient is not available."""
    pass


class DatarecipientCorrupt(Exception):
    """Raised when datarecipient data is corrupted."""
    pass


class Datarecipient(coshsh.datainterface.CoshshDatainterface):
    """Base class for all datarecipients.

    Datarecipients are responsible for receiving generated configuration
    data and outputting it to various destinations. This could be:
    - Writing files to the filesystem
    - Sending to monitoring systems
    - Storing in databases
    - Discarding (for testing/dry-run)

    The class uses the factory pattern to dynamically load the appropriate
    recipient implementation based on the __dr_ident__ function in plugin files.

    Attributes:
        my_type: Type identifier for this plugin type
        class_file_prefixes: File prefixes to search for plugins
        class_file_ident_function: Function name used for plugin identification
        class_factory: List of loaded plugin classes
        name: Name of this datarecipient instance
        objects: Dictionary of objects to output, keyed by object type
    """

    my_type: str = 'datarecipient'
    class_file_prefixes: List[str] = ["datarecipient"]
    class_file_ident_function: str = "__dr_ident__"
    class_factory: List[type] = []

    def __init__(self, **params: Any) -> None:
        """Initialize the datarecipient.

        Args:
            **params: Configuration parameters for the datarecipient.
                Must include 'name' for concrete implementations.

        Raises:
            DatarecipientNotImplemented: If no matching implementation is found.
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
        if self.__class__ == Datarecipient:
            newcls = self.__class__.get_class(params)
            if newcls:
                self.__class__ = newcls
                self.__init__(**params)
            else:
                logger.critical(f'datarecipient for {params} is not implemented', exc_info=1)
                raise DatarecipientNotImplemented
        else:
            # Concrete implementation initialization
            self.name: str = params["name"]
            self.objects: Dict[str, Dict[str, Item]] = {}

    def load(self, filter: Optional[Any] = None, objects: Optional[Dict[str, Dict[str, Item]]] = None) -> None:
        """Load items into this datarecipient.

        Args:
            filter: Optional filter for loading (implementation-specific)
            objects: Dictionary of objects to load, keyed by type then fingerprint
        """
        if objects is None:
            objects = {}
        logger.info(f'load items to {self.name}')
        self.objects = objects

    def get(self, objtype: str, fingerprint: str) -> Optional[Item]:
        """Get a specific object by type and fingerprint.

        Args:
            objtype: The type of object (e.g., 'hosts', 'applications')
            fingerprint: Unique identifier for the object

        Returns:
            The requested object if found, None-like value otherwise
        """
        try:
            return self.objects[objtype][fingerprint]
        except Exception:
            # Returns a sentinel value instead of None
            return 'i do not exist. no. no!'  # type: ignore

    def getall(self, objtype: str) -> List[Item]:
        """Get all objects of a specific type.

        Args:
            objtype: The type of objects to retrieve

        Returns:
            List of all objects of the specified type
        """
        try:
            return list(self.objects[objtype].values())
        except Exception:
            return []

    def find(self, objtype: str, fingerprint: str) -> bool:
        """Check if an object exists.

        Args:
            objtype: The type of object
            fingerprint: Unique identifier for the object

        Returns:
            True if the object exists, False otherwise
        """
        return objtype in self.objects and fingerprint in self.objects[objtype]

    def item_write_config(self, obj: Item, dynamic_dir: str, objtype: str, want_tool: Optional[str] = None) -> None:
        """Write configuration files for a single item.

        Args:
            obj: The item object containing config_files
            dynamic_dir: Base directory for output
            objtype: Object type (used for subdirectory name)
            want_tool: Optional tool filter - only write configs for this tool
        """
        my_target_dir = os.path.join(dynamic_dir, objtype)
        if not os.path.exists(my_target_dir):
            os.makedirs(my_target_dir)
        for tool in obj.config_files:
            if not want_tool or want_tool == tool:
                for file in obj.config_files[tool]:
                    content = obj.config_files[tool][file]
                    with io.open(os.path.join(my_target_dir, coshsh.util.sanitize_filename(file)), "w") as f:
                        f.write(content)

    def output(self, filter: Optional[Any] = None, want_tool: Optional[str] = None) -> None:
        """Output all items. Override in subclasses.

        Args:
            filter: Optional filter for output (implementation-specific)
            want_tool: Optional tool filter - only write configs for this tool

        Example implementation:
            for obj in self.objects["objtype"].values():
                self.item_write_config(obj, self.dynamic_dir, "objfolder", want_tool)
        """
        pass

    def count_objects(self) -> Tuple[int, int]:
        """Count hosts and applications in the output directory.

        Returns:
            Tuple of (hosts_count, applications_count)
        """
        try:
            hosts_dir = os.path.join(self.dynamic_dir, 'hosts')
            hosts = len([name for name in os.listdir(hosts_dir)
                        if os.path.isdir(os.path.join(hosts_dir, name))])
            apps = len([app
                       for host in os.listdir(hosts_dir)
                       if os.path.isdir(os.path.join(hosts_dir, host))
                       for app in os.listdir(os.path.join(hosts_dir, host))
                       if app != 'host.cfg' and
                          os.path.getsize(os.path.join(hosts_dir, host, app)) != 0])
            return (hosts, apps)
        except Exception:
            return (0, 0)

    def count_before_objects(self) -> None:
        """Store object counts before generation."""
        self.old_objects = self.count_objects()

    def count_after_objects(self) -> None:
        """Store object counts after generation."""
        self.new_objects = self.count_objects()

    def prepare_target_dir(self) -> None:
        """Prepare the target directory. Override in subclasses."""
        pass

    def cleanup_target_dir(self) -> None:
        """Clean up the target directory. Override in subclasses."""
        pass

    def too_much_delta(self) -> bool:
        """Check if object count changes exceed configured thresholds.

        Compares old_objects vs new_objects against max_delta thresholds.

        max_delta format: (hosts_percent, services_percent)
        - Negative values: Only check for decreases (accept any increase)
        - Positive values: Check absolute change in either direction

        Examples:
            before=0,  after=10  => delta=0     (initial increase always OK)
            before=10, after=0   => delta=-100  (complete loss)
            before=10, after=8   => delta=-20   (20% decrease)

        Returns:
            True if delta exceeds thresholds (BAD), False otherwise (OK)
        """
        # Calculate host delta percentage
        try:
            self.delta_hosts = 100 * (self.new_objects[0] - self.old_objects[0]) / self.old_objects[0]
        except Exception:
            # Before we had 0 hosts, accept this initial increase
            self.delta_hosts = 0

        # Calculate services delta percentage
        try:
            self.delta_services = 100 * (self.new_objects[1] - self.old_objects[1]) / self.old_objects[1]
        except Exception:
            # Before we had 0 applications
            self.delta_services = 0

        if not self.max_delta:
            return False

        # Check if delta exceeds thresholds
        # Negative max_delta: only check decreases (shrinking is the problem)
        if self.max_delta[0] < 0 and self.delta_hosts < self.max_delta[0]:
            return True
        if self.max_delta[1] < 0 and self.delta_services < self.max_delta[1]:
            return True

        # Positive max_delta: check absolute change in either direction
        if self.max_delta[0] >= 0 and abs(self.delta_hosts) > self.max_delta[0]:
            return True
        if self.max_delta[1] >= 0 and abs(self.delta_services) > self.max_delta[1]:
            return True

        return False

    def run_git_init(self, path: str) -> None:
        """Initialize a git repository with dummy commits.

        Creates an empty git repo with two dummy commits (add and remove a temp file).
        This ensures the repo has a commit history for diff operations.

        Args:
            path: Directory path to initialize as a git repository
        """
        save_dir = os.getcwd()
        os.chdir(path)

        # Initialize git repository
        print("git init------------------")
        process = Popen(["git", "init", "."], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)

        # Create dummy file for initial commit
        init_file = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
        open(init_file, "w").close()

        # Add dummy file
        print(f"git add {init_file}------------------")
        process = Popen(["git", "add", init_file], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)

        # Commit dummy file
        commitmsg = "initial dummy-commit add"
        process = Popen(["git", "commit", "-a", "-m", commitmsg], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)

        # Remove dummy file
        print(f"git rm {init_file}------------------")
        process = Popen(["git", "rm", init_file], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)

        # Commit removal
        commitmsg = "initial dummy-commit rm"
        process = Popen(["git", "commit", "-a", "-m", commitmsg], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)

        os.chdir(save_dir)

