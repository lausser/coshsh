#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).
import os
import importlib.util
import inspect
import logging

logger = logging.getLogger('coshsh')


class CoshshDatainterface(object):

    class_factory = []
    class_file_prefixes = []
    class_file_ident_function = ""
    my_type = ""

    @classmethod
    def init_class_factory(cls, classpath):
        class_factory = []
        for p in [p for p in reversed(classpath) if os.path.exists(p) and os.path.isdir(p)]:
            for module in [item for item in sorted(os.listdir(p), reverse=True) if item[-3:] == ".py" and (item in cls.class_file_prefixes or [prefix for prefix in cls.class_file_prefixes if item.startswith(prefix)])]:
                try:
                    path = os.path.abspath(os.path.join(p, module))
                    module_name = module.replace('.py', '')

                    # Find the module
                    spec = importlib.util.spec_from_file_location(module_name, path)
                    if spec is not None:
                        toplevel = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(toplevel)
                        
                        for cl in inspect.getmembers(toplevel, inspect.isfunction):
                            if cl[0] == cls.class_file_ident_function:
                                class_factory.append([path, module, cl[1]])
                except Exception as exp:
                    logger.critical("could not load %s %s from %s: %s" % (cls.my_type, module, path, exp))
        cls.update_class_factory(class_factory)
        return class_factory

    @classmethod
    def update_class_factory(cls, class_factory):
        cls.class_factory = class_factory

    @classmethod
    def get_class(cls, params={}):
        for path, module, class_func in reversed(cls.class_factory):
            try:
                newcls = class_func(params)
                if newcls:
                    return newcls
            except Exception as exp:
                print(cls.__name__+".get_class exception", exp)
        logger.debug("found no matching class for this %s %s" % (cls.my_type, params))
        return None

