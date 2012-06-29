#!/usr/bin/env python
# Copyright (C) : Gerhard Lausser, gerhard.lausser@consol.de

import os
from coshsh.site import Site
from coshsh.log import logger


class Generator(object):

    base_dir = os.path.dirname(os.path.dirname(__file__))
    messages = []

    def __init__(self):
        self.sites = {}
        self.datasources = {}


    def add_site(self, *args, **kwargs):
        try:
            site = Site(**kwargs)
            for ds in kwargs["datasources"].split(","):
                if ds in self.datasources: 
                    try:
                        self.datasources[ds].open()
                        self.datasources[ds].set_site(site.name)
                        site.datasources.append(self.datasources[ds])
                    except DatasourceUnavailable as e:
                        pass
            self.sites[kwargs["name"]] = site
        except Exception, e:
            print e
        pass


    def add_datasource(self, *args, **kwargs):
        try:
            if kwargs["type"] == "valuemation":
                from datasource import Valuemation
                datasource = Valuemation(**kwargs)
            elif kwargs["type"] == "csv":
                from datasource import CsvFile
                datasource = CsvFile(**kwargs)
            elif kwargs["type"] == "bmwcmdb":
                from datasource import BmwCmdb
                datasource = BmwCmdb(**kwargs)
            else:
                print "unknown datasource", kwargs
            self.datasources[kwargs["name"]] = datasource
        except Exception as e:
            print "add_datasource", e
        pass


    def run(self):
        for site in self.sites.values():
            try:
                site.count_before_objects()
                site.cleanup_target_dir()
            except Exception, e:
                print e
                logger.info("skipping site %s" % site.name)
            else:
                site.prepare_target_dir()
                site.collect()
                site.render()
                site.output()


