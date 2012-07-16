#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

print "--->site"
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
print sys.path
from datasource import Datasource
from util import compare_attr
print "<---site"

class EmptyObject(object):
    pass

class Site(object):

    def __del__(self):
        print "i del my site"
        self.unset_site_sys_path()

    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        logger.info("site %s init" % self.name)
        self.objects_dir = kwargs["objects_dir"]
        self.templates_dir = kwargs.get("templates_dir")
        self.classes_dir = kwargs.get("classes_dir")
        self.filter = kwargs.get("filter")

        self.classes_path = [os.path.join(os.path.dirname(__file__), '../sites/default/classes')]
        if self.classes_dir:
            self.classes_path.insert(0, self.classes_dir)
        self.set_site_sys_path()

        self.templates_path = [os.path.join(os.path.dirname(__file__), '../sites/default/templates')]
        if self.templates_dir:
            self.templates_path.insert(0, self.templates_dir)
            logger.debug("site.templates_path reloaded %s" % ':'.join(self.templates_path))
        logger.info("site %s objects_dir %s" % (self.name, os.path.abspath(self.objects_dir)))
        logger.info("site %s classes_dir %s" % (self.name, os.path.abspath(self.classes_path[0])))
        logger.info("site %s templates_dir %s" % (self.name, os.path.abspath(self.templates_path[0])))

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


    def set_site_sys_path(self):
        for p in [p for p in reversed(self.classes_path) if os.path.exists(p) and os.path.isdir(p)]:
            sys.path.insert(0, os.path.abspath(p))

    def unset_site_sys_path(self):
        for p in [p for p in self.classes_path if os.path.exists(p) and os.path.isdir(p)]:
            del sys.path[-1]

    def prepare_target_dir(self):
        logger.info("site %s dynamic_dir %s" % (self.name, self.dynamic_dir))
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
                        logger.info("site %s remove dynamic_dir %s" % (self.name, self.dynamic_dir + "/" + subdir))
                        shutil.rmtree(self.dynamic_dir + "/" + subdir)
                else:
                    logger.info("site %s remove dynamic_dir %s" % (self.name, self.dynamic_dir))
                    shutil.rmtree(self.dynamic_dir)
            except Exception as e:
                logger.info("site %s has problems with dynamic_dir %s" % (self.name, self.dynamic_dir))
                logger.info(e)
                raise e
        else:
            logger.info("site %s dynamic_dir %s does not exist" % (self.name, self.dynamic_dir))


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
        for ds in self.datasources:
            filter = self.datasource_filters.get(ds.name)
            hosts, applications, contacts, contactgroups, appdetails, dependencies, bps = ds.read(filter=filter, intermediate_hosts=self.hosts, intermediate_applications=self.applications)
            logger.info("site %s read from datasource %s %d hosts, %d applications, %d details, %d contacts, %d dependencies, %d business processes" % (self.name, ds.name, len(hosts), len(applications), len(appdetails), len(contacts), len(dependencies), len(bps)))
            
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
 

    def render(self):
        template_cache = {}
        for host in self.hosts.values():
            host.render(template_cache, self.jinja2)
        for app in self.applications.values():
            # because of this __new__ construct the Item.searchpath is
            # not inherited. Needs to be done explicitely
            print "aha! ", app
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
        print self.old_objects
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
        logger.debug("init Datasource classes")
        print "dbg", Datasource, Datasource.__name__, len(Datasource.class_factory)
        Datasource.init_classes(self.classes_path)
        print "dbb", Datasource, Datasource.__name__, len(Datasource.class_factory)
        logger.debug("init Application classes")
        print "dbg", Application, Application.__name__, len(Application.class_factory)
        Application.init_classes(self.classes_path)
        print "dbb", Application, Application.__name__, len(Application.class_factory)
        logger.debug("init MonitoringDetail classes")
        print "dbg", MonitoringDetail, MonitoringDetail.__name__, len(MonitoringDetail.class_factory)
        MonitoringDetail.init_classes(self.classes_path)
        print "dbb", MonitoringDetail, MonitoringDetail.__name__, len(MonitoringDetail.class_factory)
        print "class cache done"

    def add_datasource(self, **kwargs):
        newcls = Datasource.get_class(kwargs)
        if newcls:
            self.datasources.append(newcls(**kwargs))


