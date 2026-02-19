#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""
Base class and exceptions for datarecipients -- the output side of coshsh.

A datarecipient is responsible for writing rendered monitoring configuration
files to a target directory (the "dynamic_dir") and managing the lifecycle of
that output: cleaning old files, counting objects before and after, detecting
dangerous deltas, and optionally committing via git.

Does NOT: render templates, resolve monitoring details, or read data from any
source. Those responsibilities belong to Item/Application (rendering) and
Datasource (reading). A datarecipient only receives already-rendered
config_files dicts and persists them to disk.

Key classes:
    Datarecipient -- abstract base providing the plugin-dispatch __init__,
        object counting, delta detection, the for_tool/want_tool file-routing
        mechanism, and git-init scaffolding. Concrete subclasses (loaded at
        runtime via the class_factory) override output(), prepare_target_dir(),
        and cleanup_target_dir().

    Exception hierarchy:
        DatarecipientNotImplemented -- no plugin matched the requested type.
        DatarecipientNotReady -- target is locked / being updated.
        DatarecipientNotCurrent -- stale target, abort.
        DatarecipientNotAvailable -- target unreachable or command failed.
        DatarecipientCorrupt -- target data integrity check failed.

AI agent note:
    The for_tool / want_tool routing is a two-level dict key system:
    config_files[tool][filename] stores rendered content.  TemplateRule.for_tool
    (default "nagios") determines under which tool key a template's output is
    stored at render time.  At write time, item_write_config's want_tool
    parameter filters which tool's files to actually emit, letting a single
    object carry configs for multiple tools (nagios, prometheus, etc.) while
    each datarecipient only writes the files it cares about.
"""

import sys
import os
import io
import re
import logging
from subprocess import Popen, PIPE, STDOUT
import string
import random
import coshsh

logger = logging.getLogger('coshsh')


class DatarecipientNotImplemented(Exception):
    """Raised when no plugin's __dr_ident__ function matched the requested type."""
    pass


class DatarecipientNotReady(Exception):
    """Raised when the target directory is locked or currently being updated."""
    # datarecipient is currently being updated
    pass


class DatarecipientNotCurrent(Exception):
    """Raised when the target was not updated recently and continuing is unsafe."""
    # datarecipients was not updated lately.
    # it makes no sense to continue.
    pass


class DatarecipientNotAvailable(Exception):
    """Raised when the target is unreachable or a shell command failed."""
    pass


class DatarecipientCorrupt(Exception):
    """Raised when the target data fails an integrity check."""
    pass


