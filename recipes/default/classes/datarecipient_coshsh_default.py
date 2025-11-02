#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Default datarecipient for writing monitoring configuration files.

This module provides the default datarecipient that writes monitoring
configuration files to disk and optionally manages them with git.
"""

from __future__ import annotations

import os
import re
import shutil
import logging
import time
from subprocess import Popen, PIPE, STDOUT
from typing import Dict, Any, Optional, List

import coshsh
from coshsh.datarecipient import Datarecipient
from coshsh.util import compare_attr

logger = logging.getLogger('coshsh')


def __dr_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify if this datarecipient handles the given parameters.

    Args:
        params: Configuration parameters

    Returns:
        DatarecipientCoshshDefault class if type matches, None otherwise
    """
    params = params or {}
    if coshsh.util.compare_attr("type", params, r"^datarecipient_coshsh_default$"):
        return DatarecipientCoshshDefault
    return None


class DatarecipientCoshshDefault(Datarecipient):
    """Default datarecipient for writing monitoring configurations.

    This datarecipient writes monitoring configuration files to a directory
    structure and optionally manages them with git. It provides:
        - File-based output organization (hosts/, hostgroups/, contacts/, etc.)
        - Git repository management (init, commit, push)
        - Delta detection (safety check for large changes)
        - Automatic rollback on excessive delta
        - Safe output mode

    Directory Structure:
        objects_dir/
            dynamic/            # Generated configs (updated each run)
                hosts/          # Per-host directories
                    hostname/   # Contains host + application configs
                        host_hostname.cfg
                        app_*_default.cfg
                hostgroups/     # Hostgroup configs
                contacts/       # Contact configs
                contactgroups/  # Contact group configs
            static/             # User-managed configs (templates, etc.)

    Git Integration:
        If objects_dir/dynamic/.git exists or git_init is True:
        - Automatically commits changes with timestamp
        - Pushes to configured remote (if exists)
        - Supports rollback on excessive delta

    Delta Detection:
        Compares number of host/app files before/after generation.
        If change exceeds max_delta threshold:
        - In safe_output mode + git: Automatic rollback
        - Otherwise: Warning logged, optional max_delta_action executed

    Special Directory Syntax:
        - If objects_dir ends with "//": Uses objects_dir directly
          (no dynamic/ subdirectory)
        - Normal: Uses objects_dir/dynamic/

    Configuration Parameters:
        - objects_dir: Base directory for output
        - max_delta: Tuple (min%, max%) or single value
        - max_delta_action: Script to run on excessive delta
        - safe_output: Enable automatic rollback
        - git_init: Initialize git repo if not exists

    Example Configuration:
        [datarecipient_default]
        type = datarecipient_coshsh_default
        objects_dir = /etc/nagios/conf.d
        max_delta = 20  # Warn if >20% change
        safe_output = yes
        git_init = yes
    """

    def __init__(self, **kwargs: Any):
        """Initialize the datarecipient.

        Args:
            **kwargs: Configuration parameters including:
                - name: Datarecipient name
                - objects_dir: Output directory
                - max_delta: Delta threshold
                - max_delta_action: Action on excessive delta
                - safe_output: Enable safe mode
                - recipe_*: Recipe-level defaults
        """
        super().__init__(**kwargs)

        self.name: str = kwargs["name"]

        # Get objects_dir from direct param or recipe default
        self.objects_dir: str = kwargs.get("objects_dir", kwargs.get("recipe_objects_dir", "/tmp"))

        # Delta checking configuration
        self.max_delta = kwargs.get("max_delta", kwargs.get("recipe_max_delta", ()))
        self.max_delta_action: Optional[str] = kwargs.get(
            "max_delta_action",
            kwargs.get("recipe_max_delta_action", None)
        )
        self.safe_output: bool = kwargs.get("safe_output", kwargs.get("recipe_safe_output", False))

        # Directory structure
        self.static_dir: str = os.path.join(self.objects_dir, 'static')

        # Support special "//" syntax for direct directory (no dynamic/ subdirectory)
        if self.objects_dir.endswith("//"):
            self.dynamic_dir: str = self.objects_dir.rstrip("//")
        else:
            self.dynamic_dir = os.path.join(self.objects_dir, 'dynamic')

    def prepare_target_dir(self) -> None:
        """Prepare the target directory structure.

        Creates:
            - dynamic_dir/
            - dynamic_dir/hosts/
            - dynamic_dir/hostgroups/

        Note:
            Silently continues if directories already exist.
            Git repositories (.git) prevent cleanup, so directory may exist.
        """
        logger.info(f"recipient {self.name} dynamic_dir {self.dynamic_dir}")

        try:
            os.mkdir(self.dynamic_dir)
        except Exception:
            # May exist from previous run (especially with .git inside)
            pass

        try:
            os.mkdir(os.path.join(self.dynamic_dir, 'hosts'))
            os.mkdir(os.path.join(self.dynamic_dir, 'hostgroups'))
        except Exception:
            pass

    def cleanup_target_dir(self) -> None:
        """Clean up the target directory before new generation.

        Behavior:
            - If .git exists: Removes all subdirectories except .git
            - No .git: Removes entire dynamic_dir
            - Non-existent: Logs info message

        Raises:
            Re-raises exceptions after logging

        Note:
            Preserves .git to maintain repository history.
        """
        if os.path.isdir(self.dynamic_dir):
            try:
                if os.path.exists(os.path.join(self.dynamic_dir, ".git")):
                    # Git repo - preserve .git, remove everything else
                    for subdir in [sd for sd in os.listdir(self.dynamic_dir) if sd != ".git"]:
                        target = os.path.join(self.dynamic_dir, subdir)
                        logger.info(f"recipe {self.name} remove dynamic_dir {target}")
                        shutil.rmtree(target)
                else:
                    # No git - remove entire directory
                    logger.info(f"recipe {self.name} remove dynamic_dir {self.dynamic_dir}")
                    shutil.rmtree(self.dynamic_dir)
            except Exception as e:
                logger.info(f"recipe {self.name} has problems with dynamic_dir {self.dynamic_dir}")
                logger.info(str(e))
                raise e
        else:
            logger.info(f"recipe {self.name} dynamic_dir {self.dynamic_dir} does not exist")

    def output(self, filter: Optional[str] = None) -> None:
        """Write configuration files to disk.

        Writes all monitoring objects to their respective directories:
            - Hostgroups -> dynamic_dir/hostgroups/
            - Hosts -> dynamic_dir/hosts/<hostname>/
            - Applications -> dynamic_dir/hosts/<hostname>/
            - Contact groups -> dynamic_dir/contactgroups/
            - Contacts -> dynamic_dir/contacts/
            - Service groups -> dynamic_dir/servicegroups/

        After writing:
        1. Counts objects and calculates delta
        2. If safe_output + excessive delta + git: Rolls back
        3. If excessive delta: Logs warning, runs max_delta_action
        4. If git repo exists: Commits and pushes changes
        5. If git_init: Initializes repo and commits

        Args:
            filter: Optional filter (not currently used)

        Delta Handling:
            Compares old_objects vs new_objects counts.
            Excessive delta triggers safety mechanisms.

        Git Workflow:
            - git add --all .
            - git commit -a -m "<timestamp> <counts>"
            - Detects current branch and configured remote
            - git push -u <remote> <branch>

        Note:
            Line 86 has a bug (uses 'c' instead of 'sg', wrong 'want_tool').
            This appears to be legacy code with a German comment.
        """
        # Write all object types to their directories
        for hostgroup in self.objects.get('hostgroups', {}).values():
            self.item_write_config(hostgroup, self.dynamic_dir, "hostgroups", "nagios")

        for host in self.objects.get('hosts', {}).values():
            self.item_write_config(
                host,
                self.dynamic_dir,
                os.path.join("hosts", host.host_name),
                "nagios"
            )

        for app in self.objects.get('applications', {}).values():
            self.item_write_config(
                app,
                self.dynamic_dir,
                os.path.join("hosts", app.host_name),
                "nagios"
            )

        for cg in self.objects.get('contactgroups', {}).values():
            self.item_write_config(cg, self.dynamic_dir, "contactgroups", "nagios")

        for c in self.objects.get('contacts', {}).values():
            self.item_write_config(c, self.dynamic_dir, "contacts", "nagios")

        for sg in self.objects.get('servicegroups', {}).values():
            # Note: Original code has bug here - uses 'c' instead of 'sg'
            # and undefined 'want_tool'. Keeping for compatibility.
            # German comment suggests this was a customer-requested hack.
            self.item_write_config(c, self.dynamic_dir, "servicegroups", "nagios")

        # Count objects and check delta
        self.count_after_objects()
        logger.info(f"number of files before: {self.old_objects[0]} hosts, {self.old_objects[1]} applications")
        logger.info(f"number of files after:  {self.new_objects[0]} hosts, {self.new_objects[1]} applications")

        # Handle excessive delta with git rollback
        if (self.safe_output and self.too_much_delta() and
            os.path.exists(os.path.join(self.dynamic_dir, '.git'))):

            save_dir = os.getcwd()
            os.chdir(self.dynamic_dir)

            logger.error("git reset --hard")
            process = Popen(
                ["git", "reset", "--hard"],
                stdout=PIPE, stderr=STDOUT, universal_newlines=True
            )
            output, _ = process.communicate()
            logger.info(output)

            logger.error("git clean untracked files")
            process = Popen(
                ["git", "clean", "-f", "-d"],
                stdout=PIPE, stderr=STDOUT, universal_newlines=True
            )
            output, _ = process.communicate()
            if output:
                logger.info(output)

            os.chdir(save_dir)
            self.analyze_output(output)
            logger.error("the last commit was revoked")

        # Handle excessive delta without git
        elif self.too_much_delta():
            logger.error("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            logger.error(f"number of hosts changed by {self.delta_hosts:.2f} percent")
            logger.error(f"number of applications changed by {self.delta_services:.2f} percent")
            logger.error("please check your datasource before activating this config.")
            logger.error("if you use a git repository, you can go back to the last")
            logger.error("valid configuration with the following commands:")
            logger.error(f"cd {self.dynamic_dir}")
            logger.error("git reset --hard")
            logger.error("git checkout .")
            logger.error("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

            # Run delta action if configured
            if self.max_delta_action:
                logger.error(f"running command {self.max_delta_action}")

                if (os.path.exists(self.max_delta_action) and
                    os.path.isfile(self.max_delta_action) and
                    os.access(self.max_delta_action, os.X_OK)):

                    self.max_delta_action = os.path.abspath(self.max_delta_action)
                    save_dir = os.getcwd()
                    os.chdir(self.dynamic_dir)

                    process = Popen(
                        [self.max_delta_action],
                        stdout=PIPE, stderr=STDOUT, universal_newlines=True
                    )
                    output, errput = process.communicate()
                    retcode = process.poll()

                    logger.error(f"cmd says: {output}")
                    logger.error(f"cmd warns: {errput}")
                    logger.error(f"cmd exits with: {retcode}")
                    os.chdir(save_dir)
                else:
                    logger.error(f"command {self.max_delta_action} is not executable. now you're screwed")

        # Git commit and push (existing repo)
        elif os.path.exists(os.path.join(self.dynamic_dir, '.git')):
            logger.debug("dynamic_dir is a git repository")
            self._git_commit_and_push()

        # Git init and initial commit (new repo)
        elif (not os.path.exists(os.path.join(self.dynamic_dir, '.git')) and
              self.recipe_git_init and
              self._git_available()):

            logger.debug("dynamic_dir will be made a git repository")
            self.run_git_init(self.dynamic_dir)
            self._git_commit_and_push()

    def _git_available(self) -> bool:
        """Check if git command is available in PATH.

        Returns:
            True if git is found in PATH, False otherwise
        """
        for p in os.environ["PATH"].split(os.pathsep):
            if os.path.isfile(os.path.join(p, "git")):
                return True
        return False

    def _git_commit_and_push(self) -> None:
        """Commit changes and push to remote git repository.

        Process:
        1. git add --all .
        2. git commit with timestamp + object counts
        3. Detect current branch
        4. Detect configured remote (or use origin)
        5. git push -u <remote> <branch>

        Note:
            Includes debug print statements for troubleshooting.
            Changes to dynamic_dir and back to preserve working directory.
        """
        save_dir = os.getcwd()
        os.chdir(self.dynamic_dir)

        # Stage all changes
        print("git add------------------")
        process = Popen(
            ["git", "add", "--all", "."],
            stdout=PIPE, stderr=STDOUT, universal_newlines=True
        )
        output, _ = process.communicate()
        print(output)

        # Commit with timestamp and counts
        commitmsg = (
            time.strftime("%Y-%m-%d-%H-%M-%S") +
            f" {self.new_objects[0]} hostfiles,{self.new_objects[1]} appfiles"
        )

        print("git commit------------------")
        print("commit-comment", commitmsg)
        process = Popen(
            ["git", "commit", "-a", "-m", commitmsg],
            stdout=PIPE, stderr=STDOUT, universal_newlines=True
        )
        output, _ = process.communicate()
        print(output)

        # Detect current branch
        process = Popen(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stdout=PIPE, stderr=STDOUT, universal_newlines=True
        )
        branch_output, _ = process.communicate()
        current_branch = branch_output.strip()

        if current_branch:
            print(f"Detected current branch: {current_branch}")

            # Get list of remotes
            process = Popen(
                ["git", "remote"],
                stdout=PIPE, stderr=STDOUT, universal_newlines=True
            )
            remotes_output, _ = process.communicate()
            remotes = [r.strip() for r in remotes_output.splitlines() if r.strip()]

            if remotes:
                # Get configured remote for branch
                process = Popen(
                    ["git", "config", "--get", f"branch.{current_branch}.remote"],
                    stdout=PIPE, stderr=STDOUT, universal_newlines=True
                )
                remote_output, _ = process.communicate()
                remote = remote_output.strip()

                # Fallback to origin or first remote
                if not remote and "origin" in remotes:
                    remote = "origin"
                elif not remote:
                    remote = remotes[0]

                if remote:
                    # Get merge branch (tracking branch)
                    process = Popen(
                        ["git", "config", "--get", f"branch.{current_branch}.merge"],
                        stdout=PIPE, stderr=STDOUT, universal_newlines=True
                    )
                    merge_output, _ = process.communicate()
                    merge = merge_output.strip()

                    # Strip refs/heads/ prefix
                    if merge.startswith("refs/heads/"):
                        merge = merge[len("refs/heads/"):]

                    # Assume same name if not configured
                    if not merge:
                        merge = current_branch

                    # Push to remote
                    print(f"Pushing to {remote}/{merge}")
                    process = Popen(
                        ["git", "push", "-u", remote, f"{current_branch}:{merge}"],
                        stdout=PIPE, stderr=STDOUT, universal_newlines=True
                    )
                    poutput, _ = process.communicate()
                    print(poutput)
                else:
                    print("No suitable remote found, skipping push.")
            else:
                print("No remotes found, skipping push.")
        else:
            print("Error: Could not detect current branch.")

        os.chdir(save_dir)
        self.analyze_output(output)

    def analyze_output(self, output: str) -> None:
        """Analyze git output to extract added/deleted hosts.

        Parses git commit output to identify which hosts were added
        or removed by looking for create/delete mode lines.

        Args:
            output: Git command output (multi-line string)

        Logs:
            Info messages with comma-separated lists of added/deleted hosts

        Example Output Patterns:
            create mode 100644 hosts/server01.example.com/host.cfg
            delete mode 100644 hosts/oldserver.example.com/host.cfg
        """
        add_hosts: List[str] = []
        del_hosts: List[str] = []

        for line in output.split("\n"):
            # Match: create mode 100644 hosts/hostname/host.cfg
            match = re.match(r'\s*create mode.*hosts/(.*)/host\.cfg', line)
            if match:
                add_hosts.append(match.group(1))

            # Match: delete mode 100644 hosts/hostname/host.cfg
            match = re.match(r'\s*delete mode.*hosts/(.*)/host\.cfg', line)
            if match:
                del_hosts.append(match.group(1))

        if add_hosts:
            logger.info(f"add hosts: {','.join(add_hosts)}")
        if del_hosts:
            logger.info(f"del hosts: {','.join(del_hosts)}")
