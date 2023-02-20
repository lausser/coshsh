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
    if coshsh.util.compare_attr("type", params, "datarecipient_coshsh_default"):
        return DatarecipientCoshshDefault


class DatarecipientCoshshDefault(coshsh.datarecipient.Datarecipient):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__(**kwargs)
        self.name = kwargs["name"]
        self.objects_dir = kwargs.get("objects_dir", kwargs.get("recipe_objects_dir", "/tmp"))
        self.max_delta = kwargs.get("max_delta", kwargs.get("recipe_max_delta", ()))
        self.max_delta_action = kwargs.get("max_delta_action", kwargs.get("recipe_max_delta_action", None))
        self.safe_output = kwargs.get("safe_output", kwargs.get("recipe_safe_output", False))
        self.static_dir = os.path.join(self.objects_dir, 'static')
        if self.objects_dir.endswith("//"):
            self.dynamic_dir = self.objects_dir.rstrip("//")
        else:
            self.dynamic_dir = os.path.join(self.objects_dir, 'dynamic')

    def prepare_target_dir(self):
        logger.info("recipient %s dynamic_dir %s" % (self.name, self.dynamic_dir))
        try:
            os.mkdir(self.dynamic_dir)
        except Exception:
            # will not have been removed with a .git inside
            pass
        try:
            os.mkdir(os.path.join(self.dynamic_dir, 'hosts'))
            os.mkdir(os.path.join(self.dynamic_dir, 'hostgroups'))
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

    def output(self, filter=None):
        for hostgroup in self.objects.get('hostgroups', {}).values():
            self.item_write_config(hostgroup, self.dynamic_dir, "hostgroups", "nagios")
        for host in self.objects.get('hosts', {}).values():
            self.item_write_config(host, self.dynamic_dir, os.path.join("hosts", host.host_name), "nagios")
        for app in self.objects.get('applications', {}).values():
            self.item_write_config(app, self.dynamic_dir, os.path.join("hosts", app.host_name), "nagios")
        for cg in self.objects.get('contactgroups', {}).values():
            self.item_write_config(cg, self.dynamic_dir, "contactgroups", "nagios")
        for c in self.objects.get('contacts', {}).values():
            self.item_write_config(c, self.dynamic_dir, "contacts", "nagios")
        for sg in self.objects.get('servicegroups', {}).values():
            # Auf Kundenwunsch. Normalerweise sollte es allein schon fuer den
            # Vorschlag links und rechts eine geben und dann gleich nochmal und
            # einen Arschtritt und der Vollstaendigkeit halber noch einen
            # Tritt in den Sack. Aber was willste machen, wenn disch einer
            # zuscheisst mit seine Jeld.
            self.item_write_config(c, self.dynamic_dir, "servicegroups", want_tool)

        self.count_after_objects()
        logger.info("number of files before: %d hosts, %d applications" % self.old_objects)
        logger.info("number of files after:  %d hosts, %d applications" % self.new_objects)
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
            process = Popen(["git", "add", "--all", "."], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
            output, unused_err = process.communicate()
            retcode = process.poll()
            print(output)
            commitmsg = time.strftime("%Y-%m-%d-%H-%M-%S") + " %d hostfiles,%d appfiles" % (self.new_objects[0], self.new_objects[1])
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
            with open(".git/config") as gitcfg:
                if '[remote' in gitcfg.read():
                    process = Popen(["git", "push", "-u", "origin", "master"], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
                    poutput, unused_err = process.communicate()
                    retcode = process.poll()
                    print(poutput)
            os.chdir(save_dir)
            self.analyze_output(output)
        elif not os.path.exists(self.dynamic_dir + '/.git') and self.recipe_git_init and [p for p in os.environ["PATH"].split(os.pathsep) if os.path.isfile(os.path.join(p, "git"))]:
            logger.debug("dynamic_dir will be made a git repository")
            save_dir = os.getcwd()
            os.chdir(self.dynamic_dir)
            print("git init------------------")
            process = Popen(["git", "init", "."], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
            output, unused_err = process.communicate()
            retcode = process.poll()
            print(output)
            print("git add------------------")
            process = Popen(["git", "add", "--all", "."], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
            output, unused_err = process.communicate()
            retcode = process.poll()
            print(output)
            commitmsg = time.strftime("%Y-%m-%d-%H-%M-%S") + " %d hostfiles,%d appfiles" % (self.new_objects[0], self.new_objects[1])
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

