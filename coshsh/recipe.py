#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""
Recipe: the central orchestration unit for a single coshsh configuration-generation run.

A Recipe ties together one or more datasources (which provide raw host/application/contact
data), one or more datarecipients (which write out the rendered monitoring configs), and
optionally one or more vaults (which supply secrets like database passwords).

Sole responsibility:
    - Load and wire together vaults, datasources, and datarecipients.
    - Drive the collect -> assemble -> render -> output pipeline for one named recipe.
    - Guard against concurrent runs via PID-file locking.

What this module does NOT do:
    - It does NOT parse the cookbook .cfg files (that is coshsh.generator).
    - It does NOT implement any specific datasource, datarecipient, or vault logic
      (those live in plugin classes discovered via class factories).
    - It does NOT write monitoring config files to disk itself (datarecipients do that).

Key classes:
    Recipe  -- the main orchestrator described above.
    RecipePidAlreadyRunning / RecipePidNotWritable / RecipePidGarbage
            -- exceptions for the PID-file based concurrency guard.

AI agent note:
    The lifecycle of a Recipe during a normal coshsh-cook run is:
        1. __init__         (parse config, set up Jinja2, init class factories)
        2. add_vault()      (load vault secrets -- MUST happen before add_datasource)
        3. add_datasource() / add_datarecipient()  (secrets are substituted here)
        4. pid_protect()    (acquire exclusive lock)
        5. collect()        (read raw data from all datasources into self.objects)
        6. assemble()       (build cross-references: details->apps, apps->hosts, hostgroups)
        7. render()         (apply Jinja2 templates to produce config file content)
        8. output()         (hand rendered objects to datarecipients for writing)
        9. pid_remove()     (release lock)
    Steps 5-8 are called from generator.run(); steps 1-4 from generator.read_cookbook().
