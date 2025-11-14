#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Prometheus SNMP Exporter datarecipient for coshsh.

This module provides a datarecipient implementation for Prometheus SNMP Exporter,
which generates service discovery target files for monitoring SNMP-enabled devices
with Prometheus. It handles dynamic configuration generation, git repository
management, and delta checking to prevent accidental large-scale configuration changes.

The datarecipient outputs target files in JSON format that Prometheus can consume
for service discovery of SNMP exporter targets.
"""

from __future__ import annotations

import os
import re
import shutil
import logging
import time
from subprocess import Popen, PIPE, STDOUT
from typing import Dict, Any, Optional, TYPE_CHECKING
import coshsh
from coshsh.datarecipient import Datarecipient
from coshsh.util import compare_attr

if TYPE_CHECKING:
    from coshsh.item import Item

logger = logging.getLogger('coshsh')


def __dr_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type[DatarecipientPrometheusSnmpExporter]]:
    """Identify if this datarecipient handles the given parameters.

    Args:
        params: Configuration parameters dictionary containing 'type' key

    Returns:
        DatarecipientPrometheusSnmpExporter class if type is 'snmp_exporter',
        None otherwise
    """
    if params is None:
        params = {}
    if coshsh.util.compare_attr("type", params, "^snmp_exporter$"):
        return DatarecipientPrometheusSnmpExporter
    return None


class DatarecipientPrometheusSnmpExporter(coshsh.datarecipient.Datarecipient):
    """Datarecipient for Prometheus SNMP Exporter target generation.

    This datarecipient generates service discovery target files for Prometheus
    SNMP Exporter. It writes configuration files to a dynamic directory and
    optionally manages them with git. It includes safety features to prevent
    accidental large-scale configuration changes through delta checking.

    Attributes:
        name: Name of this datarecipient instance
        want_tool: Tool identifier, defaults to 'prometheus'
        objects_dir: Base directory for output files
        max_delta: Tuple of (hosts_percent, services_percent) thresholds
        max_delta_action: Optional command to run on excessive delta
        safe_output: Enable automatic git reset on excessive delta
        static_dir: Directory for static configuration files
        dynamic_dir: Directory for dynamically generated configuration files
        old_objects: Object count before generation
        new_objects: Object count after generation
        delta_hosts: Percentage change in host count
        delta_services: Percentage change in service count
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Prometheus SNMP Exporter datarecipient.

        Args:
            **kwargs: Configuration parameters including:
                name: Required name for this datarecipient
                want_tool: Tool identifier (default: 'prometheus')
                objects_dir: Output directory (default: recipe_objects_dir or '/tmp')
                max_delta: Tuple of thresholds (default: empty tuple)
                max_delta_action: Optional command path for delta action
                safe_output: Enable automatic rollback on excessive delta
        """
        super().__init__(**kwargs)
        self.name: str = kwargs["name"]
        self.want_tool: str = kwargs.get("want_tool", "prometheus")
        self.objects_dir: str = kwargs.get("objects_dir", kwargs.get("recipe_objects_dir", "/tmp"))
        self.max_delta: tuple = kwargs.get("max_delta", ())
        self.max_delta_action: Optional[str] = kwargs.get("max_delta_action", None)
        self.safe_output: bool = kwargs.get("safe_output", False)
        self.static_dir: str = os.path.join(self.objects_dir, 'static')
        self.dynamic_dir: str = os.path.join(self.objects_dir, 'dynamic')
        self.old_objects: int = 0
        self.new_objects: int = 0
        self.delta_hosts: float = 0.0
        self.delta_services: float = 0.0

    def prepare_target_dir(self) -> None:
        """Prepare the target directory structure.

        Creates the dynamic directory and targets subdirectory if they don't exist.
        If a .git directory exists inside, the directory won't have been removed
        during cleanup, so this is safe to call repeatedly.
        """
        logger.info(f"recipient {self.name} dynamic_dir {self.dynamic_dir}")
        try:
            os.mkdir(self.dynamic_dir)
        except Exception:
            # will not have been removed with a .git inside
            pass
        try:
            os.mkdir(os.path.join(self.dynamic_dir, 'targets'))
        except Exception:
            pass

    def cleanup_target_dir(self) -> None:
        """Clean up the target directory.

        If a .git directory exists within dynamic_dir, only removes subdirectories
        (preserving the git repository). Otherwise removes the entire dynamic_dir.

        Raises:
            Exception: If cleanup fails (e.g., permission errors)
        """
        if os.path.isdir(self.dynamic_dir):
            try:
                if os.path.exists(f"{self.dynamic_dir}/.git"):
                    for subdir in [sd for sd in os.listdir(self.dynamic_dir) if sd != ".git"]:
                        logger.info(f"recipe {self.name} remove dynamic_dir {self.dynamic_dir}/{subdir}")
                        shutil.rmtree(f"{self.dynamic_dir}/{subdir}")
                else:
                    logger.info(f"recipe {self.name} remove dynamic_dir {self.dynamic_dir}")
                    shutil.rmtree(self.dynamic_dir)
            except Exception as e:
                logger.info(f"recipe {self.name} has problems with dynamic_dir {self.dynamic_dir}")
                logger.info(e)
                raise e
        else:
            logger.info(f"recipe {self.name} dynamic_dir {self.dynamic_dir} does not exist")

    def output(self, filter: Optional[Any] = None, want_tool: Optional[str] = None) -> None:
        """Generate and output configuration files.

        Writes target files for all applications, counts objects before/after,
        and handles git operations and delta checking. If delta exceeds thresholds,
        either reverts changes automatically (if safe_output enabled) or logs
        warnings with manual recovery instructions.

        Args:
            filter: Optional filter for output (unused in this implementation)
            want_tool: Optional tool filter, defaults to self.want_tool

        Process:
            1. Write configuration files for all applications
            2. Count objects and calculate delta
            3. If safe_output enabled and delta too large: auto-revert via git
            4. If delta too large: log warnings and optionally run max_delta_action
            5. If git repo exists and delta OK: commit changes
        """
        want_tool = self.want_tool
        sd_dir = os.path.join(self.dynamic_dir, 'targets')
        for app in self.objects['applications'].values():
            self.item_write_config(app, sd_dir, app.host_name, want_tool)
        self.count_after_objects()
        logger.info(f"number of files before: {self.old_objects} targets")
        logger.info(f"number of files after:  {self.new_objects} targets")
        if self.safe_output and self.too_much_delta() and os.path.exists(f"{self.dynamic_dir}/.git"):
            save_dir = os.getcwd()
            os.chdir(self.dynamic_dir)
            logger.error("git reset --hard")
            process = Popen(["git", "reset", "--hard"], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
            output, unused_err = process.communicate()
            retcode = process.poll()
            logger.info(output)
            logger.error("git clean untracked files")
            process = Popen(["git", "clean", "-f", "-d"], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
            output, unused_err = process.communicate()
            retcode = process.poll()
            logger.info(output)
            os.chdir(save_dir)
            self.analyze_output(output)
            logger.error("the last commit was revoked")

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
            if self.max_delta_action:
                logger.error(f"running command {self.max_delta_action}")
                if os.path.exists(self.max_delta_action) and os.path.isfile(self.max_delta_action) and os.access(self.max_delta_action, os.X_OK):
                    self.max_delta_action = os.path.abspath(self.max_delta_action)
                    save_dir = os.getcwd()
                    os.chdir(self.dynamic_dir)
                    process = Popen([self.max_delta_action], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
                    output, errput = process.communicate()
                    retcode = process.poll()
                    logger.error(f"cmd says: {output}")
                    logger.error(f"cmd warns: {errput}")
                    logger.error(f"cmd exits with: {retcode}")
                    os.chdir(save_dir)
                else:
                    logger.error(f"command {self.max_delta_action} is not executable. now you're screwed")

        elif os.path.exists(f"{self.dynamic_dir}/.git"):
            logger.debug("dynamic_dir is a git repository")

            save_dir = os.getcwd()
            os.chdir(self.dynamic_dir)
            print("git add------------------")
            process = Popen(["git", "add", "."], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
            output, unused_err = process.communicate()
            retcode = process.poll()
            print(output)
            commitmsg = f"{time.strftime('%Y-%m-%d-%H-%M-%S')} {self.new_objects} targets"
            if False:
                process = Popen(["git", "diff"], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
                output, unused_err = process.communicate()
                retcode = process.poll()
                logger.debug("the changes are...")
                logger.debug(output)
            print("git commit------------------")
            print("commit-comment", commitmsg)
            process = Popen(["git", "commit", "-a", "-m", commitmsg], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
            output, unused_err = process.communicate()
            retcode = process.poll()
            print(output)
            os.chdir(save_dir)
            self.analyze_output(output)

    def analyze_output(self, output: str) -> None:
        """Analyze git output to identify added and deleted hosts.

        Parses git commit/reset output to extract which host configuration files
        were created or deleted, then logs a summary.

        Args:
            output: Git command output text to analyze

        Example output patterns:
            create mode 100644 hosts/libmbp1.naxgroup.net/host.cfg
            delete mode 100644 hosts/litxd01.emea.gdc/host.cfg
        """
        add_hosts: list[str] = []
        del_hosts: list[str] = []
        for line in output.split("\n"):
            # create mode 100644 hosts/libmbp1.naxgroup.net/host.cfg
            match = re.match(r'\s*create mode.*hosts/(.*)/host.cfg', line)
            if match:
                add_hosts.append(match.group(1))
            # delete mode 100644 hosts/litxd01.emea.gdc/host.cfg
            match = re.match(r'\s*delete mode.*hosts/(.*)/host.cfg', line)
            if match:
                del_hosts.append(match.group(1))
        if add_hosts:
            logger.info(f"add hosts: {','.join(add_hosts)}")
        if del_hosts:
            logger.info(f"del hosts: {','.join(del_hosts)}")

    def count_objects(self) -> int:
        """Count the number of target files in the targets directory.

        Returns:
            Number of target files, or 0 if directory doesn't exist or on error
        """
        try:
            targets = len([name for name in os.listdir(os.path.join(self.dynamic_dir, 'targets')) if os.path.isfile(os.path.join(self.dynamic_dir, 'targets', name))])
            return targets
        except Exception:
            return 0

    def item_write_config(self, obj: Item, sd_dir: str, objtype: str, want_tool: Optional[str] = None) -> None:
        """Write configuration files for a single item.

        Unlike the base class implementation, this writes directly to sd_dir
        without creating an intermediate subdirectory based on objtype. This is
        specific to the Prometheus SNMP Exporter format.

        Args:
            obj: The item object containing config_files attribute
            sd_dir: Target directory for configuration files
            objtype: Object type (not used for subdirectory in this implementation)
            want_tool: Optional tool filter - only write configs for this tool
        """
        # ohne objecttype, hier soll keine autom. zwischenschicht "hosts" etc. rein
        for tool in obj.config_files:
            if not want_tool or want_tool == tool:
                for file in obj.config_files[tool]:
                    content = obj.config_files[tool][file]
                    with open(os.path.join(sd_dir, file), "w") as f:
                        f.write(content)

