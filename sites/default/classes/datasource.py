#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import os
from util import compare_attr, is_attr
from coshsh.log import logger
from item import Item
from templaterule import TemplateRule


class DatasourceNotImplemented(Exception):
    pass

class DatasourceNotReady(Exception):
    # datasource is currently being updated
    pass

class DatasourceNotAvailable(Exception):
    pass


class Datasource(object):

    my_type = 'datasource'

    def __new__(cls, **params):
        print "new datasource", params
        try:
            newcls = cls.get_class(params)
            return newcls.__new__(newcls, params)
        except ImportError as exc:
            logger.info("found no working code for application %s (%s)" % (params.get("type", "null_type"), exc))
            raise ApplicationNotImplemented
        except Exception as exc:
            logger.info("found unknown datasource %s" % (params.get("type", "null_type"),))
            raise DatasourceNotImplemented

    @classmethod
    def get_class(cls, params={}):
        for class_func in cls.class_factory:
            try:
                newcls = class_func(params)
                if newcls:
                    return newcls
            except Exception:
                pass
        logger.debug("found no matching class for this datasource %s" % params)



