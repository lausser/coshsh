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
import coshsh
from coshsh.datarecipient import Datarecipient
from coshsh.host import Host
from coshsh.util import compare_attr

logger = logging.getLogger('coshsh')

def __dr_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "snmp_exporteir"):
        return DrSnmpExporter


class DrSnmpExporter(coshsh.datarecipient.Datarecipient):
    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        self.objects_dir = kwargs.get("objects_dir", "/tmp")
        self.max_delta = kwargs.get("max_delta", ())
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

    def xxcleanup_target_dir(self):
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


    def output(self, filter=None, want_tool="prometheus"):
        sd_dir = os.path.join(self.dynamic_dir, 'targets')
        for app in self.objects['applications'].values():
            self.item_write_config(app, sd_dir, app.host_name, want_tool)

    def item_write_config(self, obj, sd_dir, objtype, want_tool=None):
        # ohne objecttype, hier soll keine autom. zwischenschicht "hosts" etc. rein
        for tool in obj.config_files:
            if not want_tool or want_tool == tool:
                for file in obj.config_files[tool]:
                    content = obj.config_files[tool][file]
                    with open(os.path.join(sd_dir, file), "w") as f:
                        f.write(content)


    def xxoutput(self, filter=None, objects={}):
        logger.info('write items to simplesample')
        logger.info("writing...")
        super(self.__class__, self).output(filter, "prometheus")
        self.count_after_objects()
        try:
            delta_hosts = 100 * abs(self.new_objects[0] - self.old_objects[0]) / self.old_objects[0]
            delta_services = 100 * abs(self.new_objects[1] - self.old_objects[1]) / self.old_objects[1]
        except Exception as e:
            delta_hosts = 0
            delta_services = 0

            #print e
            # if there are no objects in the dyndir yet, this results in a
            # division by zero
            pass

        logger.info("number of files before: %d hosts, %d applications" % self.old_objects)
        logger.info("number of files after:  %d hosts, %d applications" % self.new_objects)
        if self.max_delta and (delta_hosts > self.max_delta[0] or delta_services > self.max_delta[1]):
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("number of hosts changed by %.2f percent" % delta_hosts)
            print("number of applications changed by %.2f percent" % delta_services)
            print("please check your datasource before activating this config.")
            print("if you use a git repository, you can go back to the last")
            print("valid configuration with the following commands:")
            print("cd %s" % self.dynamic_dir)
            print("git reset --hard")
            print("git checkout .")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

        elif os.path.exists(self.dynamic_dir + '/.git'):
            logger.debug("dynamic_dir is a git repository")

            save_dir = os.getcwd()
            os.chdir(self.dynamic_dir)
            print("git add------------------")
            process = Popen(["git", "add", "."], stdout=PIPE, stderr=STDOUT, universal_newlines=True)
            output, unused_err = process.communicate()
            retcode = process.poll()
            print(output)
            commitmsg = time.strftime("%Y-%m-%d-%H-%M-%S") + " %d hostfiles,%d appfiles" % (self.new_objects[0], self.new_objects[1])
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