"""

import sys
import os
import io
import re
import inspect
import time
import logging
import errno
from jinja2 import FileSystemLoader, Environment, TemplateSyntaxError, TemplateNotFound
import coshsh

logger = logging.getLogger('coshsh')

class EmptyObject(object):
    """A bare container used to attach arbitrary attributes (e.g. Jinja2 loader/env)."""
    pass


class RecipePidAlreadyRunning(Exception):
    """Raised when another coshsh process is already running for this recipe (PID file is live)."""
    # found another generator instance
    pass


class RecipePidNotWritable(Exception):
    """Raised when the PID directory or PID file cannot be written (permissions problem)."""
    # pid_dir is not writable
    pass


class RecipePidGarbage(Exception):
    """Raised when the PID file exists but its content is not a valid integer."""
    # pid_file contains no integer
    pass


class Recipe(object):
    """
    Central orchestrator for a single coshsh configuration-generation run.

    A Recipe is created once per ``[recipe:<name>]`` section in the cookbook.
    It owns the full lifecycle: collecting raw monitoring data from datasources,
    assembling cross-references between hosts/applications/details, rendering
    Jinja2 templates, and handing the result to datarecipients for output.

    Key attributes:
        objects     -- dict-of-dicts holding all monitoring items, keyed by
                       category ('hosts', 'applications', ...) and then by
                       fingerprint string (see ``# WHY: objects dict`` below).
        datasources / datarecipients / vaults -- lists of instantiated plugins.
        jinja2      -- namespace carrying the Jinja2 Environment and loader.

    Thread / process safety:
        NOT thread-safe.  Concurrency is handled at the process level via
        pid_protect() / pid_remove().
    """

    # NOTE: attributes_for_adapters lists recipe-level config keys that are
    # forwarded to datasource/datarecipient constructors as "recipe_<key>".
    # If you add a new recipe-level setting that plugins should see, add it here.
    attributes_for_adapters = ["name", "force", "safe_output", "pid_dir", "pid_file", "templates_dir", "classes_dir", "objects_dir", "max_delta", "max_delta_action", "classes_path", "templates_path", "filter", "git_init"]

    def __del__(self):
        pass
        # sys.path is invisible here, so this will fail
        #self.unset_recipe_sys_path()

    def __init__(self, **kwargs):
        """
        Initialise a Recipe from keyword arguments (typically from a cookbook section).

        Preconditions:
            - kwargs must contain at least 'name'.
            - Either 'objects_dir' or 'datarecipients' must be provided.

        Side effects:
            - Sets environment variables RECIPE_NAME, RECIPE_NAME1, ... from the
              recipe name split on underscores.
            - Prepends classes_path directories to sys.path so that plugin modules
              (application classes, datasource classes, etc.) can be imported.
            - Initialises class factories for vaults, datasources, datarecipients,
              applications, monitoring details, and contacts.
            - Creates a Jinja2 Environment loaded from templates_path.
        """
        os.environ['RECIPE_NAME'] = kwargs["name"]
        for idx, elem in enumerate(kwargs["name"].split("_")):
            os.environ['RECIPE_NAME'+str(idx+1)] = elem
        self.additional_recipe_fields = {}
        for key in kwargs.keys():
            if isinstance(kwargs[key], str):
                kwargs[key] = re.sub('%.*?%', coshsh.util.substenv, kwargs[key])
                if key not in self.attributes_for_adapters:
                    self.additional_recipe_fields[key] = re.sub('%.*?%', coshsh.util.substenv, kwargs[key])
        for key in kwargs.keys():
            if isinstance(kwargs[key], str):
                for mapping in kwargs.get("coshsh_config_mappings", {}):
                    mapping_keyword_pat = "(@MAPPING_"+mapping.upper()+r"\[(.*?)\])"
                    for match in re.findall(mapping_keyword_pat, kwargs[key]):
                        if match[1] in kwargs["coshsh_config_mappings"][mapping]:
                            oldstr = "@MAPPING_"+mapping.upper()+"["+match[1]+"]"
                            newstr = kwargs["coshsh_config_mappings"][mapping][match[1]]
                            kwargs[key] = kwargs[key].replace(oldstr, newstr)

        # WHY: env_* keys in the recipe INI config set real environment
        # variables.  The "env_" prefix is stripped and the remainder is
        # uppercased: env_foo = bar → os.environ["FOO"] = "bar".
        # This happens early in Recipe.__init__() so that environment
        # variables are available to datasource plugins, vault backends,
        # and Jinja2 templates during the rest of the pipeline.
        for key in kwargs.keys():
            if isinstance(kwargs[key], str) and key.startswith("env_"):
               os.environ[key.replace("env_", "").upper()] = kwargs[key]

        self.name = kwargs["name"]
        self.log_file = kwargs.get("log_file", None)
        self.log_dir = kwargs.get("log_dir", None)
        self.backup_count = kwargs.get("backup_count", None)
        coshsh.util.switch_logging(logdir=self.log_dir, logfile=self.log_file, backup_count=self.backup_count)
        logger.info("recipe %s init" % self.name)
        self.force = kwargs.get("force")
        # WHY: safe_output guards against accidental mass deletion of monitoring
        # configs.  When enabled, if the number of generated hosts/services
        # changes by more than max_delta percent compared to the previous run,
        # the datarecipient will revert the output directory via "git reset --hard"
        # instead of deploying the suspicious config.  This protects production
        # monitoring from a broken or empty datasource that would wipe all checks.
        self.safe_output = kwargs.get("safe_output")
        self.pid_dir = kwargs.get("pid_dir")
        if not self.pid_dir:
            if 'OMD_ROOT' in os.environ:
                self.pid_dir = os.path.join(os.environ['OMD_ROOT'], 'tmp/run')
            elif "cygwin" in sys.platform or "linux" in sys.platform:
                self.pid_dir = "/tmp"
            else:
                self.pid_dir = os.environ.get("%TEMP%", "C:/TEMP")
        self.pid_file = os.path.join(self.pid_dir, "coshsh.pid." + re.sub(r'[/\.]', '_', self.name))

        self.templates_dir = kwargs.get("templates_dir")
        self.classes_dir = kwargs.get("classes_dir")
        self.max_delta = kwargs.get("max_delta", ())
        self.max_delta_action = kwargs.get("max_delta_action", None)
        if isinstance(self.max_delta, str):
            if ":" in self.max_delta:
                self.max_delta = tuple(map(int, self.max_delta.split(":")))
            else:
                self.max_delta = tuple(map(int, (self.max_delta, self.max_delta)))
        self.my_jinja2_extensions = kwargs.get("my_jinja2_extensions", None)
        self.git_init = False if kwargs.get("git_init", "yes") == "no" else True

        if 'OMD_ROOT' in os.environ:
            self.classes_path = [os.path.join(os.environ['OMD_ROOT'], 'share/coshsh/recipes/default/classes')]
        else:
            self.classes_path = [os.path.join(os.path.dirname(__file__), '../recipes/default/classes')]
        if self.classes_dir:
            # WHY: "catchall" directories are appended *after* the default path
            # so that specific class implementations are found first by the
            # class factory; catchall acts as a last-resort fallback.
            self.classes_path = [p.strip() for p in self.classes_dir.split(',') if os.path.basename(p.strip()) != 'catchall'] + self.classes_path + [p.strip() for p in self.classes_dir.split(',') if os.path.basename(p.strip()) == 'catchall']
        self.set_recipe_sys_path()
        if 'OMD_ROOT' in os.environ:
            self.templates_path = [os.path.join(os.environ['OMD_ROOT'], 'share/coshsh/recipes/default/templates')]
        else:
            self.templates_path = [os.path.join(os.path.dirname(__file__), '../recipes/default/templates')]
        if self.templates_dir:
            self.templates_path = [p.strip() for p in self.templates_dir.split(',') if os.path.basename(p.strip()) != 'catchall'] + self.templates_path + [p.strip() for p in self.templates_dir.split(',') if os.path.basename(p.strip()) == 'catchall']
            logger.debug("recipe.templates_path reloaded %s" % ':'.join(self.templates_path))
        logger.info("recipe %s classes_dir %s" % (self.name, ','.join([os.path.abspath(p) for p in self.classes_path])))
        logger.info("recipe %s templates_dir %s" % (self.name, ','.join([os.path.abspath(p) for p in self.templates_path])))

        self.jinja2 = EmptyObject()
        setattr(self.jinja2, 'loader', FileSystemLoader(self.templates_path))
        setattr(self.jinja2, 'env', Environment(loader=self.jinja2.loader, extensions=['jinja2.ext.do']))
        self.jinja2.env.trim_blocks = True
        self.jinja2.env.tests['re_match'] = coshsh.jinja2_extensions.is_re_match
        self.jinja2.env.filters['re_sub'] = coshsh.jinja2_extensions.filter_re_sub
        self.jinja2.env.filters['re_escape'] = coshsh.jinja2_extensions.filter_re_escape
        self.jinja2.env.filters['service'] = coshsh.jinja2_extensions.filter_service
        self.jinja2.env.filters['host'] = coshsh.jinja2_extensions.filter_host
        self.jinja2.env.filters['contact'] = coshsh.jinja2_extensions.filter_contact
        self.jinja2.env.filters['custom_macros'] = coshsh.jinja2_extensions.filter_custom_macros
        self.jinja2.env.filters['rfc3986'] = coshsh.jinja2_extensions.filter_rfc3986
        self.jinja2.env.filters['neighbor_applications'] = coshsh.jinja2_extensions.filter_neighbor_applications
        self.jinja2.env.globals['environ'] = coshsh.jinja2_extensions.global_environ

        if self.my_jinja2_extensions:
            for extension in [e.strip() for e in self.my_jinja2_extensions.split(",")]:
                imported = getattr(__import__("my_jinja2_extensions", fromlist=[extension]), extension)
                if extension.startswith("is_"):
                    self.jinja2.env.tests[extension.replace("is_", "")] = imported
                elif extension.startswith("filter_"):
                    self.jinja2.env.filters[extension.replace("filter_", "")] = imported
                elif extension.startswith("global_"):
                    self.jinja2.env.globals[extension.replace("global_", "")] = imported
            
        # WHY: Vault resolution order -- vaults are loaded and their secrets
        # read *before* datasources and datarecipients are instantiated
        # (see generator.read_cookbook: add_vault() runs first, then
        # add_datasource() / add_datarecipient()).  This is critical because
        # datasource/datarecipient config strings may contain @VAULT[key]
        # placeholders that must be substituted with the actual secrets
        # (e.g. database passwords) at construction time.
        self.vaults = []
        # the vaults' contents
        self.vault_secrets = {}
        self.datasources = []
        self.datarecipients = []

        # WHY: self.objects is a dict-of-dicts.  The outer key is the object
        # category (e.g. 'hosts', 'applications').  The inner key is the
        # *fingerprint* string of each object -- a unique identity derived from
        # the object's essential attributes (e.g. "hostname" for hosts,
        # "hostname+appname+apptype" for applications).  Using fingerprints as
        # keys guarantees O(1) deduplication: when a datasource adds an object
        # that already exists, it simply overwrites the same dict slot instead
        # of creating a duplicate.  It also allows fast cross-referencing
        # during the assemble phase (e.g. looking up an application's host).
        # NOTE: datasource.add() writes into this dict via
        #   self.objects[objtype][obj.fingerprint()] = obj
        # so the fingerprint format is defined per Item subclass, not here.
        self.objects = {
            'hosts': {},
            'hostgroups': {},
            'applications': {},
            'details': {},
            'contacts': {},
            'contactgroups': {},
            'commands': {},
            'timeperiods': {},
            'dependencies': {},
            'bps': {},
        }
        
        self.old_objects = (0, 0)
        self.new_objects = (0, 0)

        self.init_vault_class_factories()
        self.init_ds_dr_class_factories()
        self.init_item_class_factories()

        if kwargs.get("vaults"):
            self.vault_names = [vault.lower().strip() for vault in kwargs.get("vaults").split(",")]
        else:
            self.vault_names = []
        if kwargs.get("datasources"):
            self.datasource_names = [ds.lower().strip() for ds in kwargs.get("datasources").split(",")]
        else:
            self.datasource_names = []
        if kwargs.get("objects_dir") and not kwargs.get("datarecipients"):
            self.objects_dir = kwargs["objects_dir"]
            logger.info("recipe %s objects_dir %s" % (self.name, os.path.abspath(self.objects_dir)))
            self.datarecipient_names = ["datarecipient_coshsh_default"]
        elif kwargs.get("objects_dir") and kwargs.get("datarecipients"):
            self.objects_dir = kwargs["objects_dir"]
            #logger.warning("recipe %s delete parameter objects_dir (use datarecipients instead)" % (self.name, ))
            self.datarecipient_names = [ds.lower().strip() for ds in kwargs.get("datarecipients").split(",")]
        else:
            self.datarecipient_names = [ds.lower().strip() for ds in kwargs.get("datarecipients").split(",")]
        # WHY: ">>>" is a shorthand alias for "datarecipient_coshsh_default"
        # in the INI config.  It allows compact config like:
        #   datarecipients = >>>,SIMPLESAMPLE
        # which expands to: datarecipient_coshsh_default,SIMPLESAMPLE
        # The expansion happens here before any datarecipient objects are created.
        self.datarecipient_names = ['datarecipient_coshsh_default' if dr == '>>>' else dr for dr in self.datarecipient_names]
        if 'datarecipient_coshsh_default' in self.datarecipient_names:
            self.add_datarecipient(**dict([('type', 'datarecipient_coshsh_default'), ('name', 'datarecipient_coshsh_default'), ('objects_dir', self.objects_dir), ('max_delta', self.max_delta), ('max_delta_action', self.max_delta_action), ('safe_output', self.safe_output)]))

        # WHY: filter parsing uses a two-pass approach.  The regex
        # (([^,^(^)]+)\((.*?)\)) splits "dsname(value)" pairs from the
        # filter string.  Pass 1: if the dsname doesn't match a known
        # datasource literally, treat it as a regex and match against all
        # datasource names.  Pass 2: direct name matches override any
        # regex matches, ensuring exact names always take precedence.
        # Example: filter = csv_hosts(host_name ~ 'prod_.*'),ds_(kees)
        # where "ds_" would regex-match multiple datasources.
        self.datasource_filters = {}
        self.filter = kwargs.get("filter")
        if kwargs.get("filter"):
            dsfilter_p = re.compile(r'(([^,^(^)]+)\((.*?)\))')
            for rule in dsfilter_p.findall(self.filter):
                if not rule[1].lower() in self.datasource_names:
                    # koennte ein regex sein
                    tmp_dsname = rule[1]
                    if not tmp_dsname.startswith("^"):
                        tmp_dsname = "^"+tmp_dsname
                    if not tmp_dsname.endswith("^"):
                        tmp_dsname = tmp_dsname+"$"
                    rule_p = re.compile(tmp_dsname)
                    for ds in self.datasource_names:
                        if rule_p.match(ds):
                            self.datasource_filters[ds] = rule[2]
            for rule in dsfilter_p.findall(self.filter):
                # direkte treffer in jedem fall so eintragen
                if rule[1].lower() in self.datasource_names:
                    self.datasource_filters[rule[1].lower()] = rule[2]

        self.render_errors = 0

    def set_recipe_sys_path(self):
        """Prepend classes_path directories to sys.path so plugin modules can be imported."""
        sys.path[0:0] = self.classes_path

    def unset_recipe_sys_path(self):
        """Remove the classes_path entries previously prepended to sys.path."""
        for p in [p for p in self.classes_path if os.path.exists(p) and os.path.isdir(p)]:
            sys.path.pop(0)

    def collect(self):
        """
        Read raw monitoring data from every configured datasource into self.objects.

        Each datasource's read() method populates self.objects with hosts,
        applications, contacts, monitoring details, etc.  If any datasource
        signals a problem (not current, not ready, not available, or generic
        exception), collection is aborted and False is returned.

        Returns:
            True if all datasources were read successfully, False otherwise.

        Side effects:
            - Opens and closes each datasource.
            - Populates self.objects dicts (hosts, applications, details, ...).

        WHY collect() is separate from assemble():
            collect() only reads raw, independent data items from external
            sources (databases, CSV files, APIs).  It does NOT resolve any
            relationships between those items.  assemble() is the phase that
            builds the cross-references -- attaching monitoring details to
            their applications/hosts, linking applications to hosts, creating
            hostgroup objects, and removing orphaned applications.  Keeping
            these two phases separate means: (a) a datasource never needs to
            know about other datasources' data, (b) all data is available
            before relationship resolution starts, and (c) collect failure
            can be detected before any expensive assembly work begins.
        """
        data_valid = True
        for ds in self.datasources:
            filter = self.datasource_filters.get(ds.name)
            try:
                ds.open()
                pre_count = dict([(key, len(self.objects[key].keys())) for key in self.objects.keys()])
                pre_detail_count = sum([(len(obj.monitoring_details) if hasattr(obj, 'monitoring_details') else 99) for objs in [self.objects[key].values() for key in self.objects.keys()] for obj in objs], 0)
                # NOTE: self.objects is passed by reference; the datasource's read()
                # method populates it in place via datasource.add() which keys
                # entries by obj.fingerprint().
                ds.read(filter=filter, objects=self.objects, force=self.force)
                post_count = dict([(key, len(self.objects[key].keys())) for key in self.objects.keys()])
                post_detail_count = sum([(len(obj.monitoring_details) if hasattr(obj, 'monitoring_details') else 99) for objs in [self.objects[key].values() for key in self.objects.keys()] for obj in objs], 0)
                pre_count['details'] = pre_detail_count
                post_count['details'] = post_detail_count
                pre_count.update(dict.fromkeys([k for k in post_count if not k in pre_count], 0))
                chg_keys = [(key, post_count[key] - pre_count[key]) for key in set(list(pre_count.keys()) + list(post_count.keys())) if post_count[key] != pre_count[key]]
                logger.info("recipe %s read from datasource %s %s" % (self.name, ds.name, ", ".join(["%d %s" % (k[1], k[0]) for k in chg_keys])))
                ds.close()
            except coshsh.datasource.DatasourceNotCurrent:
                data_valid = False
                logger.info("datasource %s is not current" % ds.name, exc_info=False)
            except coshsh.datasource.DatasourceNotReady:
                data_valid = False
                logger.info("datasource %s is busy" % ds.name, exc_info=False)
            except coshsh.datasource.DatasourceNotAvailable:
                data_valid = False
                logger.info("datasource %s is not available" % ds.name, exc_info=False)
            except Exception as exp:
                data_valid = False
                logger.critical("datasource %s returns bad data (%s)" % (ds.name, exp), exc_info=True)
            if not data_valid:
                logger.info("aborting collection phase") 
                return False
        return data_valid

    def assemble(self):
        """
        Build cross-references between collected objects and prepare them for rendering.

        This is the second phase after collect().  It performs, in order:
            1. Attach monitoring details to the applications or hosts they belong to
               (matched by application fingerprint).  Generic details (fingerprint
               starting with '*') are broadcast to all matching objects.
            2. Resolve monitoring details on each host, sort list attributes, and
               create templates / hostgroups / contacts for each host.
            3. Link each application to its host, resolve details, create templates /
               servicegroups / contacts.  Orphaned applications (whose host was not
               collected) are removed.
            4. Build HostGroup objects from the hostgroups that hosts declared.

        Preconditions:
            - collect() must have been called successfully first so that
              self.objects is populated.

        Returns:
            True (always).  Errors are logged but do not abort assembly.

        Side effects:
            - Mutates self.objects in place (attaches details, removes orphans,
              creates hostgroup objects).
            - Sets host.applications lists.
        """
        # NOTE: details are matched to applications/hosts by their application_fingerprint(),
        # which returns the same format as the application/host fingerprint key in self.objects.
        # Details whose fingerprint starts with '*' are "generic" and get broadcast
        # to all matching objects in a second pass below.
        generic_details = []
        for detail in self.objects['details'].values():
            fingerprint = detail.application_fingerprint()
            if fingerprint in self.objects['applications']:
                self.objects['applications'][fingerprint].monitoring_details.append(detail)
            elif fingerprint in self.objects['hosts']:
                self.objects['hosts'][fingerprint].monitoring_details.append(detail)
            elif fingerprint.startswith('*'):
                generic_details.append(detail)
            else:
                logger.info("found a %s detail %s for an unknown application %s" % (detail.__class__.__name__, detail, fingerprint))
        for detail in generic_details:
            dfingerprint = detail.application_fingerprint()
            if dfingerprint == '*':
                for host in self.objects['hosts'].values():
                    host.monitoring_details.insert(0, detail)
            else:
                for app in self.objects['applications'].values():
                    afingerprint = app.fingerprint()
                    if dfingerprint[1:] == afingerprint[afingerprint.index('+'):]:
                        app.monitoring_details.insert(0, detail)


        for host in self.objects['hosts'].values():
            host.resolve_monitoring_details()
            for key in [k for k in host.__dict__.keys() if not k.startswith("__") and isinstance(getattr(host, k), (list, tuple)) and k not in ["templates"]]:
                getattr(host, key).sort()
            host.create_templates()
            host.create_hostgroups()
            host.create_contacts()
            setattr(host, "applications", [])

        # NOTE: applications whose host_name does not exist in self.objects['hosts']
        # are considered orphaned and will be removed after this loop.
        orphaned_applications = []
        for app in self.objects['applications'].values():
            try:
                setattr(app, 'host', self.objects['hosts'][app.host_name])
                app.host.applications.append(app)
                app.resolve_monitoring_details()
                for key in [k for k in app.__dict__.keys() if not k.startswith("__") and isinstance(getattr(app, k), (list, tuple))]:
                    # sort monitoring_type/monitoring_0 to bring some order into services,filesystems etc.
                    getattr(app, key).sort()
                app.create_templates()
                app.create_servicegroups()
                app.create_contacts()
            except KeyError:
                logger.info("application %s %s refers to non-existing host %s" % (app.name, app.type, app.host_name))
                orphaned_applications.append(app.fingerprint())
        for oa in orphaned_applications:
            del self.objects['applications'][oa]

        # load the hostgroups-objects after application procession because
        # this allows modification of self.host.hostgroups
        # in application.wemustrepeat()
        for host in self.objects['hosts'].values():
            for hostgroup in host.hostgroups:
                try:
                    self.objects['hostgroups'][hostgroup].append(host.host_name)
                except Exception:
                    self.objects['hostgroups'][hostgroup] = []
                    self.objects['hostgroups'][hostgroup].append(host.host_name)
        for (hostgroup_name, members) in self.objects['hostgroups'].items():
            logger.debug("creating hostgroup %s" % hostgroup_name)
            self.objects['hostgroups'][hostgroup_name] = coshsh.hostgroup.HostGroup({ "hostgroup_name" : hostgroup_name, "members" : members})
            self.objects['hostgroups'][hostgroup_name].create_templates()
            self.objects['hostgroups'][hostgroup_name].create_contacts()

        return True
 
    def render(self):
        """
        Apply Jinja2 templates to every assembled object to produce config file content.

        Iterates over hosts, applications, contactgroups, contacts, hostgroups,
        and any custom object types, calling each object's render() method.
        Rendering errors are accumulated in self.render_errors.

        Preconditions:
            - assemble() must have been called first.

        Side effects:
            - Populates each object's config_files dict with rendered text.
            - Increments self.render_errors on template failures.
        """
        template_cache = {}
        for host in self.objects['hosts'].values():
            self.render_errors += host.render(template_cache, self.jinja2, self)
        for app in self.objects['applications'].values():
            # because of this __new__ construct the Item.searchpath is
            # not inherited. Needs to be done explicitely
            self.render_errors += app.render(template_cache, self.jinja2, self)
        for cg in self.objects['contactgroups'].values():
            self.render_errors += cg.render(template_cache, self.jinja2, self)
        for c in self.objects['contacts'].values():
            self.render_errors += c.render(template_cache, self.jinja2, self)
        for hg in self.objects['hostgroups'].values():
            self.render_errors += hg.render(template_cache, self.jinja2, self)
        # you can put anything in objects (Item class with own templaterules)
        for item in sum([list(self.objects[itype].values()) for itype in self.objects if itype not in ['hosts', 'applications', 'details', 'contactgroups', 'contacts', 'hostgroups']], []):
            # first check hasattr, because somebody may accidentially
            # add objects which are not a subclass of Item.
            # (And such a stupid mistake crashes coshsh-cook)
            if hasattr(item, 'config_files') and not item.config_files:
                # has not been populated with content in the datasource
                # (like bmw appmon timeperiods)
                self.render_errors += item.render(template_cache, self.jinja2, self)
            
    def count_before_objects(self):
        """Count existing config files in output dirs *before* writing new ones (for delta check)."""
        for datarecipient in self.datarecipients:
            datarecipient.count_before_objects()
        self.old_objects = (sum([dr.old_objects[0] for dr in self.datarecipients], 0), sum([dr.old_objects[1] for dr in self.datarecipients], 0))

    def count_after_objects(self):
        """Count config files in output dirs *after* writing (for delta comparison with before)."""
        for datarecipient in self.datarecipients:
            datarecipient.count_after_objects()
        self.new_objects = (sum(0, [dr.new_objects[0] for dr in self.datarecipients]), sum(0, [dr.new_objects[1] for dr in self.datarecipients]))

    def cleanup_target_dir(self):
        """Remove old generated config files from each datarecipient's target directory."""
        for datarecipient in self.datarecipients:
            datarecipient.cleanup_target_dir()

    def prepare_target_dir(self):
        """Create required subdirectories in each datarecipient's target directory."""
        for datarecipient in self.datarecipients:
            datarecipient.prepare_target_dir()

    def output(self):
        """
        Write rendered config files to disk via all configured datarecipients.

        For each datarecipient: counts existing files, loads the rendered objects,
        cleans and prepares the target directory, then writes new files.
        Directories are cleaned at most once even when multiple datarecipients
        share the same dynamic_dir.

        Side effects:
            - Writes/overwrites files on disk.
            - May revert output via git if safe_output detects too-large delta.
        """
        cleaned_dirs = []
        for datarecipient in self.datarecipients:
            datarecipient.count_before_objects()
            datarecipient.load(None, self.objects)
            if hasattr(datarecipient, 'dynamic_dir') and datarecipient.dynamic_dir not in cleaned_dirs:
                # do not clean a target dir where another datarecipient already wrote it's files
                datarecipient.cleanup_target_dir()
                cleaned_dirs.append(datarecipient.dynamic_dir)
            datarecipient.prepare_target_dir()
            datarecipient.output()

    def read(self):
        """Return the current objects dict (used by tests and introspection)."""
        return self.objects

    def add_class_factory(self, cls, path, factory):
        """
        Register a class factory (mapping of type-names to classes) for the given base class.

        Class factories enable dynamic plugin discovery: each datasource type,
        application type, etc. is resolved at runtime from the classes_path.
        """
        logger.debug("init {} classes ({})".format(cls.__name__, len(factory)))
        path_text = ",".join(path)
        if not hasattr(self, "class_factory"):
            self.class_factory = {}
        if not cls in self.class_factory:
            self.class_factory[cls] = {}
        self.class_factory[cls][path_text] = factory

    def get_class_factory(self, cls, path):
        """Retrieve a previously registered class factory for the given base class and path."""
        path_text = ",".join(path)
        return self.class_factory[cls][path_text]

    def init_vault_class_factories(self):
        """Discover and register all vault plugin classes from classes_path."""
        self.add_class_factory(coshsh.vault.Vault, self.classes_path, coshsh.vault.Vault.init_class_factory(self.classes_path))

    def init_ds_dr_class_factories(self):
        """Discover and register all datasource and datarecipient plugin classes."""
        self.add_class_factory(coshsh.datasource.Datasource, self.classes_path, coshsh.datasource.Datasource.init_class_factory(self.classes_path))
        self.add_class_factory(coshsh.datarecipient.Datarecipient, self.classes_path, coshsh.datarecipient.Datarecipient.init_class_factory(self.classes_path))

    def update_vault_class_factories(self):
        """Refresh the global vault class factory from this recipe's registered copy."""
        coshsh.vault.Vault.update_class_factory(self.get_class_factory(coshsh.vault.Vault, self.classes_path))

    def update_ds_dr_class_factories(self):
        """Refresh the global datasource and datarecipient class factories."""
        coshsh.datasource.Datasource.update_class_factory(self.get_class_factory(coshsh.datasource.Datasource, self.classes_path))
        coshsh.datarecipient.Datarecipient.update_class_factory(self.get_class_factory(coshsh.datarecipient.Datarecipient, self.classes_path))

    def init_item_class_factories(self):
        """Discover and register all application, monitoring-detail, and contact plugin classes."""
        self.add_class_factory(coshsh.application.Application, self.classes_path, coshsh.application.Application.init_class_factory(self.classes_path))
        self.add_class_factory(coshsh.monitoringdetail.MonitoringDetail, self.classes_path, coshsh.monitoringdetail.MonitoringDetail.init_class_factory(self.classes_path))
        self.add_class_factory(coshsh.contact.Contact, self.classes_path, coshsh.contact.Contact.init_class_factory(self.classes_path))

    def update_item_class_factories(self):
        """Refresh the global application, monitoring-detail, and contact class factories."""
        coshsh.application.Application.update_class_factory(self.get_class_factory(coshsh.application.Application, self.classes_path))
        coshsh.monitoringdetail.MonitoringDetail.update_class_factory(self.get_class_factory(coshsh.monitoringdetail.MonitoringDetail, self.classes_path))
        coshsh.contact.Contact.update_class_factory(self.get_class_factory(coshsh.contact.Contact, self.classes_path))

    def add_vault(self, **kwargs):
        """
        Instantiate a vault plugin, read its secrets, and store them for later substitution.

        Unlike add_datasource/add_datarecipient, the vault is immediately opened and
        its secrets are read into self.vault_secrets.  This is because datasource and
        datarecipient config values may contain @VAULT[key] references that must be
        resolved before those adapters are constructed.

        Raises:
            Re-raises any exception from vault.read() after logging it.
        """
        for key in [k for k in kwargs.keys() if isinstance(kwargs[k], str)]:
            kwargs[key] = re.sub('%.*?%', coshsh.util.substenv, kwargs[key])
        newcls = coshsh.vault.Vault.get_class(kwargs)
        if newcls:
            for key in [attr for attr in self.attributes_for_adapters if hasattr(self, attr)]:
                kwargs['recipe_'+key] = getattr(self, key)
            for key, value in self.additional_recipe_fields.items():
                kwargs['recipe_'+key] = value
            vault = newcls(**kwargs)
            self.vaults.append(vault)
            try:
                self.vault_secrets.update(vault.read())
            except Exception as e:
                logger.critical(f"problem with vault {vault.name}: {e}")
                raise e
        else:
            logger.warning("could not find a suitable vault")

    def substsecret(self, match):
        """Regex substitution callback: replace @VAULT[key] with the secret value, or leave unchanged."""
        identifier = match.group(1)
        if identifier in self.vault_secrets:
            return self.vault_secrets[identifier]
        else:
            return match.group(0)

    def add_datasource(self, **kwargs):
        """
        Instantiate a datasource plugin and append it to self.datasources.

        Before instantiation, all string-valued kwargs go through three
        substitution passes:
            1. %ENV_VAR% environment variable expansion
            2. @VAULT[key] secret substitution (requires vaults to be loaded first)
            3. @MAPPING_...[key] config-mapping expansion

        Side effects:
            - Appends the new datasource to self.datasources.
            - Logs a warning if no matching datasource class is found.
        """
        for key in [k for k in kwargs.keys() if isinstance(kwargs[k], str)]:
            kwargs[key] = re.sub('%.*?%', coshsh.util.substenv, kwargs[key])
            # WHY: vault secrets must already be loaded (via add_vault) at this
            # point so that @VAULT[password_key] in datasource params (e.g. a
            # database password) can be resolved before the datasource is constructed.
            kwargs[key] = re.sub(r'@VAULT\[(.*?)\]', self.substsecret, kwargs[key])
            for mapping in kwargs.get("coshsh_config_mappings", {}):
                mapping_keyword_pat = "(@MAPPING_"+mapping.upper()+r"\[(.*?)\])"
                for match in re.findall(mapping_keyword_pat, kwargs[key]):
                    if match[1] in kwargs["coshsh_config_mappings"][mapping]:
                        oldstr = "@MAPPING_"+mapping.upper()+"["+match[1]+"]"
                        newstr = kwargs["coshsh_config_mappings"][mapping][match[1]]
                        kwargs[key] = kwargs[key].replace(oldstr, newstr)
        newcls = coshsh.datasource.Datasource.get_class(kwargs)
        if newcls:
            for key in [attr for attr in self.attributes_for_adapters if hasattr(self, attr)]:
                kwargs['recipe_'+key] = getattr(self, key)
            for key, value in self.additional_recipe_fields.items():
                kwargs['recipe_'+key] = value
            datasource = newcls(**kwargs)
            self.datasources.append(datasource)
        else:
            logger.warning("could not find a suitable datasource")

    def get_datasource(self, name):
        """Return the datasource with the given name, or None if not found."""
        try:
            return [ds for ds in self.datasources if ds.name == name][0]
        except Exception:
            return None

    def add_datarecipient(self, **kwargs):
        """
        Instantiate a datarecipient plugin and append it to self.datarecipients.

        Performs the same three-pass substitution as add_datasource (env, vault, mapping).

        Side effects:
            - Appends the new datarecipient to self.datarecipients.
            - Logs a warning if no matching datarecipient class is found.
        """
        for key in [k for k in kwargs.keys() if isinstance(kwargs[k], str)]:
            kwargs[key] = re.sub('%.*?%', coshsh.util.substenv, kwargs[key])
            kwargs[key] = re.sub(r'@VAULT\[(.*?)\]', self.substsecret, kwargs[key])
            for mapping in kwargs.get("coshsh_config_mappings", {}):
                mapping_keyword_pat = "(@MAPPING_"+mapping.upper()+r"\[(.*?)\])"
                for match in re.findall(mapping_keyword_pat, kwargs[key]):
                    if match[1] in kwargs["coshsh_config_mappings"][mapping]:
                        oldstr = "@MAPPING_"+mapping.upper()+"["+match[1]+"]"
                        newstr = kwargs["coshsh_config_mappings"][mapping][match[1]]
                        kwargs[key] = kwargs[key].replace(oldstr, newstr)
        newcls = coshsh.datarecipient.Datarecipient.get_class(kwargs)
        if newcls:
            for key in [attr for attr in self.attributes_for_adapters if hasattr(self, attr)]:
                kwargs['recipe_'+key] = getattr(self, key)
            datarecipient = newcls(**kwargs)
            self.datarecipients.append(datarecipient)
        else:
            logger.warning("could not find a suitable datarecipient")

    def get_datarecipient(self, name):
        """Return the datarecipient with the given name, or None if not found."""
        try:
            return [dr for dr in self.datarecipients if dr.name == name][0]
        except Exception:
            return None

    def pid_exists(self, pid):
        """Check whether a process with the given PID is currently running (signal 0 probe)."""
        try:
            os.kill(pid, 0)
        except ProcessLookupError as e_oserror:
            # The pid doesn't exist
            return False
        except PermissionError:
            # The pid exists but is not mine
            return False
        else:
            return True

    def pid_protect(self):
        """
        Acquire an exclusive PID-file lock to prevent concurrent coshsh runs on the same recipe.

        WHY pid_protect() exists:
            coshsh reads from datasources, wipes the output directory, then writes
            new config files.  If two coshsh processes for the same recipe ran
            concurrently, they could interleave their cleanup and write phases,
            producing a corrupt or incomplete config directory.  The PID file acts
            as a cooperative advisory lock: if a live process already holds the
            lock, this method raises RecipePidAlreadyRunning instead of proceeding.

        Behaviour:
            - If the PID file exists and contains a live PID: raise RecipePidAlreadyRunning.
            - If the PID file exists but the process is gone: remove the stale file and proceed.
            - If the PID file contains garbage: raise RecipePidGarbage.
            - If the PID file or directory is not writable: raise RecipePidNotWritable.
            - On success: writes the current PID to the file and returns the file path.

        Returns:
            The path to the PID file on success.

        Raises:
            RecipePidAlreadyRunning -- another coshsh instance is active.
            RecipePidNotWritable    -- filesystem permissions prevent locking.
            RecipePidGarbage        -- PID file exists but content is not an integer.
        """
        # WHY: prevents concurrent coshsh runs on the same recipe, which would
        # race on cleanup/write of the output directory and corrupt monitoring config.
        if os.path.exists(self.pid_file):
            if not os.access(self.pid_file, os.W_OK):
                raise RecipePidNotWritable
            try:
                with io.open(self.pid_file) as f:
                    pid = int(f.read().strip())
            except ValueError:
                if os.stat(self.pid_file).st_size == 0 and os.statvfs(self.pid_file).f_bavail > 0:
                    # might be (and was) the result of a full filesystem in the past
                    logger.info('removing empty pidfile %s' % (self.pid_file,))
                    os.remove(self.pid_file)
                raise RecipePidGarbage
            except Exception as e:
                logger.info('some other trouble with the pid file %s' % (self.pid_file,))
                raise RecipePidGarbage
            if not self.pid_exists(pid):
                # The pid doesn't exist, so remove the stale pidfile.
                os.remove(self.pid_file)
                logger.info('removing stale (pid %d) pidfile %s' % (pid, self.pid_file))
            else:
                logger.info('another instance seems to be running (pid %s), exiting' % pid)
                raise RecipePidAlreadyRunning
        else:
            if not os.access(self.pid_dir, os.W_OK):
                raise RecipePidNotWritable
        pid = str(os.getpid())
        try:
            with io.open(self.pid_file, 'w') as f:
                f.write(pid)
        except Exception as e:
            raise RecipePidNotWritable
        else:
            return self.pid_file

    def pid_remove(self):
        """Release the PID-file lock.  Silently ignores errors (e.g. file already gone)."""
        try:
            os.remove(self.pid_file)
        except Exception:
            pass

