#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""CSV File Datasource Plugin

This plugin reads monitoring configuration data from CSV files.

CSV File Structure:
-------------------
The datasource expects up to 5 CSV files with specific naming conventions:

1. {name}_hosts.csv
   - Columns: host_name, address, type, os, hardware, virtual,
              notification_period, location, department, hostgroups
   - Creates Host objects
   - hostgroups column: semicolon-separated list

2. {name}_applications.csv
   - Columns: name, type, component, version, host_name, check_period
   - Creates Application objects
   - host_name supports regex patterns (e.g., "web[0-9]+")

3. {name}_applicationdetails.csv
   - Columns: host_name, name, type, monitoring_type,
              monitoring_0..monitoring_5
   - Creates MonitoringDetail objects
   - Supports hostname regex patterns

4. {name}_contactgroups.csv
   - Columns: host_name, name, type, groups
   - Assigns contactgroups to hosts/applications
   - groups: colon-separated list

5. {name}_contacts.csv
   - Columns: name, type, address, userid, notification_period, groups
   - Creates Contact objects
   - groups: colon-separated list

Regex Hostname Matching:
------------------------
Hostnames containing '[' or '*' are treated as regular expressions:

Example:
    host_name: "web[0-9]+"
    Matches: web01, web02, web99, etc.

The pattern is automatically expanded to match existing hosts,
creating one application/detail per matching host.

Filter Column:
--------------
CSV files can include a 'coshsh_filter' column (configurable via
filter_column parameter). When a filter is specified in read(),
only rows with matching filter values are processed.

Example:
    host_name,address,coshsh_filter
    web01,10.0.0.1,production
    web02,10.0.0.2,staging

    datasource.read(filter='production')  # Only reads web01

Environment Variable Expansion:
-------------------------------
CommentedFileEnv automatically expands %VAR% syntax to environment
variable values:

Example:
    host_name,address
    web01,%WEB_IP%

    If WEB_IP=10.0.0.1, becomes: web01,10.0.0.1

Classes:
--------
- CommentedFile: Iterator that skips lines starting with #
- CommentedFileEnv: Adds environment variable expansion
- CsvFile: Main datasource for files named {name}_{type}.csv
- CsvFileRecipe: Recipe-specific files named {name}_{recipe}_{type}.csv

Usage Examples:
---------------
Basic CSV datasource:
    [datasource_csv1]
    type = csv
    name = monitoring
    dir = /path/to/csv/files

Creates files: monitoring_hosts.csv, monitoring_applications.csv, etc.

Recipe-specific datasource:
    [datasource_csv2]
    type = recipe_csv
    name = monitoring
    dir = /path/to/csv/files

For recipe "prod", creates: monitoring_prod_hosts.csv, etc.

Filter column customization:
    [datasource_csv3]
    type = csv
    name = monitoring
    dir = /path/to/csv/files
    filter_column = environment

Uses 'environment' column instead of 'coshsh_filter'.
"""

from __future__ import annotations

import csv
import os
import io
import re
import logging
from copy import copy
from typing import Optional, Dict, Any, Iterator, TextIO

import coshsh
from coshsh.datasource import Datasource, DatasourceNotAvailable
from coshsh.host import Host
from coshsh.application import Application
from coshsh.contactgroup import ContactGroup
from coshsh.contact import Contact
from coshsh.monitoringdetail import MonitoringDetail
from coshsh.util import compare_attr, substenv

logger = logging.getLogger('coshsh')


def __ds_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify the appropriate datasource class based on type parameter.

    This function is called by the plugin factory system to determine
    which class to instantiate based on configuration parameters.

    Args:
        params: Configuration dictionary containing 'type' key

    Returns:
        CsvFileRecipe if type='recipe_csv'
        CsvFile if type='csv'
        None if no match

    Example:
        # In cookbook.cfg:
        [datasource_mydata]
        type = csv
        name = monitoring
        dir = /path/to/csv

        # Factory calls: __ds_ident__({'type': 'csv', ...})
        # Returns: CsvFile class
    """
    if params is None:
        params = {}

    if coshsh.util.compare_attr("type", params, "^recipe_csv$"):
        # csv-files have names like self.name+'_'+self.recipe_name+'_*.csv
        # recommendation is to use CsvFile and add a coshsh_filter column
        return CsvFileRecipe
    if coshsh.util.compare_attr("type", params, "^csv$"):
        return CsvFile
    return None


