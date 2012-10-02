#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import sys
import os
import re
import shutil
import inspect
import time
#sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
#sys.path.append(os.path.join(os.path.dirname(__file__), '../coshsh'))
from jinja2 import FileSystemLoader, Environment, TemplateSyntaxError, TemplateNotFound
from subprocess import Popen, PIPE, STDOUT
from jinja2_extensions import is_re_match, filter_re_sub, filter_re_escape, filter_service
from log import logger
from item import Item
from application import Application
from monitoring_detail import MonitoringDetail
from datasource import Datasource, DatasourceCorrupt, DatasourceNotReady, DatasourceNotAvailable
from util import compare_attr, substenv


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
        self.objects_dir = kwargs["objects_dir"]
        self.templates_dir = kwargs.get("templates_dir")
        self.classes_dir = kwargs.get("classes_dir")
        self.datasource_names = [ds.lower() for ds in kwargs.get("datasources").split(",")]
        self.filter = kwargs.get("filter")

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
        logger.info("recipe %s objects_dir %s" % (self.name, os.path.abspath(self.objects_dir)))
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

        

        self.datasources = []

        self.hosts = {}
        self.applications = {}
        self.appdetails = {}
        self.contacts = {}
        self.contactgroups = {}
        self.dependencies = {}
        self.bps = {}

        self.hostgroups = {}

        self.datasource_filters = {}
        if kwargs.get("filter"):
            for rule in kwargs.get("filter").split(','):
                match = re.match(r'(\w+)\((.*)\)', rule)
                if match:
                    self.datasource_filters[match.groups()[0].lower()] = match.groups()[1]
        self.static_dir = os.path.join(self.objects_dir, 'static')
        self.dynamic_dir = os.path.join(self.objects_dir, 'dynamic')
        self.init_class_cache()


    def set_recipe_sys_path(self):
        for p in [p for p in reversed(self.classes_path) if os.path.exists(p) and os.path.isdir(p)]:
            sys.path.insert(0, os.path.abspath(p))

    def unset_recipe_sys_path(self):
        for p in [p for p in self.classes_path if os.path.exists(p) and os.path.isdir(p)]:
            sys.path.pop(0)

    def prepare_target_dir(self):
        logger.info("recipe %s dynamic_dir %s" % (self.name, self.dynamic_dir))
        if not os.path.exists(self.dynamic_dir):
            # will not have been removed with a .git inside
            os.mkdir(self.dynamic_dir)
        os.mkdir(os.path.join(self.dynamic_dir, 'hosts'))
        os.mkdir(os.path.join(self.dynamic_dir, 'hostgroups'))


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


    def count_before_objects(self):
        try:
            hosts = len([name for name in os.listdir(os.path.join(self.dynamic_dir, 'hosts')) if os.path.isdir(os.path.join(self.dynamic_dir, 'hosts', name))])
            apps = len([app for host in os.listdir(os.path.join(self.dynamic_dir, 'hosts')) if os.path.isdir(os.path.join(self.dynamic_dir, 'hosts', host)) for app in os.listdir(os.path.join(self.dynamic_dir, 'hosts', host)) if app != 'host.cfg'])
            self.old_objects = (hosts, apps)
        except Exception:
            self.old_objects = (0, 0)

    def count_after_objects(self):
        if os.path.isdir(self.dynamic_dir):
            hosts = len([name for name in os.listdir(os.path.join(self.dynamic_dir, 'hosts')) if os.path.isdir(os.path.join(self.dynamic_dir, 'hosts', name))])
            apps = len([app for host in os.listdir(os.path.join(self.dynamic_dir, 'hosts')) if os.path.isdir(os.path.join(self.dynamic_dir, 'hosts', host)) for app in os.listdir(os.path.join(self.dynamic_dir, 'hosts', host)) if app != 'host.cfg'])
            self.new_objects = (hosts, apps)
        else:
            self.new_objects = (0, 0)

    def collect(self):
        data_valid = True
        for ds in self.datasources:
            filter = self.datasource_filters.get(ds.name)
            try:
                ds.open()
                hosts, applications, contacts, contactgroups, appdetails, dependencies, bps = ds.read(filter=filter, intermediate_hosts=self.hosts, intermediate_applications=self.applications)
                logger.info("recipe %s read from datasource %s %d hosts, %d applications, %d details, %d contacts, %d dependencies, %d business processes" % (self.name, ds.name, len(hosts), len(applications), len(appdetails), len(contacts), len(dependencies), len(bps)))
                ds.close()
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
            for host in hosts:
                self.hosts[host.host_name] = host
            for app in applications:
                self.applications[app.fingerprint()] = app
            for cg in contactgroups:
                self.contactgroups[cg.contactgroup_name] = cg
            for c in contacts:
                self.contacts[c.fingerprint()] = c

        for host in self.hosts.values():
            host.resolve_monitoring_details()
            host.create_templates()
            host.create_hostgroups()
            host.create_contacts()
            for hostgroup in host.hostgroups:
                try:
                    self.hostgroups[hostgroup].append(host.host_name)
                except Exception:
                    self.hostgroups[hostgroup] = []
                    self.hostgroups[hostgroup].append(host.host_name)

        orphaned_applications = []
        for app in self.applications.values():
            try:
                setattr(app, 'host', self.hosts[app.host_name])
                app.resolve_monitoring_details()
                app.create_templates()
                app.create_servicegroups()
                app.create_contacts()
            except KeyError:
                logger.info("application %s %s refers to non-existing host %s" % (app.name, app.type, app.host_name))
                orphaned_applications.append(app.fingerprint())
        for oa in orphaned_applications:
            del self.applications[oa]

        from hostgroup import Hostgroup
        for (hostgroup_name, members) in self.hostgroups.items():
            logger.debug("creating hostgroup %s" % hostgroup_name)
            self.hostgroups[hostgroup_name] = Hostgroup({ "hostgroup_name" : hostgroup_name, "members" : members})
            self.hostgroups[hostgroup_name].create_templates()
            self.hostgroups[hostgroup_name].create_contacts()

        return True
 

    def render(self):
        template_cache = {}
        for host in self.hosts.values():
            host.render(template_cache, self.jinja2)
        for app in self.applications.values():
            # because of this __new__ construct the Item.searchpath is
            # not inherited. Needs to be done explicitely
            app.render(template_cache, self.jinja2)
        for cg in self.contactgroups.values():
            cg.render(template_cache, self.jinja2)
        for c in self.contacts.values():
            c.render(template_cache, self.jinja2)
        for hg in self.hostgroups.values():
            hg.render(template_cache, self.jinja2)
        #if self.classes_dir:
        #    Item.reload_template_path()
            


    def output(self):
        delta_hosts, delta_services = 0, 0
        for hostgroup in self.hostgroups.values():
            hostgroup.write_config(self.dynamic_dir)
        for host in self.hosts.values():
            host.write_config(self.dynamic_dir)
        for app in self.applications.values():
            app.write_config(self.dynamic_dir)
        for cg in self.contactgroups.values():
            cg.write_config(self.dynamic_dir)
        for c in self.contacts.values():
            c.write_config(self.dynamic_dir)
        self.count_after_objects()
        try:
            delta_hosts = 100 * abs(self.new_objects[0] - self.old_objects[0]) / self.old_objects[0]
            delta_services = 100 * abs(self.new_objects[1] - self.old_objects[1]) / self.old_objects[1]
        except Exception, e:
            #print e
            # if there are no objects in the dyndir yet, this results in a
            # division by zero
            pass

        logger.info("number of files before: %d hosts, %d applications" % self.old_objects)
        logger.info("number of files after:  %d hosts, %d applications" % self.new_objects)
        if delta_hosts > 10 or delta_services > 10:
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

    def read(self):
        return self.hosts.values(), self.applications.values(), self.appdetails, self.contacts, self.dependencies, self.bps


    def init_class_cache(self):
        Datasource.init_classes(self.classes_path)
        logger.debug("init Datasource classes (%d)" % len(Datasource.class_factory))
        Application.init_classes(self.classes_path)
        logger.debug("init Application classes (%d)" % len(Application.class_factory))
        MonitoringDetail.init_classes(self.classes_path)
        logger.debug("init MonitoringDetail classes (%d)" % len(MonitoringDetail.class_factory))

    def add_datasource(self, **kwargs):
        #print "add a datasource", kwargs
        newcls = Datasource.get_class(kwargs)
        if newcls:
            datasource = newcls(**kwargs)
            self.datasources.append(datasource)


