#!/usr/bin/env python
#-*- encoding: utf-8 -*-
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

def __ds_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "datarecipient_coshsh_default"):
        return DatarecipientCoshshDefault


class DatarecipientCoshshDefault(coshsh.datarecipient.Datarecipient):
    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        self.objects_dir = kwargs.get("objects_dir", "/tmp")
        self.max_delta = kwargs.get("max_delta", ())
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
        super(self.__class__, self).output(filter)
        self.count_after_objects()
        try:
            delta_hosts = 100 * abs(self.new_objects[0] - self.old_objects[0]) / self.old_objects[0]
            delta_services = 100 * abs(self.new_objects[1] - self.old_objects[1]) / self.old_objects[1]
        except Exception, e:
            delta_hosts = 0
            delta_services = 0

        logger.info("number of files before: %d hosts, %d applications" % self.old_objects)
        logger.info("number of files after:  %d hosts, %d applications" % self.new_objects)
        if self.safe_output and self.max_delta and (delta_hosts > self.max_delta[0] or delta_services > self.max_delta[1]) and os.path.exists(self.dynamic_dir + '/.git'):
            save_dir = os.getcwd()
            os.chdir(self.dynamic_dir)
            print "git reset hard------------------"
            process = Popen(["git", "reset", "--hard"], stdout=PIPE, stderr=STDOUT)
            output, unused_err = process.communicate()
            retcode = process.poll()
            print output
            os.chdir(save_dir)
            self.analyze_output(output)
            logger.error("the last commit was revoked")

        elif self.max_delta and (delta_hosts > self.max_delta[0] or delta_services > self.max_delta[1]):
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            print "number of hosts changed by %.2f percent" % delta_hosts
            print "number of applications changed by %.2f percent" % delta_services
            print "please check your datasource before activating this config."
            print "if you use a git repository, you can go back to the last"
            print "valid configuration with the following commands:"
            print "cd %s" % self.dynamic_dir
            print "git reset --hard"
            print "git checkout ."
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"

        elif os.path.exists(self.dynamic_dir + '/.git'):
            logger.debug("dynamic_dir is a git repository")

            save_dir = os.getcwd()
            os.chdir(self.dynamic_dir)
            print "git add------------------"
            process = Popen(["git", "add", "."], stdout=PIPE, stderr=STDOUT)
            output, unused_err = process.communicate()
            retcode = process.poll()
            print output
            commitmsg = time.strftime("%Y-%m-%d-%H-%M-%S") + " %d hostfiles,%d appfiles" % (self.new_objects[0], self.new_objects[1])
            print "git commit------------------"
            print "commit-comment", commitmsg
            process = Popen(["git", "commit", "-a", "-m", commitmsg], stdout=PIPE, stderr=STDOUT)
            output, unused_err = process.communicate()
            retcode = process.poll()
            print output
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