class Datarecipient(coshsh.datainterface.CoshshDatainterface):
    """Abstract base for all datarecipient plugins.

    Inherits the class_factory / plugin-dispatch machinery from
    CoshshDatainterface.  When instantiated directly (i.e. not via a
    subclass), __init__ calls get_class() to find the concrete subclass
    matching the params and re-assigns self.__class__, then re-runs
    __init__ on the now-concrete instance.

    Subclasses must override at least output() to do useful work.
    They typically also override prepare_target_dir() and
    cleanup_target_dir().
    """

    my_type = 'datarecipient'
    class_file_prefixes = ["datarecipient"]
    class_file_ident_function = "__dr_ident__"
    class_factory = []

    def __init__(self, **params):
        """Dispatch to the correct subclass or initialise a concrete instance.

        When called on the base Datarecipient class, uses the class_factory
        to find a matching subclass (via __dr_ident__ functions), re-assigns
        self.__class__, and calls __init__ again.  When called on an already-
        concrete subclass, just stores the name and initialises self.objects.

        Params whose keys start with ``recipe_`` are also exposed under the
        short name (without the prefix), and all string values undergo
        environment-variable substitution via ``%VAR%`` patterns.
        """
        for key in [k for k in params if k.startswith("recipe_")]:
            setattr(self, key, params[key])
            short = key.replace("recipe_", "")
            if not short in params:
                params[short] = params[key]
        for key in params.keys():
            if isinstance(params[key], str):
                params[key] = re.sub('%.*?%', coshsh.util.substenv, params[key])
        if self.__class__ == Datarecipient:
            newcls = self.__class__.get_class(params)
            if newcls:
                self.__class__ = newcls
                self.__init__(**params)
            else:
                logger.critical('datarecipient for %s is not implemented' % params, exc_info=1)
                raise DatarecipientNotImplemented
        else:
            setattr(self, 'name', params["name"])
            self.objects = {}

    def load(self, filter=None, objects={}):
        """Accept the rendered objects dict from the recipe for later output.

        Stores a reference to the objects dict (keyed by type, e.g.
        'hosts', 'applications') so that output() can iterate over them.
        Subclasses may override to apply filter logic.
        """
        logger.info('load items to %s' % (self.name, ))
        self.objects = objects

    def get(self, objtype, fingerprint):
        """Return a single object by type and fingerprint, or a sentinel string if missing."""
        try:
            return self.objects[objtype][fingerprint]
        except Exception:
            # should be None
            return 'i do not exist. no. no!'

    def getall(self, objtype):
        """Return all objects of the given type, or an empty list if none exist."""
        try:
            return self.objects[objtype].values()
        except Exception:
            return []

    def find(self, objtype, fingerprint):
        """Return True if an object with the given type and fingerprint exists."""
        return objtype in self.objects and fingerprint in self.objects[objtype]

    def item_write_config(self, obj, dynamic_dir, objtype, want_tool=None):
        """Write one object's rendered config files to disk.

        Iterates over obj.config_files, a two-level dict keyed as
        config_files[tool][filename].  If want_tool is given, only files
        under that tool key are written; otherwise all tools are written.

        Args:
            obj: An Item (Host, Application, etc.) with a config_files dict.
            dynamic_dir: Root output directory.
            objtype: Subdirectory name under dynamic_dir (e.g. "hosts/hostname").
            want_tool: If set, only write files for this monitoring tool key
                (e.g. "nagios", "prometheus").  None means write all.
        """
        # WHY: The for_tool routing mechanism -- config_files is a two-level
        # dict: config_files[tool_name][filename] = content.  At render time,
        # TemplateRule.for_tool (default "nagios") determines which tool key
        # the rendered output is stored under.  Here at write time, want_tool
        # filters which tool's files this recipient actually emits.  This lets
        # a single object carry configs for multiple tools (nagios, prometheus,
        # etc.) while each datarecipient writes only the subset it is
        # responsible for.
        my_target_dir = os.path.join(dynamic_dir, objtype)
        if not os.path.exists(my_target_dir):
            os.makedirs(my_target_dir)
        for tool in obj.config_files:
            if not want_tool or want_tool == tool:
                for file in obj.config_files[tool]:
                    content = obj.config_files[tool][file]
                    with io.open(os.path.join(my_target_dir, coshsh.util.sanitize_filename(file)), "w") as f:
                        f.write(content)

    def output(self, filter=None, want_tool=None):
        """Write all loaded objects to the target directory.

        This is a no-op in the base class.  Concrete subclasses override
        this to iterate over self.objects and call item_write_config() for
        each object type they handle.  The commented-out code below shows
        the intended pattern.
        """
        pass
        # for obj in self-objects["objtype"].values():
        #     self.item_write_config(obj, self.dynamic_dir, "objfolder", want_tool)

    def count_objects(self):
        """Count host directories and non-empty application files on disk.

        Returns a (hosts, apps) tuple.  This is a filesystem-level count
        of what has actually been written, not an in-memory count.

        Returns:
            Tuple of (host_count, app_count).  Returns (0, 0) if the
            directory does not exist or is unreadable.
        """
        # WHY: count_before/count_after delta tracking -- the recipe calls
        # count_before_objects() before cleanup+output and count_after_objects()
        # after output.  Both store their result so that too_much_delta() can
        # compare old vs new counts.  This filesystem-level counting (rather
        # than in-memory len(self.objects)) is deliberate: it measures what
        # was ACTUALLY written to disk, which is what the monitoring system
        # will read.  If rendering silently produced fewer files (e.g. due to
        # a datasource returning incomplete data), the disk count catches it.
        try:
            hosts = len([name for name in os.listdir(os.path.join(self.dynamic_dir, 'hosts')) if os.path.isdir(os.path.join(self.dynamic_dir, 'hosts', name))])
            apps = len([app for host in os.listdir(os.path.join(self.dynamic_dir, 'hosts')) if os.path.isdir(os.path.join(self.dynamic_dir, 'hosts', host)) for app in os.listdir(os.path.join(self.dynamic_dir, 'hosts', host)) if app != 'host.cfg' and os.path.getsize(os.path.join(self.dynamic_dir, 'hosts', host, app)) != 0])
            return (hosts, apps)
        except Exception:
            return (0, 0)

    def count_before_objects(self):
        """Snapshot the current on-disk object counts before output runs.

        Stores the result in self.old_objects for later comparison by
        too_much_delta().  Called by the recipe before cleanup_target_dir().
        """
        self.old_objects = self.count_objects()

    def count_after_objects(self):
        """Snapshot the on-disk object counts after output has written files.

        Stores the result in self.new_objects.  Called by subclass output()
        methods after writing all config files.  The delta between
        self.old_objects and self.new_objects drives too_much_delta().
        """
        self.new_objects = self.count_objects()

    def prepare_target_dir(self):
        """Create required subdirectories in the target output directory.

        No-op in the base class.  Subclasses override to create
        hosts/, hostgroups/, etc. under self.dynamic_dir.
        """
        pass

    def cleanup_target_dir(self):
        """Remove old generated files from the target directory before output.

        No-op in the base class.  Subclasses override to remove stale
        content (e.g. shutil.rmtree) while preserving .git if present.
        """
        pass

    def too_much_delta(self):
        """Check whether the change in object counts exceeds the allowed threshold.

        Compares self.old_objects (before) with self.new_objects (after) and
        computes the percentage change for hosts and applications.  Returns
        True if the change exceeds the bounds defined by self.max_delta,
        meaning the output should be considered suspect and possibly reverted.

        Returns:
            True if the delta is dangerously large, False otherwise.
            Also returns False if self.max_delta is not set (no limit).
        """
        # self.old_objects = (hosts_before, apps_before)
        # self.new_objects = (hosts_after, apps_after)
        # self.max_delta = (%hosts, %apps)
        #
        # WHY: Positive vs negative max_delta semantics --
        # max_delta is a tuple of two percentage thresholds, one for hosts and
        # one for apps/services.  The sign controls which direction of change
        # is guarded:
        #
        #   Negative max_delta (e.g. -20):
        #     Only guards against SHRINKAGE.  An increase of any size is
        #     accepted.  This is the common safety mode: if a datasource
        #     suddenly returns far fewer hosts (e.g. database connectivity
        #     issue), coshsh should not blindly delete the config for those
        #     hosts.  But if new hosts appear, that is always safe.
        #     Triggers when: delta_hosts < max_delta[0] (i.e. shrunk more
        #     than the threshold).
        #
        #   Positive max_delta (e.g. 20):
        #     Guards against change in EITHER direction.  Any change larger
        #     than the threshold (increase or decrease) is flagged.  This is
        #     stricter and used when unexpected growth is also suspicious.
        #     Triggers when: abs(delta_hosts) > max_delta[0].
        #
        # if %hosts or %apps is negative, then accept an increase of any size
        # only shrinking numbers are a problem
        try:
            self.delta_hosts = 100 * (self.new_objects[0] - self.old_objects[0]) / self.old_objects[0]
        except Exception as e:
            # before we had 0 hosts. accept this initial increase
            self.delta_hosts = 0
        try:
            self.delta_services = 100 * (self.new_objects[1] - self.old_objects[1]) / self.old_objects[1]
        except Exception as e:
            # before we had 0 applications
            self.delta_services = 0
        if not self.max_delta:
            return False
        #
        #  before  after  delta
        #  0       10     0
        #  10      0      -100
        #  10      8      -20
        if self.max_delta[0] < 0 and self.delta_hosts < self.max_delta[0]:
            return True
        if self.max_delta[1] < 0 and self.delta_services < self.max_delta[1]:
            return True
        if self.max_delta[0] >= 0 and abs(self.delta_hosts) > self.max_delta[0]:
            return True
        if self.max_delta[1] >= 0 and abs(self.delta_services) > self.max_delta[1]:
            return True
        return False

    def run_git_init(self, path):
        """Initialise a git repository in the given path with a dummy commit.

        Creates a git repo, adds and commits a random dummy file, then
        removes it with a second commit.  This leaves the repo with a
        valid history (two commits) and an empty working tree, ready for
        the first real config commit.

        Args:
            path: Directory to initialise as a git repository.
        """
        # WHY: safe_output git reset behaviour -- when safe_output is enabled
        # and too_much_delta() triggers, the subclass (e.g.
        # DatarecipientCoshshDefault) runs "git reset --hard" + "git clean -f -d"
        # in the dynamic_dir to revert to the last committed state.  This is
        # only possible if the directory is already a git repo.  run_git_init
        # bootstraps that repo with two dummy commits so that "git reset --hard"
        # has a known-good state to revert to even on the very first run.  The
        # dummy file is created with a random name to avoid collisions, added,
        # committed, then removed and committed again, leaving a clean baseline.
        save_dir = os.getcwd()
        os.chdir(path)
        print("git init------------------")
        process = Popen(["git", "init", "."], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        init_file = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
        open(init_file, "w").close()
        print("git add {}------------------".format(init_file))
        process = Popen(["git", "add", init_file], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        commitmsg = "initial dummy-commit add"
        process = Popen(["git", "commit", "-a", "-m", commitmsg], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        print("git rm {}------------------".format(init_file))
        process = Popen(["git", "rm", init_file], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        commitmsg = "initial dummy-commit rm"
        process = Popen(["git", "commit", "-a", "-m", commitmsg], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        output, unused_err = process.communicate()
        retcode = process.poll()
        print(output)
        os.chdir(save_dir)

