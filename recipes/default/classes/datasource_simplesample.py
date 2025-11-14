"""Simple Sample Datasource Plugin

This plugin provides a template/example datasource implementation.

Plugin Identification:
---------------------
Identifies datasource configurations with type = "simplesample".

Purpose:
--------
Serves as a template and starting point for creating custom datasources:
    - Demonstrates basic datasource structure
    - Shows required methods (open, read, close)
    - Provides example of object creation pattern
    - Used in testing and development

Datasource Lifecycle:
--------------------
1. __init__: Configure datasource parameters
2. open: Establish connection to data source
3. read: Fetch and process monitoring objects
4. close: Clean up resources

Configuration Example:
---------------------
Cookbook configuration:
    [datasource_sample]
    type = simplesample
    dir = /path/to/data

Usage:
------
This is a minimal example. Real datasources typically:
    - Connect to databases, APIs, or files
    - Parse and transform data
    - Create Host, Application, Contact objects
    - Add MonitoringDetails to objects

Creating Objects:
----------------
In the read() method, create monitoring objects:
    # Create host
    host = Host({
        'host_name': 'server01',
        'address': '192.168.1.100',
        'type': 'linux'
    })
    self.add('hosts', host)

    # Create application on host
    app = Application({
        'host_name': 'server01',
        'name': 'mysql',
        'type': 'database'
    })
    self.add('applications', app)

    # Add monitoring detail
    detail = MonitoringDetail({
        'host_name': 'server01',
        'name': 'mysql',
        'monitoring_type': 'PORT',
        'monitoring_0': '3306'
    })
    self.add('details', detail)

Object Types:
-------------
Datasources can create these object types:
    - hosts: Server/device definitions
    - applications: Services running on hosts
    - contacts: Notification contacts
    - contactgroups: Contact group definitions
    - details: Monitoring-specific details (ports, credentials, etc.)

Integration:
-----------
Objects from multiple datasources are merged by the recipe.
The 'objects' parameter in read() contains previously loaded objects
from other datasources in the recipe.

Classes:
--------
- SimpleSample: Minimal example datasource implementation
"""

from __future__ import annotations

import os
import re
import logging
from copy import copy
from typing import Optional, Dict, Any

import coshsh
from coshsh.util import compare_attr
from coshsh.datasource import Datasource
from coshsh.host import Host
from coshsh.application import Application
from coshsh.contactgroup import ContactGroup
from coshsh.contact import Contact
from coshsh.monitoringdetail import MonitoringDetail

logger = logging.getLogger('coshsh')


def __ds_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify SimpleSample datasource configurations.

    Called by the plugin factory system to determine if a datasource
    configuration should use the SimpleSample class.

    Args:
        params: Datasource configuration dictionary

    Returns:
        SimpleSample class if type="simplesample"
        None if no match

    Example:
        params = {'type': 'simplesample', 'dir': '/tmp'}
        Returns: SimpleSample class

        params = {'type': 'csvfile'}
        Returns: None
    """
    if params is None:
        params = {}

    if coshsh.util.compare_attr("type", params, "^simplesample$"):
        return SimpleSample
    return None


class SimpleSample(coshsh.datasource.Datasource):
    """Simple sample datasource implementation.

    Minimal example datasource that demonstrates the basic structure
    and required methods for custom datasource plugins.

    Attributes:
        name: Datasource name (from configuration section name)
        dir: Working directory for datasource data
        objects: Dictionary of monitoring objects from all datasources

    Configuration:
        [datasource_sample]
        type = simplesample
        dir = /path/to/data

    Example:
        ds = SimpleSample(
            name='sample_ds',
            dir='/tmp/monitoring'
        )
        ds.open()
        ds.read(objects={})
        ds.close()

    Note:
        This is a template. Real implementations should:
        - Connect to actual data sources (DB, API, files)
        - Parse and validate data
        - Create monitoring objects (hosts, applications, contacts)
        - Handle errors appropriately
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize SimpleSample datasource.

        Args:
            **kwargs: Datasource configuration parameters
                name: Datasource name (from INI section)
                dir: Working directory (default: /tmp)

        Note:
            The name is automatically set from the INI section name.
            For [datasource_mydata], name will be 'mydata'.
        """
        super().__init__(**kwargs)
        # default name is taken from the ini-section
        # [datasource_thisisthename]
        # self.name = kwargs["name"]
        self.dir: str = kwargs.get("dir", "/tmp")
        self.objects: Dict[str, Any] = {}

    def open(self) -> bool:
        """Open/initialize the datasource.

        Called once before reading data. Use this to:
            - Establish database connections
            - Authenticate to APIs
            - Open files
            - Validate configuration

        Returns:
            True if datasource opened successfully
            False if opening failed

        Example:
            # In a real datasource:
            try:
                self.connection = connect_to_database(self.host, self.user)
                return True
            except ConnectionError:
                logger.error("Failed to connect to database")
                return False
        """
        logger.info(f'open datasource {self.name}')
        return True

    def read(
        self,
        filter: Optional[Any] = None,
        objects: Optional[Dict[str, Any]] = None,
        force: Optional[bool] = None,
        **kwargs: Any
    ) -> None:
        """Read and process monitoring objects from datasource.

        Called by the recipe to load monitoring data. Create Host,
        Application, Contact, and MonitoringDetail objects and add
        them using self.add().

        Args:
            filter: Optional filter for selective reading
            objects: Previously loaded objects from other datasources
            force: Force refresh even if cached
            **kwargs: Additional datasource-specific parameters

        Note:
            The objects parameter contains monitoring objects from
            datasources read earlier in the recipe. You can use these
            for reference or enrichment.

        Example:
            # Create a host
            host = Host({
                'host_name': 'server01',
                'address': '192.168.1.100',
                'type': 'linux'
            })
            self.add('hosts', host)

            # Create an application
            app = Application({
                'host_name': 'server01',
                'name': 'apache',
                'type': 'webserver'
            })
            self.add('applications', app)

            # Add monitoring detail
            detail = MonitoringDetail({
                'host_name': 'server01',
                'name': 'apache',
                'monitoring_type': 'PORT',
                'monitoring_0': '80'
            })
            self.add('details', detail)
        """
        if objects is None:
            objects = {}

        logger.info('read items from simplesample')
        # if the recipe has read other datasources before, then these
        # are the objects collected so far:
        self.objects = objects
        # self.add('hosts', Host(...))

    def close(self) -> None:
        """Close/cleanup the datasource.

        Called after all data has been read. Use this to:
            - Close database connections
            - Release file handles
            - Clean up temporary resources
            - Logout from APIs

        Example:
            # In a real datasource:
            if hasattr(self, 'connection') and self.connection:
                self.connection.close()
                logger.info("Database connection closed")
        """
        # close a database, file, ...
        pass

