#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import sys
import os
import re
import inspect
import time
import logging
from jinja2 import FileSystemLoader, Environment, TemplateSyntaxError, TemplateNotFound
from jinja2_extensions import is_re_match, filter_re_sub, filter_re_escape, filter_service
from item import Item
from application import Application
from hostgroup import Hostgroup
from monitoring_detail import MonitoringDetail
from datasource import Datasource, DatasourceCorrupt, DatasourceNotReady, DatasourceNotAvailable, DatasourceNotCurrent
from datarecipient import Datarecipient, DatarecipientCorrupt, DatarecipientNotReady, DatarecipientNotAvailable, DatarecipientNotCurrent
from util import compare_attr, substenv

logger = logging.getLogger('coshsh')

class EmptyObject(object):
    pass


class Recipe(object):

    def __del__(self):
        pass
        # sys.path is invisible here, so this will fail
        #self.unset_recipe_sys_path()

    def __init__(self, **kwargs):
        for key in kwargs.iterkeys():
            kwargs[key] = re.sub('%.*?%', substenv, kwargs[key])
        self.name = kwargs["name"]
        logger.info("recipe %s init" % self.name)
        self.templates_dir = kwargs.get("templates_dir")
        self.classes_dir = kwargs.get("classes_dir")
        self.max_delta = kwargs.get("max_delta", ())
        if isinstance(self.max_delta, str):
            if ":" in self.max_delta:
                self.max_delta = tuple(map(int, self.max_delta.split(":")))
            else:
                self.max_delta = tuple(map(int, (self.max_delta, self.max_delta)))
        self.my_jinja2_extensions = kwargs.get("my_jinja2_extensions", None)

        self.classes_path = [os.path.join(os.path.dirname(__file__), '../recipes/default/classes')]
        if self.classes_dir:
            for path in reversed([p.strip() for p in self.classes_dir.split(',')]):
                self.classes_path.insert(0, path)
        self.set_recipe_sys_path()
        self.templates_path = [os.path.join(os.path.dirname(__file__), '../recipes/default/templates')]
        if self.templates_dir:
            for path in reversed([p.strip() for p in self.templates_dir.split(',')]):
                self.templates_path.insert(0, path)
            logger.debug("recipe.templates_path reloaded %s" % ':'.join(self.templates_path))
        logger.info("recipe %s classes_dir %s" % (self.name, ','.join([os.path.abspath(p) for p in self.classes_path])))
        logger.info("recipe %s templates_dir %s" % (self.name, ','.join([os.path.abspath(p) for p in self.templates_path])))

        self.jinja2 = EmptyObject()
        setattr(self.jinja2, 'loader', FileSystemLoader(self.templates_path))
        setattr(self.jinja2, 'env', Environment(loader=self.jinja2.loader))
        self.jinja2.env.trim_blocks = True
        self.jinja2.env.tests['re_match'] = is_re_match
        self.jinja2.env.filters['re_sub'] = filter_re_sub
        self.jinja2.env.filters['re_escape'] = filter_re_escape
        self.jinja2.env.filters['service'] = filter_service

        if self.my_jinja2_extensions:
            for extension in [e.strip() for e in self.my_jinja2_extensions.split(",")]:
                imported = getattr(__import__("my_jinja2_extensions", fromlist=[extension]), extension)
                if extension.startswith("is_"):
                    self.jinja2.env.tests[extension.replace("is_", "")] = imported
                elif extension.startswith("filter_"):
                    self.jinja2.env.filters[extension.replace("filter_", "")] = imported
            
        self.datasources = []
        self.datarecipients = []

        self.objects = {
            'hosts': {},
            'hostgroups': {},
            'applications': {},
            'appdetails': {},
            'contacts': {},
            'contactgroups': {},
            'commands': {},
            'timeperiods': {},
            'dependencies': {},
            'bps': {},
        }
        
        self.old_objects = (0, 0)
        self.new_objects = (0, 0)

        self.datasource_filters = {}
        self.filter = kwargs.get("filter")
        if kwargs.get("filter"):
            for rule in kwargs.get("filter").split(','):
                match = re.match(r'(\w+)\((.*)\)', rule)
                if match:
                    self.datasource_filters[match.groups()[0].lower()] = match.groups()[1]
        self.init_class_cache()

        if kwargs.get("datasources"):
            self.datasource_names = [ds.lower() for ds in kwargs.get("datasources").split(",")]
        else:
            self.datasource_names = []
        if kwargs.get("objects_dir") and not kwargs.get("datarecipients"):
            self.objects_dir = kwargs["objects_dir"]
            logger.info("recipe %s objects_dir %s" % (self.name, os.path.abspath(self.objects_dir)))
            self.datarecipient_names = ["datarecipient_coshsh_default"]
            self.add_datarecipient(**dict([('type', 'datarecipient_coshsh_default'), ('name', 'datarecipient_coshsh_default'), ('objects_dir', self.objects_dir), ('max_delta', self.max_delta)]))
        elif kwargs.get("objects_dir") and kwargs.get("datarecipients"):
            logger.warn("recipe %s delete parameter objects_dir (use datarecipients instead)" % (self.name, ))
            self.datarecipient_names = [ds.lower() for ds in kwargs.get("datarecipients").split(",")]
        else:
            self.datarecipient_names = [ds.lower() for ds in kwargs.get("datarecipients").split(",")]

    def set_recipe_sys_path(self):
        for p in [p for p in reversed(self.classes_path) if os.path.exists(p) and os.path.isdir(p)]:
            sys.path.insert(0, os.path.abspath(p))

    def unset_recipe_sys_path(self):
        for p in [p for p in self.classes_path if os.path.exists(p) and os.path.isdir(p)]:
            sys.path.pop(0)

    def collect(self):
        data_valid = True
        for ds in self.datasources:
            filter = self.datasource_filters.get(ds.name)
            try:
                ds.open()
                pre_count = dict([(key, len(self.objects[key].keys())) for key in self.objects.keys()])
                pre_detail_count = sum([(len(obj.monitoring_details) if hasattr(obj, 'monitoring_details') else 99) for objs in [self.objects[key].values() for key in self.objects.keys()] for obj in objs], 0)
                ds.read(filter=filter, objects=self.objects)
                post_count = dict([(key, len(self.objects[key].keys())) for key in self.objects.keys()])
                post_detail_count = sum([(len(obj.monitoring_details) if hasattr(obj, 'monitoring_details') else 99) for objs in [self.objects[key].values() for key in self.objects.keys()] for obj in objs], 0)
                pre_count['details'] = pre_detail_count
                post_count['details'] = post_detail_count
                # todo: count monitoring_details
                chg_keys = [(key, post_count[key] - pre_count[key]) for key in set(pre_count.keys() + post_count.keys()) if post_count[key] != pre_count[key]]
                logger.info("recipe %s read from datasource %s %s" % (self.name, ds.name, ", ".join(["%d %s" % (k[1], k[0]) for k in chg_keys])))

                ds.close()
            except DatasourceNotCurrent:
                data_valid = False
                logger.info("datasource %s is is not current" % ds.name)
            except DatasourceNotReady:
                data_valid = False
                logger.info("datasource %s is busy" % ds.name)
            except DatasourceNotAvailable:
                data_valid = False
                logger.info("datasource %s is not available" % ds.name)
            except Exception, exp:
                data_valid = False
                logger.critical("datasource %s returns bad data (%s)" % (ds.name, exp))
            if not data_valid:
                logger.info("aborting collection phase") 
                return False

        for host in self.objects['hosts'].values():
            host.resolve_monitoring_details()
            host.create_templates()
            host.create_hostgroups()
            host.create_contacts()
            for hostgroup in host.hostgroups:
                try:
                    self.objects['hostgroups'][hostgroup].append(host.host_name)
                except Exception:
                    self.objects['hostgroups'][hostgroup] = []
                    self.objects['hostgroups'][hostgroup].append(host.host_name)

        orphaned_applications = []
        for app in self.objects['applications'].values():
            try:
                setattr(app, 'host', self.objects['hosts'][app.host_name])
                app.resolve_monitoring_details()
                app.create_templates()
                app.create_servicegroups()
                app.create_contacts()
            except KeyError:
                logger.info("application %s %s refers to non-existing host %s" % (app.name, app.type, app.host_name))
                orphaned_applications.append(app.fingerprint())
        for oa in orphaned_applications:
            del self.objects['applications'][oa]

        for (hostgroup_name, members) in self.objects['hostgroups'].items():
            logger.debug("creating hostgroup %s" % hostgroup_name)
            self.objects['hostgroups'][hostgroup_name] = Hostgroup({ "hostgroup_name" : hostgroup_name, "members" : members})
            self.objects['hostgroups'][hostgroup_name].create_templates()
            self.objects['hostgroups'][hostgroup_name].create_contacts()

        return True
 
    def render(self):
        template_cache = {}
        for host in self.objects['hosts'].values():
            host.render(template_cache, self.jinja2)
        for app in self.objects['applications'].values():
            # because of this __new__ construct the Item.searchpath is
            # not inherited. Needs to be done explicitely
            app.render(template_cache, self.jinja2)
        for cg in self.objects['contactgroups'].values():
            cg.render(template_cache, self.jinja2)
        for c in self.objects['contacts'].values():
            c.render(template_cache, self.jinja2)
        for hg in self.objects['hostgroups'].values():
            hg.render(template_cache, self.jinja2)
            
    def count_before_objects(self):
        for datarecipient in self.datarecipients:
            datarecipient.count_before_objects()
        self.old_objects = (sum([dr.old_objects[0] for dr in self.datarecipients], 0), sum([dr.old_objects[1] for dr in self.datarecipients], 0))

    def count_after_objects(self):
        for datarecipient in self.datarecipients:
            datarecipient.count_after_objects()
        self.new_objects = (sum(0, [dr.new_objects[0] for dr in self.datarecipients]), sum(0, [dr.new_objects[1] for dr in self.datarecipients]))

    def cleanup_target_dir(self):
        for datarecipient in self.datarecipients:
            datarecipient.cleanup_target_dir()

    def prepare_target_dir(self):
        for datarecipient in self.datarecipients:
            datarecipient.prepare_target_dir()

    def output(self):
        for datarecipient in self.datarecipients:
            datarecipient.count_before_objects()
            datarecipient.load(None, self.objects)
            datarecipient.cleanup_target_dir()
            datarecipient.prepare_target_dir()
            datarecipient.output()

    def read(self):
        return self.objects


    def init_class_cache(self):
        Datasource.init_classes(self.classes_path)
        logger.debug("init Datasource classes (%d)" % len(Datasource.class_factory))
        Datarecipient.init_classes(self.classes_path)
        logger.debug("init Datarecipient classes (%d)" % len(Datarecipient.class_factory))
        Application.init_classes(self.classes_path)
        logger.debug("init Application classes (%d)" % len(Application.class_factory))
        MonitoringDetail.init_classes(self.classes_path)
        logger.debug("init MonitoringDetail classes (%d)" % len(MonitoringDetail.class_factory))

    def add_datasource(self, **kwargs):
        for key in [k for k in kwargs.iterkeys() if isinstance(kwargs[k], str)]:
            kwargs[key] = re.sub('%.*?%', substenv, kwargs[key])
        newcls = Datasource.get_class(kwargs)
        if newcls:
            datasource = newcls(**kwargs)
            self.datasources.append(datasource)

    def add_datarecipient(self, **kwargs):
        for key in [k for k in kwargs.iterkeys() if isinstance(kwargs[k], str)]:
            kwargs[key] = re.sub('%.*?%', substenv, kwargs[key])
        newcls = Datarecipient.get_class(kwargs)
        if newcls:
            datarecipient = newcls(**kwargs)
            self.datarecipients.append(datarecipient)