class CommentedFile:
    """Iterator that skips comment lines in a file.

    Wraps a file object and filters out lines starting with a
    comment string (default: #).

    This allows CSV files to contain comments for documentation:
        # This is a comment
        host_name,address
        web01,10.0.0.1
        # Another comment
        web02,10.0.0.2

    Attributes:
        f: Wrapped file object
        commentstring: Lines starting with this are skipped (default: #)
    """

    def __init__(self, f: TextIO, commentstring: str = "#") -> None:
        """Initialize the commented file iterator.

        Args:
            f: File object to wrap
            commentstring: Comment prefix to skip (default: #)
        """
        self.f = f
        self.commentstring = commentstring

    def __next__(self) -> str:
        """Return next non-comment line.

        Returns:
            Next line that doesn't start with commentstring

        Raises:
            StopIteration: When end of file is reached
        """
        line = self.f.__next__()
        while line.startswith(self.commentstring):
            line = self.f.__next__()
        return line

    def __iter__(self) -> Iterator[str]:
        """Return iterator interface.

        Returns:
            Self as iterator
        """
        return self


class CommentedFileEnv(CommentedFile):
    """CommentedFile with environment variable expansion.

    Extends CommentedFile to replace %VAR% patterns with environment
    variable values using the substenv utility function.

    Example:
        CSV file content:
            host_name,address,notification_period
            web01,%WEB_IP%,%NOTIFY_PERIOD%

        If environment has:
            WEB_IP=10.0.0.1
            NOTIFY_PERIOD=24x7

        Read as:
            host_name,address,notification_period
            web01,10.0.0.1,24x7

    Note:
        substenv is defined in coshsh.util and handles the %VAR% pattern.
    """

    def __next__(self) -> str:
        """Return next non-comment line with environment variables expanded.

        Returns:
            Next line with %VAR% replaced by environment values

        Raises:
            StopIteration: When end of file is reached
        """
        line = self.f.__next__()
        while line.startswith(self.commentstring):
            line = self.f.__next__()
        return re.sub('%.*?%', substenv, line)


