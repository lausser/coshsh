#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Represents a monitored application or service running on a host.

Sole responsibility: use a class factory to auto-select the correct
Application subclass (e.g. ``os_windows``, ``app_db_mysql``) based on
the application's type, name, and other identifying attributes.  Once the
right subclass is chosen its ``template_rules`` drive config generation.

This module does NOT own template files -- those live on disk in the
directories listed in ``templates_dir`` and are loaded by the Jinja2
environment configured on the Item base class.
"""

import sys
import os
import logging
import coshsh

logger = logging.getLogger('coshsh')


class Application(coshsh.item.Item):

    class_factory = []
    class_file_prefixes = ["app_", "os_"]
    class_file_ident_function = "__mi_ident__"
    my_type = "application"
    lower_columns = ['name', 'type', 'component', 'version', 'patchlevel']

    def __init__(self, params):
        """Initialise an Application, auto-selecting the correct subclass.

        When called as ``Application(params)`` (the generic base class),
        this method acts as a class factory redirect:

        1. Normalise identifying columns (name, type, ...) to lowercase.
        2. Call ``get_class(params)`` to scan all registered ``__mi_ident__``
           functions and find the subclass that claims this application.
        3. Mutate ``self.__class__`` to the discovered subclass (or to
           ``GenericApplication`` if nothing matched) and re-invoke
           ``__init__`` so the subclass-specific initialisation runs.

        When called on an already-resolved subclass (the ``else`` branch),
        no factory logic executes -- the subclass simply inherits from
        Item.
        """
        # WHY: class factory redirect -- when Application(params) is called,
        # the base __init__ detects it is the generic class, calls
        # get_class(params) to find the right subclass (e.g. os_windows,
        # app_db_mysql), then re-invokes __init__ as that subclass.  This
        # lets datasources always instantiate ``Application(params)`` without
        # needing to know which concrete class to use.
        #print "Application init", self.__class__, self.__class__.__name__, len(self.__class__.class_factory)
        if self.__class__.__name__ == "Application":
            for c in self.__class__.lower_columns:
                try:
                    params[c] = params[c].lower()
                except Exception:
                    if c in params:
                        params[c] = None
            newcls = self.__class__.get_class(params)
            if newcls:
                self.__class__ = newcls
                self.contact_groups = []
                super(Application, self).__init__(params)
                self.__init__(params)
                self.fingerprint = lambda s=self:s.__class__.fingerprint(params)
            else:
                # WHY: GenericApplication is the fallback when no ident
                # function matches.  It only renders if the object has
                # meaningful monitoring details (processes, filesystems,
                # ports, etc.) -- this prevents empty config files for
                # application types that have no dedicated subclass and no
                # actionable details.
                logger.debug('this will be Generic %s' % params)
                self.__class__ = GenericApplication
                self.contact_groups = []
                super(Application, self).__init__(params)
                self.__init__(params)
                self.fingerprint = lambda s=self:s.__class__.fingerprint(params)
        else:
            pass

    @classmethod
    def fingerprint(self, params={}):
        """Return a unique identity string for this application instance.

        The fingerprint is composed as ``host_name + name + type``.
        These three fields together uniquely identify an application
        instance on a host -- the same application type can appear
        multiple times on one host as long as the name differs.
        """
        # WHY: fingerprint = host_name + name + type -- these three fields
        # together uniquely identify an application instance on a host.
        return "%s+%s+%s" % (params["host_name"], params["name"], params["type"])

    def create_servicegroups(self):
        """Hook for subclasses to define service groups for this application.

        Called during the recipe cook phase.  Subclasses override this to
        populate service group membership based on application attributes.
        """
        pass

    def create_contacts(self):
        """Hook for subclasses to define contacts for this application.

        Called during the recipe cook phase.  Subclasses override this to
        attach contact or contact-group information derived from the
        application's datasource attributes.
        """
        pass

    def create_templates(self):
        """Hook for subclasses to set up custom template rules at runtime.

        Called during the recipe cook phase.  Subclasses override this when
        template rules need to be computed dynamically rather than declared
        as class-level ``template_rules``.
        """
        pass


class GenericApplication(Application):
    """Fallback application class used when no ``__mi_ident__`` function
    claims the application row from the datasource.

    GenericApplication only renders output when the object carries
    meaningful monitoring details (processes, filesystems, ports, etc.)
    to prevent empty, useless config files.
    """

    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None,
            template="app_generic_default",
            unique_attr=['type', 'name'], unique_config="app_%s_%s_default"),
    ]

    def __init__(self, params={}):
        """Initialise a GenericApplication, delegating to Application."""
        super(GenericApplication, self).__init__(params)

    def render(self, template_cache, jinja2, recipe):
        """Render only if this generic application has actionable details.

        Checks for the presence of at least one monitoring-relevant
        attribute (processes, filesystems, cfgfiles, files, ports, urls,
        or services).  If none exist the application was likely imported
        from the datasource with no detail rows, so rendering is skipped
        to avoid producing empty config files.

        Returns the total number of render errors (0 when skipped).
        """
        # WHY: GenericApplication only renders if it has meaningful
        # monitoring details -- this prevents empty config files for
        # application types that have no dedicated subclass and no
        # actionable detail rows from the datasource.
        # Maybe we find some processes, ports, filesystems in the
        # monitoring_details so we can output generic services
        if (hasattr(self, "processes") and self.processes) or (hasattr(self, "filesystems") and self.filesystems) or (hasattr(self, "cfgfiles") and self.cfgfiles) or (hasattr(self, "files") and self.files) or (hasattr(self, "ports") and self.ports) or (hasattr(self, "urls") and self.urls) or (hasattr(self, "services") and self.services):
            return super(GenericApplication, self).render(template_cache, jinja2, recipe)
        else:
            return 0

