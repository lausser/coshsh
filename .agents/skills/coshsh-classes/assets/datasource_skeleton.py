#!/usr/bin/env python
# coshsh datasource skeleton.
# File name MUST be datasource_<something>.py to be auto-discovered.
# Place in a directory listed in the recipe's classes_dir.

import logging

from coshsh.datasource import (
    Datasource,
    DatasourceNotAvailable,
    DatasourceNotCurrent,
    DatasourceCorrupt,
)
from coshsh.host import Host
from coshsh.application import Application
from coshsh.monitoringdetail import MonitoringDetail
from coshsh.contact import Contact
from coshsh.contactgroup import ContactGroup

logger = logging.getLogger("coshsh")


def __ds_ident__(params={}):
    """Called for every [datasource_*] section in the cookbook.

    Return the class to instantiate when the section matches, else None.
    The standard convention is to dispatch on params["type"].
    """
    if params.get("type", "").lower() == "CHANGEME":
        return MyDatasource
    return None


class MyDatasource(Datasource):
    """One-line description of where data comes from."""

    def __init__(self, **kwargs):
        # MANDATORY — the base class wires up self.name and shared state.
        super().__init__(**kwargs)
        # Stash the cookbook params you'll need later.
        # Every key from the [datasource_X] section is in kwargs.
        self.dir = kwargs.get("dir")
        self.url = kwargs.get("url")
        # If a parameter is required, fail loudly here.

    def open(self):
        """Connect / open files. Called once per recipe run.

        Raise DatasourceNotAvailable if the source can't be reached;
        the recipe will then continue with prior data if max_delta allows.
        """
        try:
            # connect, open file, etc.
            pass
        except Exception as e:
            logger.error("MyDatasource open failed: %s", e)
            raise DatasourceNotAvailable from e

    def read(self, filter=None, objects={}, force=False, **kwargs):
        """Populate objects with Hosts, Applications, MonitoringDetails.

        MANDATORY: bind the shared objects dict to self.objects so that
        self.add('hosts', host) registers into the dict everyone reads from.
        """
        self.objects = objects

        # --- iterate over your source ----------------------------------
        for row in self._iter_rows():
            # Hosts — required fields: host_name, address
            host = Host({
                "host_name": row["hostname"],
                "address": row["ip"],
                # optional:
                # "hostgroups": "linux,prod",
                # "contact_groups": "ops,oncall",
                # any other key becomes available as host.<key>
            })
            self.add("hosts", host)

            # Applications — required: host_name, name, type
            # The class for this app is selected by __mi_ident__ functions
            # in app_*.py / os_*.py files matching on params["type"].
            app = Application({
                "host_name": row["hostname"],
                "name": "os",
                "type": row["os"],            # e.g. "redhat", "windows"
            })
            self.add("applications", app)

            # MonitoringDetail — the host_name+name+type triple MUST
            # match the Application above for the detail to attach.
            for fs in row.get("filesystems", []):
                detail = MonitoringDetail({
                    "host_name": row["hostname"],
                    "name": "os",
                    "type": row["os"],
                    "monitoring_type": "FILESYSTEM",
                    "monitoring_0": fs["path"],
                    "monitoring_1": fs.get("warn", 80),
                    "monitoring_2": fs.get("crit", 90),
                })
                self.add("details", detail)

        return True

    def close(self):
        """Tear down connections. Called once at end of read phase."""
        pass

    # --- private helpers ----------------------------------------------
    def _iter_rows(self):
        # Replace with your actual source iteration (DB cursor, API
        # pagination, file lines, ...).
        return []