class CsvFile(coshsh.datasource.Datasource):
    """CSV file datasource for monitoring configuration data.

    Reads monitoring objects (hosts, applications, contacts, etc.) from
    CSV files with standardized naming: {name}_{type}.csv

    Expected Files:
        {name}_hosts.csv              - Host definitions
        {name}_applications.csv       - Application definitions
        {name}_applicationdetails.csv - Monitoring details for apps
        {name}_contactgroups.csv      - Contactgroup assignments
        {name}_contacts.csv           - Contact definitions

    Features:
        - Automatic hostname regex expansion
        - Comment line support (lines starting with #)
        - Environment variable expansion (%VAR% syntax)
        - Filter column for selective processing
        - Missing file tolerance (logs debug, continues)

    Configuration:
        [datasource_csv1]
        type = csv
        name = monitoring           # File prefix
        dir = /path/to/csv/files    # Directory containing CSVs
        filter_column = coshsh_filter  # Optional: custom filter column

    Attributes:
        name: Datasource name (used as file prefix)
        dir: Directory containing CSV files
        filter_column: Column name for filtering (default: 'coshsh_filter')
        objects: Dictionary of collected objects (inherited)
        csv_hosts: Full path to hosts CSV
        csv_applications: Full path to applications CSV
        csv_applicationdetails: Full path to application details CSV
        csv_contactgroups: Full path to contactgroups CSV
        csv_contacts: Full path to contacts CSV
        file_class: Class used for reading files (CommentedFileEnv)
    """

    def __init__(self, **kwargs) -> None:
        """Initialize CSV file datasource.

        Args:
            **kwargs: Configuration parameters including:
                name (str): Datasource name (file prefix)
                dir (str): Directory path containing CSV files
                filter_column (str, optional): Filter column name
                    (default: 'coshsh_filter')
        """
        super().__init__(**kwargs)
        self.name: str = kwargs["name"]
        self.dir: str = kwargs["dir"]
        self.filter_column: str = kwargs.get("filter_column", "coshsh_filter")
        self.objects: Dict[str, Dict[str, Any]] = {}

    def open(self) -> None:
        """Open datasource and prepare file paths.

        Validates that the CSV directory exists and constructs full paths
        to all expected CSV files.

        Raises:
            DatasourceNotAvailable: If directory doesn't exist
        """
        logger.info(f'open datasource {self.name}')
        if not os.path.exists(self.dir):
            logger.error(f'csv dir {self.dir} does not exist')
            raise coshsh.datasource.DatasourceNotAvailable

        self.csv_hosts = os.path.join(self.dir, self.name + '_hosts.csv')
        self.csv_applications = os.path.join(self.dir, self.name + '_applications.csv')
        self.csv_applicationdetails = os.path.join(self.dir, self.name + '_applicationdetails.csv')
        self.csv_contactgroups = os.path.join(self.dir, self.name + '_contactgroups.csv')
        self.csv_contacts = os.path.join(self.dir, self.name + '_contacts.csv')
        self.file_class = CommentedFileEnv

    def record_valid(self, filter: Optional[str], row: Dict[str, str]) -> bool:
        """Check if a CSV row passes the filter.

        If filter is specified and the row contains filter_column,
        validates that the column value matches the filter.

        Args:
            filter: Filter value to match (None = accept all)
            row: CSV row as dictionary

        Returns:
            True if row passes filter, False otherwise

        Example:
            filter='production'
            row={'host_name': 'web01', 'coshsh_filter': 'production'}
            Returns: True

            row={'host_name': 'web02', 'coshsh_filter': 'staging'}
            Returns: False
        """
        if filter and self.filter_column in row:
            return filter == row[self.filter_column]
        else:
            return True

    def read(
        self,
        filter: Optional[str] = None,
        objects: Optional[Dict[str, Dict[str, Any]]] = None,
        force: bool = False,
        **kwargs
    ) -> None:
        """Read monitoring objects from CSV files.

        Reads all CSV files and populates the objects dictionary with
        Host, Application, MonitoringDetail, ContactGroup, and Contact
        objects.

        Processing Order:
            1. Hosts (no dependencies)
            2. Applications (can reference hosts via regex)
            3. Application Details (references applications)
            4. Contactgroups (references hosts/applications)
            5. Contacts (independent)

        Regex Hostname Expansion:
            If a hostname contains '[' or '*', it's treated as a regex
            pattern. The plugin finds all matching hosts and creates
            one object per match.

            Example:
                CSV: host_name,name,type
                     web[0-9]+,apache,webserver

                If hosts contain: web01, web02, web99
                Creates 3 applications: (web01, apache, webserver),
                                       (web02, apache, webserver),
                                       (web99, apache, webserver)

        Args:
            filter: Optional filter value for filter_column
            objects: Dictionary to populate with objects
            force: Force reading even if not current (unused)
            **kwargs: Additional parameters (unused)
        """
        self.objects = objects if objects is not None else {}

        # Read hosts
        try:
            with io.open(self.csv_hosts) as f:
                hostreader = list(csv.DictReader(self.file_class(f)))
            logger.info(f'read hosts from {self.csv_hosts}')
        except Exception as exp:
            logger.debug(exp)
            hostreader = []

        # host_name,address,type,os,hardware,virtual,notification_period,location,department
        for row in hostreader:
            if not self.record_valid(filter, row):
                continue

            row["templates"] = ["generic-host"]

            # Normalize attribute values to lowercase
            for attr in [k for k in row.keys() if k in ['type', 'os', 'hardware', 'virtual']]:
                try:
                    row[attr] = row[attr].lower()
                except Exception:
                    pass

            # Parse semicolon-separated hostgroups
            if "hostgroups" in row:
                row["hostgroups"] = [hg.strip() for hg in row["hostgroups"].split(";")]

            h = coshsh.host.Host(row)
            self.add('hosts', h)

        # Read applications
        try:
            with io.open(self.csv_applications) as f:
                appreader = list(csv.DictReader(self.file_class(f)))
            logger.info(f'read applications from {self.csv_applications}')
        except Exception as exp:
            logger.debug(exp)
            appreader = []

        resolvedrows = []
        # name,type,component,version,host_name,check_period
        for row in appreader:
            if not self.record_valid(filter, row):
                continue

            # Normalize attribute values to lowercase
            for attr in [k for k in row.keys() if k in ['name', 'type', 'component', 'version']]:
                try:
                    row[attr] = row[attr].lower()
                except Exception:
                    pass

            # Expand regex hostnames
            if '[' in row['host_name'] or '*' in row['host_name']:
                # hostnames can be regular expressions
                matching_hosts = [
                    h for h in self.objects['hosts'].keys()
                    if re.match('^(' + row['host_name'] + ')', h)
                ]
                for host_name in matching_hosts:
                    row['host_name'] = host_name
                    resolvedrows.append(copy(row))
            else:
                resolvedrows.append(copy(row))

        for row in resolvedrows:
            a = coshsh.application.Application(row)
            self.add('applications', a)

        # Read application details
        try:
            with io.open(self.csv_applicationdetails) as f:
                appdetailreader = list(csv.DictReader(self.file_class(f)))
            logger.info(f'read appdetails from {self.csv_applicationdetails}')
        except Exception as exp:
            logger.debug(exp)
            appdetailreader = []

        resolvedrows = []
        # host_name,name,type,monitoring_type,monitoring_0,monitoring_1,monitoring_2,monitoring_3,monitoring_4,monitoring_5
        for row in appdetailreader:
            if not self.record_valid(filter, row):
                continue

            # Expand regex hostnames
            if '[' in row['host_name'] or '*' in row['host_name']:
                # hostnames can be regular expressions
                matching_hosts = [
                    h for h in self.objects['hosts'].keys()
                    if re.match('^(' + row['host_name'] + ')', h)
                ]
                for host_name in matching_hosts:
                    row['host_name'] = host_name
                    resolvedrows.append(copy(row))
            else:
                resolvedrows.append(copy(row))

        for row in resolvedrows:
            # Normalize attribute values to lowercase
            for attr in [k for k in row.keys() if k in ['name', 'type', 'component', 'version']]:
                row[attr] = row[attr].lower()

            application_id = f"{row['host_name']}+{row['name']}+{row['type']}"
            detail = coshsh.monitoringdetail.MonitoringDetail(row)
            self.add('details', detail)

        # Read contactgroups
        try:
            with io.open(self.csv_contactgroups) as f:
                contactgroupreader = list(csv.DictReader(self.file_class(f)))
            logger.info(f'read contactgroups from {self.csv_contactgroups}')
        except Exception as exp:
            logger.debug(exp)
            contactgroupreader = []

        resolvedrows = []
        # host_name,name,type,groups
        for row in contactgroupreader:
            if not self.record_valid(filter, row):
                continue

            # Expand regex hostnames
            if '[' in row['host_name'] or '*' in row['host_name']:
                # hostnames can be regular expressions
                matching_hosts = [
                    h for h in self.objects['hosts'].keys()
                    if re.match('^(' + row['host_name'] + ')', h)
                ]
                for host_name in matching_hosts:
                    row['host_name'] = host_name
                    resolvedrows.append(copy(row))
            else:
                resolvedrows.append(copy(row))

        for row in resolvedrows:
            application_id = f"{row['host_name']}+{row['name']}+{row['type']}"

            # Parse colon-separated groups
            for group in row["groups"].split(":"):
                # Create contactgroup if it doesn't exist
                if not self.find('contactgroups', group):
                    self.add('contactgroups', coshsh.contactgroup.ContactGroup({
                        'contactgroup_name': group
                    }))

                # Assign to application or host
                if self.find('applications', application_id) and row["name"] == "os":
                    # OS application contacts
                    if group not in self.get('applications', application_id).contact_groups:
                        self.get('applications', application_id).contact_groups.append(group)

                    # OS contacts also are host's contacts
                    if group not in self.get('hosts', row["host_name"]).contact_groups:
                        self.get('hosts', row["host_name"]).contact_groups.append(group)

                elif self.find('applications', application_id):
                    # Regular application contacts
                    if group not in self.get('applications', application_id).contact_groups:
                        self.get('applications', application_id).contact_groups.append(group)

                elif ("name" not in row or not row['name']) and self.find('hosts', row['host_name']):
                    # Host-level contacts (no application name)
                    if group not in self.get('hosts', row['host_name']).contact_groups:
                        self.get('hosts', row['host_name']).contact_groups.append(group)
                else:
                    pass
                    # it's ok, no host, no app matches this hostname/name/type
                    # maybe it's a mistake, but better be quiet than to fill
                    # up the log file with an error for _every_ application

        # Read contacts
        try:
            with io.open(self.csv_contacts) as f:
                contactreader = list(csv.DictReader(self.file_class(f)))
            logger.info(f'read contacts from {self.csv_contacts}')
        except Exception as exp:
            logger.debug(exp)
            contactreader = []

        # name,type,address,userid,notification_period,groups
        for row in contactreader:
            if not self.record_valid(filter, row):
                continue

            c = coshsh.contact.Contact(row)
            if not self.find('contacts', c.fingerprint()):
                # Parse colon-separated groups
                c.contactgroups.extend(row["groups"].split(":"))
                self.add('contacts', c)


