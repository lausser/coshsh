#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import csv
import os
import io
import re
import logging
from copy import copy
import coshsh
from coshsh.datasource import Datasource, DatasourceNotAvailable
from coshsh.host import Host
from coshsh.application import Application
from coshsh.contactgroup import ContactGroup
from coshsh.contact import Contact
from coshsh.monitoringdetail import MonitoringDetail
from coshsh.util import compare_attr, substenv

logger = logging.getLogger('coshsh')

def __ds_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "recipe_csv"):
        # csv-files have names like self.name+'_'+self.recipe_name+'_*.csv
        return CsvFileRecipe
    if coshsh.util.compare_attr("type", params, "csv"):
        return CsvFile

class CommentedFile:
    def __init__(self, f, commentstring="#"):
        self.f = f
        self.commentstring = commentstring
    def __next__(self):
        line = self.f.__next__()
        while line.startswith(self.commentstring):
            line = self.f.__next__()
        return line
    def __iter__(self):
        return self

class CommentedFileEnv(CommentedFile):
    def __next__(self):
        line = self.f.__next__()
        while line.startswith(self.commentstring):
            line = self.f.__next__()
        return re.sub('%.*?%', substenv, line)

class CsvFile(coshsh.datasource.Datasource):
    def __init__(self, **kwargs):
        super(CsvFile, self).__init__(**kwargs)
        self.name = kwargs["name"]
        self.dir = kwargs["dir"]
        self.objects = {}

    def open(self):
        logger.info('open datasource %s' % self.name)
        if not os.path.exists(self.dir):
            logger.error('csv dir %s does not exist' % self.dir)
            raise coshsh.datasource.DatasourceNotAvailable
        self.csv_hosts = os.path.join(self.dir, self.name+'_hosts.csv')
        self.csv_applications = os.path.join(self.dir, self.name+'_applications.csv')
        self.csv_applicationdetails = os.path.join(self.dir, self.name+'_applicationdetails.csv')
        self.csv_contactgroups = os.path.join(self.dir, self.name+'_contactgroups.csv')
        self.csv_contacts = os.path.join(self.dir, self.name+'_contacts.csv')
        self.file_class = CommentedFileEnv

    def read(self, filter=None, objects={}, force=False, **kwargs):
        self.objects = objects
        try:
            with io.open(self.csv_hosts) as f:
                hostreader = list(csv.DictReader(self.file_class(f)))
            logger.info('read hosts from %s' % self.csv_hosts)
        except Exception as exp:
            logger.debug(exp)
            hostreader = []
        # host_name,address,type,os,hardware,virtual,notification_period,location,department
        for row in hostreader:
            row["templates"] = ["generic-host"]
            for attr in [k for k in row.keys() if k in ['type', 'os', 'hardware', 'virtual']]:
                try:
                    row[attr] = row[attr].lower()
                except Exception:
                    pass
            h = coshsh.host.Host(row)
            self.add('hosts', h)

        try:
            with io.open(self.csv_applications) as f:
                appreader = list(csv.DictReader(self.file_class(f)))
            logger.info('read applications from %s' % self.csv_applications)
        except Exception as exp:
            logger.debug(exp)
            appreader = []
        resolvedrows = []
        # name,type,component,version,host_name,check_period
        for row in appreader:
            for attr in [k for k in row.keys() if k in ['name', 'type', 'component', 'version']]:
                try:
                    row[attr] = row[attr].lower()
                except Exception:
                    pass
            if '[' in row['host_name'] or '*' in row['host_name']:
                # hostnames can be regular expressions
                matching_hosts = [h for h in self.objects['hosts'].keys() if re.match('^('+row['host_name']+')', h)]
                for host_name in matching_hosts:
                    row['host_name'] = host_name
                    resolvedrows.append(copy(row))
            else:
                resolvedrows.append(copy(row))
        for row in resolvedrows:
            a = coshsh.application.Application(row)
            self.add('applications', a)

        try:
            with io.open(self.csv_applicationdetails) as f:
                appdetailreader = list(csv.DictReader(self.file_class(f)))
            logger.info('read appdetails from %s' % self.csv_applicationdetails)
        except Exception as exp:
            logger.debug(exp)
            appdetailreader = []
        resolvedrows = []
        # host_name,name,type,monitoring_type,monitoring_0,monitoring_1,monitoring_2,monitoring_3,monitoring_4,monitoring_5
        for row in appdetailreader:
            if '[' in row['host_name'] or '*' in row['host_name']:
                # hostnames can be regular expressions
                matching_hosts = [h for h in self.objects['hosts'].keys() if re.match('^('+row['host_name']+')', h)]
                for host_name in matching_hosts:
                    row['host_name'] = host_name
                    resolvedrows.append(copy(row))
            else:
                resolvedrows.append(copy(row))
        for row in resolvedrows:
            for attr in [k for k in row.keys() if k in ['name', 'type', 'component', 'version']]:
                row[attr] = row[attr].lower()
            application_id = "%s+%s+%s" % (row["host_name"], row["name"], row["type"])
            detail = coshsh.monitoringdetail.MonitoringDetail(row)
            self.add('details', detail)
        
        try:
            with io.open(self.csv_contactgroups) as f:
                contactgroupreader = list(csv.DictReader(self.file_class(f)))
            logger.info('read contactgroups from %s' % self.csv_contactgroups)
        except Exception as exp:
            logger.debug(exp)
            contactgroupreader = []
        resolvedrows = []
        # host_name,name,type,groups
        for row in contactgroupreader:
            if '[' in row['host_name'] or '*' in row['host_name']:
                # hostnames can be regular expressions
                matching_hosts = [h for h in self.objects['hosts'].keys() if re.match('^('+row['host_name']+')', h)]
                for host_name in matching_hosts:
                    row['host_name'] = host_name
                    resolvedrows.append(copy(row))
            else:
                resolvedrows.append(copy(row))
        for row in resolvedrows:
            application_id = "%s+%s+%s" % (row["host_name"], row["name"], row["type"])
            for group in row["groups"].split(":"):
                if not self.find('contactgroups', group):
                    self.add('contactgroups', coshsh.contactgroup.ContactGroup({ 'contactgroup_name' : group }))
                if self.find('applications', application_id) and row["name"] == "os":
                    if not group in self.get('applications', application_id).contact_groups:
                        self.get('applications', application_id).contact_groups.append(group)
                    # OS contacts also are host's contacts
                    if not group in self.get('hosts', row["host_name"]).contact_groups:
                        self.get('hosts', row["host_name"]).contact_groups.append(group)
                elif self.find('applications', application_id):
                    if not group in self.get('applications', application_id).contact_groups:
                        self.get('applications', application_id).contact_groups.append(group)
                elif ("name" not in row or not row['name']) and self.find('hosts', row['host_name']):
                    if not group in self.get('hosts', row['host_name']).contact_groups:
                        self.get('hosts', row['host_name']).contact_groups.append(group)
                else:
                    pass
                    # it's ok, no host, no app matches this hostname/name/type
                    # maybe it's a mistake, but bette be quiet than to fill
                    # up the log file with an error for _every_ application
        
        try:
            with io.open(self.csv_contacts) as f:
                contactreader = list(csv.DictReader(self.file_class(f)))
            logger.info('read contacts from %s' % self.csv_contacts)
        except Exception as exp:
            logger.debug(exp)
            contactreader = []
        # name,type,address,userid,notification_period,groups
        for row in contactreader:
            c = coshsh.contact.Contact(row)
            if not self.find('contacts', c.fingerprint()):
                c.contactgroups.extend(row["groups"].split(":"))
                self.add('contacts', c)



class CsvFileRecipe(CsvFile):

    def open(self):
        logger.info('open datasource %s' % self.name)
        if not os.path.exists(self.dir):
            logger.error('csv dir %s does not exist' % self.dir)
            raise coshsh.datasource.DatasourceNotAvailable
        self.csv_hosts = os.path.join(self.dir, self.name+'_'+self.recipe_name+'_hosts.csv')
        self.csv_applications = os.path.join(self.dir, self.name+'_'+self.recipe_name+'_applications.csv')
        self.csv_applicationdetails = os.path.join(self.dir, self.name+'_'+self.recipe_name+'_applicationdetails.csv')
        self.csv_contactgroups = os.path.join(self.dir, self.name+'_'+self.recipe_name+'_contactgroups.csv')
        self.csv_contacts = os.path.join(self.dir, self.name+'_'+self.recipe_name+'_contacts.csv')
        self.file_class = CommentedFileEnv

