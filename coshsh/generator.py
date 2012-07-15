#!/usr/bin/env python
# Copyright (C) : Gerhard Lausser, gerhard.lausser@consol.de

print "--->generator"
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from site import Site
from log import logger
print "<--generator"


class Generator(object):

    base_dir = os.path.dirname(os.path.dirname(__file__))
    messages = []

    def __init__(self):
        self.sites = {}

    def add_site(self, *args, **kwargs):
        try:
            site = Site(**kwargs)
            self.sites[kwargs["name"]] = site
        except Exception, e:
            print e
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