class CsvFileRecipe(CsvFile):
    """Recipe-specific CSV file datasource.

    Extends CsvFile to use recipe-specific filenames:
        {name}_{recipe_name}_{type}.csv

    instead of:
        {name}_{type}.csv

    This allows different recipes to have separate CSV files in the
    same directory.

    Example:
        Configuration:
            [datasource_csv1]
            type = recipe_csv
            name = monitoring
            dir = /path/to/csv

        For recipe "production":
            monitoring_production_hosts.csv
            monitoring_production_applications.csv
            etc.

        For recipe "staging":
            monitoring_staging_hosts.csv
            monitoring_staging_applications.csv
            etc.

    Note:
        The recipe name is set automatically by the Recipe class
        via the recipe_name attribute inherited from Datasource.
    """

    def open(self) -> None:
        """Open datasource and prepare recipe-specific file paths.

        Constructs paths using {name}_{recipe_name}_{type}.csv pattern.

        Raises:
            DatasourceNotAvailable: If directory doesn't exist
        """
        logger.info(f'open datasource {self.name}')
        if not os.path.exists(self.dir):
            logger.error(f'csv dir {self.dir} does not exist')
            raise coshsh.datasource.DatasourceNotAvailable

        self.csv_hosts = os.path.join(
            self.dir, f'{self.name}_{self.recipe_name}_hosts.csv'
        )
        self.csv_applications = os.path.join(
            self.dir, f'{self.name}_{self.recipe_name}_applications.csv'
        )
        self.csv_applicationdetails = os.path.join(
            self.dir, f'{self.name}_{self.recipe_name}_applicationdetails.csv'
        )
        self.csv_contactgroups = os.path.join(
            self.dir, f'{self.name}_{self.recipe_name}_contactgroups.csv'
        )
        self.csv_contacts = os.path.join(
            self.dir, f'{self.name}_{self.recipe_name}_contacts.csv'
        )
        self.file_class = CommentedFileEnv
