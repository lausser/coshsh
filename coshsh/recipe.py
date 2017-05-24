#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import sys
import os
import re
import inspect
import time
import logging
import errno
from jinja2 import FileSystemLoader, Environment, TemplateSyntaxError, TemplateNotFound
import coshsh
from coshsh.jinja2_extensions import is_re_match, filter_re_sub, filter_re_escape, filter_host, filter_service, filter_custom_macros
from coshsh.item import Item
from coshsh.application import Application
from coshsh.hostgroup import HostGroup
from coshsh.monitoringdetail import MonitoringDetail
from coshsh.datasource import Datasource, DatasourceCorrupt, DatasourceNotReady, DatasourceNotAvailable, DatasourceNotCurrent
from coshsh.datarecipient import Datarecipient, DatarecipientCorrupt, DatarecipientNotReady, DatarecipientNotAvailable, DatarecipientNotCurrent
from coshsh.util import compare_attr, substenv

logger = logging.getLogger('coshsh')

class EmptyObject(object):
    pass


class RecipePidAlreadyRunning(Exception):
    # found another generator instance
    pass

class RecipePidNotWritable(Exception):
    # pid_dir is not writable
    pass

class RecipePidGarbage(Exception):
    # pid_file contains no integer
    pass


class Recipe(object):

    attributes_for_adapters = ["name", "force", "safe_output", "pid_dir", "pid_file", "templates_dir", "classes_dir", "objects_dir", "max_delta", "max_delta_action", "classes_path", "templates_path", "filter"]

    def __del__(self):
        pass
        # sys.path is invisible here, so this will fail
        #self.unset_recipe_sys_path()

    def __init__(self, **kwargs):
        os.environ['RECIPE_NAME'] = kwargs["name"]
        for key in kwargs.iterkeys():
            if isinstance(kwargs[key], basestring):
                kwargs[key] = re.sub('%.*?%', substenv, kwargs[key])
        self.name = kwargs["name"]
        self.force = kwargs.get("force")
        self.safe_output = kwargs.get("safe_output")
        self.pid_dir = kwargs.get("pid_dir")
        if not self.pid_dir:
            if 'OMD_ROOT' in os.environ:
                self.pid_dir = os.path.join(os.environ['OMD_ROOT'], 'tmp/run')
            elif "cygwin" in sys.platform or "linux" in sys.platform:
                self.pid_dir = "/tmp"
            else:
                self.pid_dir = os.environ.get("%TEMP%", "C:/TEMP")

        self.pid_file = os.path.join(self.pid_dir, "coshsh.pid." + re.sub('[/\\\.]', '_', self.name))
        logger.info("recipe %s init" % self.name)
        self.templates_dir = kwargs.get("templates_dir")
        self.classes_dir = kwargs.get("classes_dir")
        self.max_delta = kwargs.get("max_delta", ())
        self.max_delta_action = kwargs.get("max_delta_action", None)
        if isinstance(self.max_delta, str):
            if ":" in self.max_delta:
                self.max_delta = tuple(map(int, self.max_delta.split(":")))
            else:
                self.max_delta = tuple(map(int, (self.max_delta, self.max_delta)))
        self.my_jinja2_extensions = kwargs.get("my_jinja2_extensions", None)

        if 'OMD_ROOT' in os.environ:
            self.classes_path = [os.path.join(os.environ['OMD_ROOT'], 'share/coshsh/recipes/default/classes')]
        else:
            self.classes_path = [os.path.join(os.path.dirname(__file__), '../recipes/default/classes')]
        if self.classes_dir:
            self.classes_path = [p.strip() for p in self.classes_dir.split(',')] + self.classes_path
        self.set_recipe_sys_path()
        if 'OMD_ROOT' in os.environ:
            self.templates_path = [os.path.join(os.environ['OMD_ROOT'], 'share/coshsh/recipes/default/templates')]
        else:
            self.templates_path = [os.path.join(os.path.dirname(__file__), '../recipes/default/templates')]
        if self.templates_dir:
            self.templates_path = [p.strip() for p in self.templates_dir.split(',')] + self.templates_path
            logger.debug("recipe.templates_path reloaded %s" % ':'.join(self.templates_path))
        logger.info("recipe %s classes_dir %s" % (self.name, ','.join([os.path.abspath(p) for p in self.classes_path])))
        logger.info("recipe %s templates_dir %s" % (self.name, ','.join([os.path.abspath(p) for p in self.templates_path])))

        self.jinja2 = EmptyObject()
        setattr(self.jinja2, 'loader', FileSystemLoader(self.templates_path))
        setattr(self.jinja2, 'env', Environment(loader=self.jinja2.loader, extensions=['jinja2.ext.do']))
        self.jinja2.env.trim_blocks = True
        self.jinja2.env.tests['re_match'] = is_re_match
        self.jinja2.env.filters['re_sub'] = filter_re_sub
        self.jinja2.env.filters['re_escape'] = filter_re_escape
        self.jinja2.env.filters['service'] = filter_service
        self.jinja2.env.filters['host'] = filter_host
        self.jinja2.env.filters['custom_macros'] = filter_custom_macros

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
            'details': {},
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
        elif kwargs.get("objects_dir") and kwargs.get("datarecipients"):
            self.objects_dir = kwargs["objects_dir"]
            #logger.warn("recipe %s delete parameter objects_dir (use datarecipients instead)" % (self.name, ))
            self.datarecipient_names = [ds.lower() for ds in kwargs.get("datarecipients").split(",")]
        else:
            self.datarecipient_names = [ds.lower() for ds in kwargs.get("datarecipients").split(",")]
        # because this is allowed: datarecipients = >>>,SIMPLESAMPLE
        self.datarecipient_names = ['datarecipient_coshsh_default' if dr == '>>>' else dr for dr in self.datarecipient_names]
        if 'datarecipient_coshsh_default' in self.datarecipient_names:
            self.add_datarecipient(**dict([('type', 'datarecipient_coshsh_default'), ('name', 'datarecipient_coshsh_default'), ('objects_dir', self.objects_dir), ('max_delta', self.max_delta), ('max_delta_action', self.max_delta_action), ('safe_output', self.safe_output)]))

    def set_recipe_sys_path(self):
        sys.path[0:0] = self.classes_path

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
                ds.read(filter=filter, objects=self.objects, force=self.force)
                post_count = dict([(key, len(self.objects[key].keys())) for key in self.objects.keys()])
                post_detail_count = sum([(len(obj.monitoring_details) if hasattr(obj, 'monitoring_details') else 99) for objs in [self.objects[key].values() for key in self.objects.keys()] for obj in objs], 0)
                pre_count['details'] = pre_detail_count
                post_count['details'] = post_detail_count
                pre_count.update(dict.fromkeys([k for k in post_count if not k in pre_count], 0))
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

        for detail in self.objects['details'].values():
            fingerprint = detail.application_fingerprint()
            if fingerprint in self.objects['applications']:
                self.objects['applications'][fingerprint].monitoring_details.append(detail)
            elif fingerprint in self.objects['hosts']:
                self.objects['hosts'][fingerprint].monitoring_details.append(detail)
            else:
                logger.info("found a detail %s for an unknown application %s" % (detail, fingerprint))

        for host in self.objects['hosts'].values():
            host.resolve_monitoring_details()
            for key in [k for k in host.__dict__.keys() if not k.startswith("__") and isinstance(getattr(host, k), (list, tuple))]:
                getattr(host, key).sort()
            host.create_templates()
            host.create_hostgroups()
            host.create_contacts()

        orphaned_applications = []
        for app in self.objects['applications'].values():
            try:
                setattr(app, 'host', self.objects['hosts'][app.host_name])
                app.resolve_monitoring_details()
                for key in [k for k in app.__dict__.keys() if not k.startswith("__") and isinstance(getattr(app, k), (list, tuple))]:
                    # sort monitoring_type/monitoring_0 to bring some order into services,filesystems etc.
                    getattr(app, key).sort()
                app.create_templates()
                app.create_servicegroups()
                app.create_contacts()
            except KeyError:
                logger.info("application %s %s refers to non-existing host %s" % (app.name, app.type, app.host_name))
                orphaned_applications.append(app.fingerprint())
        for oa in orphaned_applications:
            del self.objects['applications'][oa]

        # load the hostgroups-objects after application procession because
        # this allows modification of self.host.hostgroups
        # in application.wemustrepeat()
        for host in self.objects['hosts'].values():
            for hostgroup in host.hostgroups:
                try:
                    self.objects['hostgroups'][hostgroup].append(host.host_name)
                except Exception:
                    self.objects['hostgroups'][hostgroup] = []
                    self.objects['hostgroups'][hostgroup].append(host.host_name)
        for (hostgroup_name, members) in self.objects['hostgroups'].items():
            logger.debug("creating hostgroup %s" % hostgroup_name)
            self.objects['hostgroups'][hostgroup_name] = HostGroup({ "hostgroup_name" : hostgroup_name, "members" : members})
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
        # you can put anything in objects (Item class with own templaterules)
        for item in sum([self.objects[itype].values() for itype in self.objects if itype not in ['hosts', 'applications', 'details', 'contactgroups', 'contacts', 'hostgroups']], []):
            # first check hasattr, because somebody may accidentially
            # add objects which are not a subclass of Item.
            # (And such a stupid mistake crashes coshsh-cook)
            if hasattr(item, 'config_files') and not item.config_files:
                # has not been populated with content in the datasource
                # (like bmw appmon timeperiods)
                item.render(template_cache, self.jinja2)
            
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
            for key in [attr for attr in self.attributes_for_adapters if hasattr(self, attr)]:
                kwargs['recipe_'+key] = getattr(self, key)
            datasource = newcls(**kwargs)
            self.datasources.append(datasource)

    def add_datarecipient(self, **kwargs):
        for key in [k for k in kwargs.iterkeys() if isinstance(kwargs[k], str)]:
            kwargs[key] = re.sub('%.*?%', substenv, kwargs[key])
        newcls = Datarecipient.get_class(kwargs)
        if newcls:
            for key in [attr for attr in self.attributes_for_adapters if hasattr(self, attr)]:
                kwargs['recipe_'+key] = getattr(self, key)
            datarecipient = newcls(**kwargs)
            self.datarecipients.append(datarecipient)

    def pid_protect(self):
        if os.path.exists(self.pid_file):
            if not os.access(self.pid_file, os.W_OK):
                raise RecipePidNotWritable
            try:
                pid = int(open(self.pid_file).read().strip())
            except ValueError:
                raise RecipePidGarbage
            try:
                os.kill(pid, 0)
            except OSError, (code, text):
                if code == errno.ESRCH:
                    # The pid doesn't exist, so remove the stale pidfile.
                    os.remove(self.pid_file)
                    logger.info('removing stale (pid %d) pidfile %s' % (pid, self.pid_file))
                else:
                    logger.info('failed to check status of process %d from pidfile %s: %s' % (pid, self.pid_file, text))
                    raise RecipePidGarbage
            else:
                logger.info('another instance seems to be running (pid %s), exiting' % pid)
                raise RecipePidAlreadyRunning
        else:
            if not os.access(self.pid_dir, os.W_OK):
                raise RecipePidNotWritable
        pid = str(os.getpid())
        try:
            file(self.pid_file, 'w').write(pid)
        except Exception:
            raise RecipePidNotWritable
        else:
            return self.pid_file

    def pid_remove(self):
        try:
            os.remove(self.pid_file)
        except Exception:
            pass

