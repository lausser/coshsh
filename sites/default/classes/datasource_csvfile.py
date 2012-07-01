#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from datasource import Datasource
import csv
import os
import re
from copy import copy
from host import Host
from application import Application
from contactgroup import ContactGroup
from contact import Contact
from monitoring_detail import MonitoringDetail
from shintarator.log import logger
from util import compare_attr

def __ds_ident__(params={}):
    print "-----------------ident csv----------------", params
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
        self.dir = kwargs["dir"]
        self.hosts = {}
        self.applications = {}
        self.appdetails = {}
        self.contacts = {}
        self.contactgroups = {}
        self.dependencies = {}
        self.bps = {}


    def read(self, filter=None, intermediate_hosts=[], intermediate_applications=[]):

        logger.info('read hosts from %s' % os.path.join(self.dir, self.name+'_hosts.csv'))
        try:
            hostreader = csv.DictReader(CommentedFile(open(os.path.join(self.dir, self.name+'_hosts.csv'))))
        except Exception:
            hostreader = []
        # host_name,address,type,os,hardware,virtual,notification_period,location,department
        for row in hostreader:
            row["templates"] = ["generic-host"]
            h = Host(row)
            self.hosts[h.host_name] = h

        intermediate_hosts = dict(intermediate_hosts.items() + self.hosts.items())

        logger.info('read applications from %s' % os.path.join(self.dir, self.name+'_applications.csv'))
        try:
            appreader = csv.DictReader(CommentedFile(open(os.path.join(self.dir, self.name+'_applications.csv'))))
        except Exception:
            appreader = []
        resolvedrows = []
        # name,type,component,version,host_name,check_period
        for row in appreader:
            if '[' in row['host_name'] or '*' in row['host_name']:
                # hostnames can be regular expressions
                matching_hosts = [h for h in intermediate_hosts.keys() if re.match('^('+row['host_name']+')', h)]
                for host_name in matching_hosts:
                    row['host_name'] = host_name
                    resolvedrows.append(copy(row))
            else:
                resolvedrows.append(copy(row))
        for row in resolvedrows:
            if not "virtual" in row:
                try:
                    row["virtual"] = intermediate_hosts[row["host_name"]].virtual
                except KeyError:
                    logger.error('host %s not found for application %s' % (row["host_name"], row["name"]))
            a = Application(row)
            self.applications["%s+%s+%s" % (a.host_name, a.name, a.type)] = a

        intermediate_applications = dict(intermediate_applications.items() + self.applications.items())

        logger.info('read appdetails from %s' % os.path.join(self.dir, self.name+'_applicationdetails.csv'))
        try:
            appdetailreader = csv.DictReader(CommentedFile(open(os.path.join(self.dir, self.name+'_applicationdetails.csv'))))
        except Exception:
            appdetailreader = []
        resolvedrows = []
        # host_name,application_name,application_type,monitoring_type,monitoring_0,monitoring_1,monitoring_2,monitoring_3,monitoring_4,monitoring_5
        for row in appdetailreader:
            if '[' in row['host_name'] or '*' in row['host_name']:
                # hostnames can be regular expressions
                matching_hosts = [h for h in intermediate_hosts.keys() if re.match('^('+row['host_name']+')', h)]
                for host_name in matching_hosts:
                    row['host_name'] = host_name
                    resolvedrows.append(copy(row))
            else:
                resolvedrows.append(copy(row))
        for row in resolvedrows:
            application_id = "%s+%s+%s" % (row["host_name"], row["application_name"], row["application_type"])
            detail = MonitoringDetail(row)
            if application_id in intermediate_applications:
                intermediate_applications[application_id].monitoring_details.append(detail)
            elif row["host_name"] in intermediate_hosts:
                intermediate_hosts[row["host_name"]].monitoring_details.append(detail)
                print "der host, der scheeene host"
            else:
                print "no such application", row["host_name"], row["application_name"], row["application_type"]
                print self.hosts.keys()
                raise
        
        logger.info('read contactgroups from %s' % os.path.join(self.dir, self.name+'_contactgroups.csv'))
        try:
            contactgroupreader = csv.DictReader(CommentedFile(open(os.path.join(self.dir, self.name+'_contactgroups.csv'))))
        except Exception:
            contactgroupreader = []
        resolvedrows = []
        # host_name,application_name,application_type,groups
        for row in contactgroupreader:
            if '[' in row['host_name'] or '*' in row['host_name']:
                # hostnames can be regular expressions
                matching_hosts = [h for h in intermediate_hosts.keys() if re.match('^('+row['host_name']+')', h)]
                for host_name in matching_hosts:
                    row['host_name'] = host_name
                    resolvedrows.append(copy(row))
            else:
                resolvedrows.append(copy(row))
        for row in resolvedrows:
            application_id = "%s+%s+%s" % (row["host_name"], row["application_name"], row["application_type"])
            for group in row["groups"].split(":"):
                if group not in self.contactgroups:
                    self.contactgroups[group] = ContactGroup({ 'contactgroup_name' : group })
                if application_id in self.applications and row["application_name"] == "os":
                    if not group in self.applications[application_id].contact_groups:
                        self.applications[application_id].contact_groups.append(group)
                    # OS contacts also are host's contacts
                    if not group in self.hosts[row["host_name"]].contact_groups:
                        self.hosts[row["host_name"]].contact_groups.append(group)
                elif application_id in self.applications:
                    if not group in self.applications[application_id].contact_groups:
                        self.applications[application_id].contact_groups.append(group)
                elif ("application_name" not in row or not row['application_name']) and row['host_name'] in intermediate_hosts:
                    if not group in intermediate_hosts[row['host_name']].contact_groups:
                        intermediate_hosts[row['host_name']].contact_groups.append(group)
                else:
                    logger.error('no such application %s for contactgroup %s' % (application_id, row['groups']))

        
        logger.info('read contacts from %s' % os.path.join(self.dir, self.name+'_contacts.csv'))
        try:
            contactreader = csv.DictReader(CommentedFile(open(os.path.join(self.dir, self.name+'_contacts.csv'))))
        except Exception:
            contactreader = []
        # name,type,address,userid,notification_period,groups
        for row in contactreader:
            c = Contact(row)
            if c.fingerprint() not in self.contacts:
                c.contactgroups.extend(row["groups"].split(":"))
                self.contacts[c.fingerprint()] = c

        return self.hosts.values(), self.applications.values(), self.contacts.values(), self.contactgroups.values(), self.appdetails, self.dependencies, self.bps

