#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import os
import re
import shutil
import logging
import time
from subprocess import Popen, PIPE, STDOUT
import coshsh
from coshsh.datarecipient import Datarecipient
from coshsh.util import compare_attr

logger = logging.getLogger('coshsh')

def __dr_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "snmp_exporter"):
        return DatarecipientPrometheusSnmpExporter


class DatarecipientPrometheusSnmpExporter(coshsh.datarecipient.Datarecipient):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__(**kwargs)
        self.name = kwargs["name"]
        self.want_tool = kwargs.get("want_tool", "prometheus")
        self.objects_dir = kwargs.get("objects_dir", kwargs.get("recipe_objects_dir", "/tmp"))
        self.max_delta = kwargs.get("max_delta", ())
        self.max_delta_action = kwargs.get("max_delta_action", None)
        self.safe_output = kwargs.get("safe_output")
        self.static_dir = os.path.join(self.objects_dir, 'static')
        self.dynamic_dir = os.path.join(self.objects_dir, 'dynamic')

    def prepare_target_dir(self):
        logger.info("recipient %s dynamic_dir %s" % (self.name, self.dynamic_dir))
        try:
            os.mkdir(self.dynamic_dir)
        except Exception:
            # will not have been removed with a .git inside
            pass
        try:
            os.mkdir(os.path.join(self.dynamic_dir, 'targets'))
        except Exception:
            pass

    def cleanup_target_dir(self):
        if os.path.isdir(self.dynamic_dir):
            try:
                if os.path.exists(self.dynamic_dir + "/.git"):
                    for subdir in [sd for sd in os.listdir(self.dynamic_dir) if sd != ".git"]:
                        logger.info("recipe %s remove dynamic_dir %s" % (self.name, self.dynamic_dir + "/" + subdir))
                        shutil.rmtree(self.dynamic_dir + "/" + subdir)
                else:
                    logger.info("recipe %s remove dynamic_dir %s" % (self.name, self.dynamic_dir))
                    shutil.rmtree(self.dynamic_dir)
            except Exception as e:
                logger.info("recipe %s has problems with dynamic_dir %s" % (self.name, self.dynamic_dir))
                logger.info(e)
                raise e
        else:
            logger.info("recipe %s dynamic_dir %s does not exist" % (self.name, self.dynamic_dir))

    def output(self, filter=None, want_tool=None):
        want_tool = self.want_tool
        sd_dir = os.path.join(self.dynamic_dir, 'targets')
        for app in self.objects['applications'].values():
            self.item_write_config(app, sd_dir, app.host_name, want_tool)
        self.count_after_objects()
        logger.info("number of files before: %d targets" % self.old_objects)
        logger.info("number of files after:  %d targets" % self.new_objects)
        if self.safe_output and self.too_much_delta() and os.path.exists(self.dynamic_dir + '/.git'):
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
            logger.error("number of hosts changed by %.2f percent" % self.delta_hosts)
            logger.error("number of applications changed by %.2f percent" % self.delta_services)
            logger.error("please check your datasource before activating this config.")
            logger.error("if you use a git repository, you can go back to the last")
            logger.error("valid configuration with the following commands:")
            logger.error("cd %s" % self.dynamic_dir)
            logger.error("git reset --hard")
            logger.error("git checkout .")
            logger.error("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            if self.max_delta_action:
                logger.error("running command %s" % self.max_delta_action)
                if os.path.exists(self.max_delta_action) and os.path.isfile(self.max_delta_action) and os.access(self.max_delta_action, os.X_OK):
                    self.max_delta_action = os.path.abspath(self.max_delta_action)
                    save_dir = os.getcwd()
                    os.chdir(self.dynamic_dir)
                    process = Popen([self.max_delta_action], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
                    output, errput = process.communicate()
                    retcode = process.poll()
                    logger.error("cmd says: %s" % output)
                    logger.error("cmd warns: %s" % errput)
                    logger.error("cmd exits with: %d" % retcode)
                    os.chdir(save_dir)
                else:
                    logger.error("command %s is not executable. now you're screwed" % self.max_delta_action)

        elif os.path.exists(self.dynamic_dir + '/.git'):
            logger.debug("dynamic_dir is a git repository")

            save_dir = os.getcwd()
            os.chdir(self.dynamic_dir)
            print("git add------------------")
            process = Popen(["git", "add", "."], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
            output, unused_err = process.communicate()
            retcode = process.poll()
            print(output)
            commitmsg = time.strftime("%Y-%m-%d-%H-%M-%S") + " %d targets" % (self.new_objects,)
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

    def analyze_output(self, output):
        add_hosts = []
        del_hosts = []
        for line in output.split("\n"):
            #create mode 100644 hosts/libmbp1.naxgroup.net/host.cfg
            match = re.match(r'\s*create mode.*hosts/(.*)/host.cfg', line)
            if match:
                add_hosts.append(match.group(1))
            #delete mode 100644 hosts/litxd01.emea.gdc/host.cfg
            match = re.match(r'\s*delete mode.*hosts/(.*)/host.cfg', line)
            if match:
                del_hosts.append(match.group(1))
        if add_hosts:
            logger.info("add hosts: %s" % ','.join(add_hosts))
        if del_hosts:
            logger.info("del hosts: %s" % ','.join(del_hosts))

    def count_objects(self):
        try:
            targets = len([name for name in os.listdir(os.path.join(self.dynamic_dir, 'targets')) if os.path.isfile(os.path.join(self.dynamic_dir, 'targets', name))])
            return targets
        except Exception:
            return 0

    def item_write_config(self, obj, sd_dir, objtype, want_tool=None):
        # ohne objecttype, hier soll keine autom. zwischenschicht "hosts" etc. rein
        for tool in obj.config_files:
            if not want_tool or want_tool == tool:
                for file in obj.config_files[tool]:
                    content = obj.config_files[tool][file]
                    with open(os.path.join(sd_dir, file), "w") as f:
                        f.write(content)

