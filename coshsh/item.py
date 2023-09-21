#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import os
import re
import locale
import logging
import functools
from jinja2 import FileSystemLoader, Environment, TemplateSyntaxError, TemplateNotFound
from copy import copy, deepcopy
import coshsh

logger = logging.getLogger('coshsh')


class EmptyObject(object):
    pass


class Item(coshsh.datainterface.CoshshDatainterface):
    template_cache = {}

    @classmethod
    def reload_template_path(cls):
        loader = FileSystemLoader(cls.templates_path)
        cls.env = Environment(loader=loader)
        cls.env.trim_blocks = True

    def __init__(self, params={}):
        for key in params:
            if hasattr(self, "dont_strip_attributes") and isinstance(params[key], str):
                if isinstance(self.dont_strip_attributes, bool) and self.dont_strip_attributes == True:
                    setattr(self, key, params[key])
                elif isinstance(self.dont_strip_attributes, list) and key in self.dont_strip_attributes:
                    setattr(self, key, params[key])
                else:
                    setattr(self, key, params[key].strip())
            elif isinstance(params[key], str):
                setattr(self, key, params[key].strip())
            else:
                setattr(self, key, params[key])

        if not hasattr(self, "monitoring_details"):
            # if not pre-set through the class
            self.monitoring_details = []
        else:
            setattr(self, "monitoring_details", list(self.__class__.monitoring_details))
        self.config_files = {}

    def write_config(self, target_dir, want_tool=None):
        my_target_dir = os.path.join(target_dir, "hosts", self.host_name)
        if not os.path.exists(my_target_dir):
            os.makedirs(my_target_dir)
        for tool in self.config_files:
            if not want_tool or want_tool == tool:
                for file in self.config_files[tool]:
                    content = self.config_files[tool][file]
                    with open(os.path.join(my_target_dir, file), "w") as f:
                        f.write(content)

    def resolve_monitoring_details(self):
        details = [d for d in self.monitoring_details]
        for detail in details:
            property = detail.__class__.property
            if property == "generic":
                if detail.__class__.property_type == dict:
                    for key in detail.dictionary:
                        if key:
                            if ":" in key:
                                dictname, key = key.split(":")
                                try:
                                    setattr(getattr(self, dictname), key, detail.dictionary[dictname + ":" + key])
                                except Exception:
                                    setattr(self, dictname, EmptyObject())
                                    setattr(getattr(self, dictname), key, detail.dictionary[dictname + ":" + key])
                            else:
                                setattr(self, key, detail.dictionary[key])
                elif detail.__class__.property_type == list:
                    for key in detail.dictionary:
                        if key:
                            try:
                                getattr(self, key).extend(detail.dictionary[key])
                            except Exception:
                                setattr(self, key, detail.dictionary[key])
                else:
                    setattr(self, detail.attribute, detail.value)
            else:
                if detail.__class__.property_type == list:
                    if not hasattr(self, property):
                        setattr(self, property, [])
                    if hasattr(detail.__class__, "unique_attribute"):
                        # from the details remove an existing detail
                        # - which is of this class
                        # - which has the same unique_attr
                        if [o for o in getattr(self, property) if o.__class__ == detail.__class__ and getattr(o, detail.__class__.unique_attribute) == getattr(detail, detail.__class__.unique_attribute)]:
                            old = getattr(self, property)
                            new = [o for o in old if ((o.__class__ != detail.__class__) or (getattr(o, detail.__class__.unique_attribute) != getattr(detail, detail.__class__.unique_attribute)))]
                            new.append(detail)
                            setattr(self, property, new)
                        #print "res", self.host.host_name, detail.path
                        else:
                            getattr(self, property).append(detail)
                    else:
                        if hasattr(detail.__class__, "property_attr"):
                            getattr(self, property).append(getattr(detail, getattr(detail.__class__, "property_attr")))
                        else:
                            getattr(self, property).append(detail)
                elif detail.__class__.property_type == dict:
                    if not hasattr(self, property):
                        setattr(self, property, {})
                    if hasattr(detail, "key") and hasattr(detail, "value"):
                        getattr(self, property)[detail.key] = detail.value
                else:
                    if getattr(detail.__class__, 'property_flat', False):
                        # ex. MonitoringDetailRole: appl.role == str instead of appl.role.role == str
                        setattr(self, property, getattr(detail, property))
                    else:
                        setattr(self, property, detail)
            # This detail has been resolved. Maybe we run resolve_monitoring_details
            # later again, we don't want to repeat ourselves.
            self.monitoring_details.remove(detail)
        self.wemustrepeat()
        # example: if we have self.ports
        # and self.ports[0] has an inside property ports
        # and self has d default property port (set in __init__)
        # replace the self.port by self.ports[0].port
        for one_property in [detail.__class__.property.rstrip('s') for detail in details if detail.__class__.property_type == list and not hasattr(detail.__class__, "unique_attribute") and not hasattr(detail.__class__, "property_attr") and detail.__class__.property.endswith('s') and hasattr(self, detail.__class__.property.rstrip('s'))]:
            if hasattr(getattr(self, one_property + 's')[0], one_property):
                setattr(self, one_property, getattr(getattr(self, one_property + 's')[0], one_property))

    def wemustrepeat(self):
        """
        This method is called by some classes if different monitoring_details need to interact.
        Ex. (username/password was set in a LOGIN detail and/or a URL detail
        The name is a tribute to my favorite band.
        https://www.youtube.com/watch?v=hRguZr0xCOc&feature=youtu.be&t=212
        """
        pass

    def pythonize(self):
        if hasattr(self, "templates"):
            self.templates = self.templates.split(',')
        if hasattr(self, "contactgroups"):
            self.contactgroups = self.contactgroups.split(',')
        if hasattr(self, "contact_groups"): #! contacts have contact!_!groups
            self.contact_groups = self.contact_groups.split(',')
        if hasattr(self, "contacts"):
            self.contacts = self.contacts.split(',')
        if hasattr(self, "hostgroups"):
            self.hostgroups = self.hostgroups.split(',')
        if hasattr(self, "servicegroups"):
            self.servicegroups = self.servicegroups.split(',')
        if hasattr(self, "members"):
            self.members = self.members.split(',')
        if hasattr(self, "parents"):
            self.parents = self.parents.split(',')
        if hasattr(self, "host_notification_commands"):
            self.host_notification_commands = self.host_notification_commands.split(',')
        if hasattr(self, "service_notification_commands"):
            self.service_notification_commands = self.service_notification_commands.split(',')

    def depythonize(self):
        if hasattr(self, "templates"):
            self.templates = ",".join(self.templates)
        if hasattr(self, "contactgroups"):
            self.contactgroups = ",".join(sorted(list(set(self.contactgroups))))
        if hasattr(self, "contact_groups"):
            self.contact_groups = ",".join(sorted(list(set(self.contact_groups))))
        if hasattr(self, "contacts"):
            self.contacts = ",".join(sorted(list(set(self.contacts))))
        if hasattr(self, "hostgroups"):
            self.hostgroups = ",".join(sorted(list(set(self.hostgroups))))
        if hasattr(self, "servicegroups"):
            self.servicegroups = ",".join(sorted(list(set(self.servicegroups))))
        if hasattr(self, "members"):
            self.members = ",".join(sorted(list(set(self.members))))
        if hasattr(self, "parents"):
            self.parents = ",".join(sorted(list(set(self.parents))))
        if hasattr(self, "host_notification_commands"):
            self.host_notification_commands = ",".join(sorted(list(set(self.host_notification_commands))))
        if hasattr(self, "service_notification_commands"):
            self.service_notification_commands = ",".join(sorted(list(set(self.service_notification_commands))))

    def render_cfg_template(self, jinja2, template_cache, name, output_name, suffix, for_tool, **kwargs):
        render_errors = 0
        try:
            if not name in template_cache:
                template_cache[name] = jinja2.env.get_template(name + ".tpl")
                logger.info("load template " + name)
        except TemplateSyntaxError as e:
            logger.critical("%s template %s has an error in line %d: %s" % (self.__class__.__name__, name, e.lineno, e.message), exc_info=1)
            render_errors += 1
        except TemplateNotFound:
            logger.error("cannot find template " + name)
        except Exception as exp:
            logger.critical("error in template %s (%s,%s)" % (name, exp.__class__.__name__, exp), exc_info=1)
            render_errors += 1

        if name in template_cache:
            # transform hostgroups, contacts, etc. from list to string
            self.depythonize()
            try:
                if not for_tool in self.config_files:
                    self.config_files[for_tool] = {}
                if suffix:
                    self.config_files[for_tool][output_name + "." + suffix] = template_cache[name].render(kwargs)
                else:
                    # files without suffix
                    self.config_files[for_tool][output_name] = template_cache[name].render(kwargs)
            except Exception as exp:
                if hasattr(self, "fingerprint"):
                    logger.critical("render exception in template %s for %s %s: %s" % (name, self, self.fingerprint(), exp), exc_info=1)
                else:
                    logger.critical("render exception in template %s for %s: %s" % (name, self, exp), exc_info=1)
                render_errors += 1
            # transform hostgroups, contacts, etc. back to lists
            self.pythonize()
        return render_errors

    def render(self, template_cache, jinja2, recipe):
        render_errors = 0
        if not hasattr(self, 'template_rules'):
            return render_errors
        for rule in self.template_rules:
            render_this = False
            try:
                if not rule.needsattr:
                    # TemplateRule(template="os_solaris_default")
                    render_this = True
    
                elif (hasattr(self, rule.needsattr) and rule.isattr == None):
                    # TemplateRule(needsattr=None,template="os_solaris_default")
                    render_this = True
    
                elif hasattr(self, rule.needsattr) and not isinstance (getattr(self, rule.needsattr), list) and ((getattr(self, rule.needsattr) == rule.isattr) or re.match(rule.isattr, getattr(self, rule.needsattr))):
                    # TemplateRule(needsattr="cluster", isattr="veritas",
                    #     template="os_solaris_cluster_veritas")
                    render_this = True
    
                elif hasattr(self, rule.needsattr) and isinstance (getattr(self, rule.needsattr), list) and [elem for elem in getattr(self, rule.needsattr) if (elem == rule.isattr or re.match(rule.isattr, elem))]:
                    # TemplateRule(needsattr="hostgroups",
                    #     isattr="cluster_solaris_veritas.*",
                    #     template="os_solaris_cluster_veritas")
                    render_this = True
                    
                elif hasattr(self, rule.needsattr) and isinstance (getattr(self, rule.needsattr), list):
                    pass
            except Exception as e:
                logger.critical("error in %s template rules. please check %s. Error was: %s" % (self.__class__.__name__, rule, str(e)), exc_info=1)
                render_errors += 1

            if render_this:
                if rule.unique_config and isinstance(rule.unique_attr, str) and hasattr(self, rule.unique_attr):
                    render_errors += self.render_cfg_template(jinja2, template_cache, rule.template, rule.unique_config % getattr(self, rule.unique_attr), rule.suffix, rule.for_tool, **dict([(rule.self_name, self), ("recipe", recipe)]))
                elif rule.unique_config and isinstance(rule.unique_attr, list) and functools.reduce(lambda x, y: x and y, [hasattr(self, ua) for ua in rule.unique_attr]):
                    render_errors += self.render_cfg_template(jinja2, template_cache, rule.template, rule.unique_config % tuple([getattr(self, a) for a in rule.unique_attr]), rule.suffix, rule.for_tool, **dict([(rule.self_name, self), ("recipe", recipe)]))
                else:
                    render_errors += self.render_cfg_template(jinja2, template_cache, rule.template, rule.template, rule.suffix, rule.for_tool, **dict([(rule.self_name, self), ("recipe", recipe)]))
        return render_errors

    def fingerprint(self):
        try:
            return "%s+%s+%s" % (self.host_name, self.name, self.type)
        except: pass
        try:
            return "%s" % (self.host_name, )
        except: pass
        raise "impossible fingerprint"

