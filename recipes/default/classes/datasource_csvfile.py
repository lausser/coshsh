#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from datasource import Datasource, DatasourceNotAvailable
import csv
import os
import re
import logging
from copy import copy
from host import Host
from application import Application
from contactgroup import ContactGroup
from contact import Contact
from monitoring_detail import MonitoringDetail
from util import compare_attr

logger = logging.getLogger('coshsh')

def __ds_ident__(params={}):
    if compare_attr("type", params, "csv"):
        return CsvFile

class CommentedFile:
    def __init__(self, f, commentstring="#"):
        self.f = f
        self.commentstring = commentstring
    def next(self):
        line = self.f.next()
        while line.startswith(self.commentstring):
            line = self.f.next()
        return line
    def __iter__(self):
        return self

class CsvFile(Datasource):
    def __init__(self, **kwargs):
        superclass = super(self.__class__, self)
        superclass.__init__(**kwargs)
        self.name = kwargs["name"]
        self.dir = kwargs["dir"]
        self.objects = {}

    def open(self):
        logger.info('open datasource %s' % self.name)
        if not os.path.exists(self.dir):
            logger.error('csv dir %s does not exist' % self.dir)
            raise DatasourceNotAvailable

    def read(self, filter=None, objects={}):
        self.objects = objects
        try:
            hostreader = csv.DictReader(CommentedFile(open(os.path.join(self.dir, self.name+'_hosts.csv'))))
            logger.info('read hosts from %s' % os.path.join(self.dir, self.name+'_hosts.csv'))
        except Exception, exp:
            print "except", exp
            hostreader = []
        # host_name,address,type,os,hardware,virtual,notification_period,location,department
        for row in hostreader:
            row["templates"] = ["generic-host"]
            for attr in [k for k in row.keys() if k in ['type', 'os', 'hardware', 'virtual']]:
                row[attr] = row[attr].lower()
            h = Host(row)
            self.objects['hosts'][h.host_name] = h

        try:
            appreader = csv.DictReader(CommentedFile(open(os.path.join(self.dir, self.name+'_applications.csv'))))
            logger.info('read applications from %s' % os.path.join(self.dir, self.name+'_applications.csv'))
        except Exception:
            appreader = []
        resolvedrows = []
        # name,type,component,version,host_name,check_period
        for row in appreader:
            for attr in [k for k in row.keys() if k in ['name', 'type', 'component', 'version']]:
                row[attr] = row[attr].lower()
            if '[' in row['host_name'] or '*' in row['host_name']:
                # hostnames can be regular expressions
                matching_hosts = [h for h in self.objects['hosts'].keys() if re.match('^('+row['host_name']+')', h)]
                for host_name in matching_hosts:
                    row['host_name'] = host_name
                    resolvedrows.append(copy(row))
            else:
                resolvedrows.append(copy(row))
        for row in resolvedrows:
            if not "virtual" in row:
                try:
                    row["virtual"] = self.objects['hosts'][row["host_name"]].virtual
                except KeyError:
                    logger.error('host %s not found for application %s' % (row["host_name"], row["name"]))
            a = Application(row)
            self.objects['applications']["%s+%s+%s" % (a.host_name, a.name, a.type)] = a

        try:
            appdetailreader = csv.DictReader(CommentedFile(open(os.path.join(self.dir, self.name+'_applicationdetails.csv'))))
            logger.info('read appdetails from %s' % os.path.join(self.dir, self.name+'_applicationdetails.csv'))
        except Exception:
            appdetailreader = []
        resolvedrows = []
        # host_name,application_name,application_type,monitoring_type,monitoring_0,monitoring_1,monitoring_2,monitoring_3,monitoring_4,monitoring_5
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
            for attr in [k for k in row.keys() if k in ['application_name', 'application_type', 'component', 'version']]:
                row[attr] = row[attr].lower()
            application_id = "%s+%s+%s" % (row["host_name"], row["application_name"], row["application_type"])
            detail = MonitoringDetail(row)
            if application_id in self.objects['applications']:
                self.objects['applications'][application_id].monitoring_details.append(detail)
            elif row["host_name"] in self.objects['hosts']:
                self.objects['hosts'][row["host_name"]].monitoring_details.append(detail)
            else:
                logger.info("found a detail %s for an unknown application %s" % (detail, application_id))
                raise
        
        try:
            contactgroupreader = csv.DictReader(CommentedFile(open(os.path.join(self.dir, self.name+'_contactgroups.csv'))))
            logger.info('read contactgroups from %s' % os.path.join(self.dir, self.name+'_contactgroups.csv'))
        except Exception:
            contactgroupreader = []
        resolvedrows = []
        # host_name,application_name,application_type,groups
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
            application_id = "%s+%s+%s" % (row["host_name"], row["application_name"], row["application_type"])
            for group in row["groups"].split(":"):
                if group not in self.contactgroups:
                    self.add('contactgroups', ContactGroup({ 'contactgroup_name' : group }))
                if self.find('applications', application_id) and row["application_name"] == "os":
                    if not group in self.get('applications', application_id).contact_groups:
                        self.get('applications', application_id).contact_groups.append(group)
                    # OS contacts also are host's contacts
                    if not group in self.get('hosts', row["host_name"]).contact_groups:
                        self.get('hosts', row["host_name"]).contact_groups.append(group)
                elif self.find('applications', application_id):
                    if not group in self.get('applications', application_id).contact_groups:
                        self.get('applications', application_id).contact_groups.append(group)
                elif ("application_name" not in row or not row['application_name']) and self.find('hosts', row['host_name']):
                    if not group in self.get('hosts', row['host_name']).contact_groups:
                        self.get('hosts', row['host_name']).contact_groups.append(group)
                else:
                    logger.error('no such application %s for contactgroup %s' % (application_id, row['groups']))

        
        try:
            contactreader = csv.DictReader(CommentedFile(open(os.path.join(self.dir, self.name+'_contacts.csv'))))
            logger.info('read contacts from %s' % os.path.join(self.dir, self.name+'_contacts.csv'))
        except Exception:
            contactreader = []
        # name,type,address,userid,notification_period,groups
        for row in contactreader:
            c = Contact(row)
            if not self.find('contacts', c.fingerprint()):
                c.contactgroups.extend(row["groups"].split(":"))
                self.add('contacts', c)


