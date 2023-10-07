#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import sys
import os
import io
import re
import logging
import coshsh

logger = logging.getLogger('coshsh')


class DatarecipientNotImplemented(Exception):
    pass


class DatarecipientNotReady(Exception):
    # datarecipient is currently being updated
    pass


class DatarecipientNotCurrent(Exception):
    # datarecipients was not updated lately.
    # it makes no sense to continue.
    pass


class DatarecipientNotAvailable(Exception):
    pass


class DatarecipientCorrupt(Exception):
    pass


class Datarecipient(coshsh.datainterface.CoshshDatainterface):

    my_type = 'datarecipient'
    class_file_prefixes = ["datarecipient"]
    class_file_ident_function = "__dr_ident__"
    class_factory = []

    def __init__(self, **params):
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
        logger.info('load items to %s' % (self.name, ))
        self.objects = objects

    def get(self, objtype, fingerprint):
        try:
            return self.objects[objtype][fingerprint]
        except Exception:
            # should be None
            return 'i do not exist. no. no!'

    def getall(self, objtype):
        try:
            return self.objects[objtype].values()
        except Exception:
            return []

    def find(self, objtype, fingerprint):
        return objtype in self.objects and fingerprint in self.objects[objtype]

    def item_write_config(self, obj, dynamic_dir, objtype, want_tool=None):
        my_target_dir = os.path.join(dynamic_dir, objtype)
        if not os.path.exists(my_target_dir):
            os.makedirs(my_target_dir)
        for tool in obj.config_files:
            if not want_tool or want_tool == tool:
                for file in obj.config_files[tool]:
                    content = obj.config_files[tool][file]
                    with io.open(os.path.join(my_target_dir, file), "w") as f:
                        f.write(content)

    def output(self, filter=None, want_tool=None):
        pass
        # for obj in self-objects["objtype"].values():
        #     self.item_write_config(obj, self.dynamic_dir, "objfolder", want_tool)

    def count_objects(self):
        try:
            hosts = len([name for name in os.listdir(os.path.join(self.dynamic_dir, 'hosts')) if os.path.isdir(os.path.join(self.dynamic_dir, 'hosts', name))])
            apps = len([app for host in os.listdir(os.path.join(self.dynamic_dir, 'hosts')) if os.path.isdir(os.path.join(self.dynamic_dir, 'hosts', host)) for app in os.listdir(os.path.join(self.dynamic_dir, 'hosts', host)) if app != 'host.cfg' and os.path.getsize(os.path.join(self.dynamic_dir, 'hosts', host, app)) != 0])
            return (hosts, apps)
        except Exception:
            return (0, 0)

    def count_before_objects(self):
        self.old_objects = self.count_objects()

    def count_after_objects(self):
        self.new_objects = self.count_objects()

    def prepare_target_dir(self):
        pass

    def cleanup_target_dir(self):
        pass

    def too_much_delta(self):
        # self.old_objects = (hosts_before, apps_before)
        # self.new_objects = (hosts_after, apps_after)
        # self.max_delta = (%hosts, %apps)
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
            print("neg and shrink")
            return True
        if self.max_delta[1] < 0 and self.delta_services < self.max_delta[1]:
            return True
        if self.max_delta[0] >= 0 and abs(self.delta_hosts) > self.max_delta[0]:
            return True
        if self.max_delta[1] >= 0 and abs(self.delta_services) > self.max_delta[1]:
            return True
        return False
