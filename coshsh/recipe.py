#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

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
    pass


class RecipePidAlreadyRunning(Exception):
    # found another generator instance
    pass


class RecipePidNotWritable(Exception):
    # pid_dir is not writable
    pass


class RecipePidGarbage(Exception):
    # pid_file contains no integer
    pass


class Recipe(object):

    attributes_for_adapters = ["name", "force", "safe_output", "pid_dir", "pid_file", "templates_dir", "classes_dir", "objects_dir", "max_delta", "max_delta_action", "classes_path", "templates_path", "filter", "git_init"]

    def __del__(self):
        pass
        # sys.path is invisible here, so this will fail
        #self.unset_recipe_sys_path()

    def __init__(self, **kwargs):
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
            
        self.datasources = []
        self.datarecipients = []

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

        self.init_ds_dr_class_factories()
        self.init_item_class_factories()

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
        # because this is allowed: datarecipients = >>>,SIMPLESAMPLE
        self.datarecipient_names = ['datarecipient_coshsh_default' if dr == '>>>' else dr for dr in self.datarecipient_names]
        if 'datarecipient_coshsh_default' in self.datarecipient_names:
            self.add_datarecipient(**dict([('type', 'datarecipient_coshsh_default'), ('name', 'datarecipient_coshsh_default'), ('objects_dir', self.objects_dir), ('max_delta', self.max_delta), ('max_delta_action', self.max_delta_action), ('safe_output', self.safe_output)]))

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
        sys.path[0:0] = self.classes_path

    def unset_recipe_sys_path(self):
        for p in [p for p in self.classes_path if os.path.exists(p) and os.path.isdir(p)]:
            sys.path.pop(0)

    def collect(self):
        data_valid = True
        for ds in self.datasources:
            filter = self.datasource_filters.get(ds.name)
            try:
                ds.open()
                pre_count = dict([(key, len(self.objects[key].keys())) for key in self.objects.keys()])
                pre_detail_count = sum([(len(obj.monitoring_details) if hasattr(obj, 'monitoring_details') else 99) for objs in [self.objects[key].values() for key in self.objects.keys()] for obj in objs], 0)
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
                logger.info("datasource %s is is not current" % ds.name, exc_info=False)
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
        for datarecipient in self.datarecipients:
            datarecipient.count_before_objects()
        self.old_objects = (sum([dr.old_objects[0] for dr in self.datarecipients], 0), sum([dr.old_objects[1] for dr in self.datarecipients], 0))

    def count_after_objects(self):
        for datarecipient in self.datarecipients:
            datarecipient.count_after_objects()
        self.new_objects = (sum(0, [dr.new_objects[0] for dr in self.datarecipients]), sum(0, [dr.new_objects[1] for dr in self.datarecipients]))

    def cleanup_target_dir(self):
        for datarecipient in self.datarecipients:
            datarecipient.cleanup_target_dir()

    def prepare_target_dir(self):
        for datarecipient in self.datarecipients:
            datarecipient.prepare_target_dir()

    def output(self):
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
        return self.objects

    def add_class_factory(self, cls, path, factory):
        logger.debug("init {} classes ({})".format(cls.__name__, len(factory)))
        path_text = ",".join(path)
        if not hasattr(self, "class_factory"):
            self.class_factory = {}
        if not cls in self.class_factory:
            self.class_factory[cls] = {}
        self.class_factory[cls][path_text] = factory

    def get_class_factory(self, cls, path):
        path_text = ",".join(path)
        return self.class_factory[cls][path_text]

    def init_ds_dr_class_factories(self):
        self.add_class_factory(coshsh.datasource.Datasource, self.classes_path, coshsh.datasource.Datasource.init_class_factory(self.classes_path))
        self.add_class_factory(coshsh.datarecipient.Datarecipient, self.classes_path, coshsh.datarecipient.Datarecipient.init_class_factory(self.classes_path))

    def update_ds_dr_class_factories(self):
        coshsh.datasource.Datasource.update_class_factory(self.get_class_factory(coshsh.datasource.Datasource, self.classes_path))
        coshsh.datarecipient.Datarecipient.update_class_factory(self.get_class_factory(coshsh.datarecipient.Datarecipient, self.classes_path))

    def init_item_class_factories(self):
        self.add_class_factory(coshsh.application.Application, self.classes_path, coshsh.application.Application.init_class_factory(self.classes_path))
        self.add_class_factory(coshsh.monitoringdetail.MonitoringDetail, self.classes_path, coshsh.monitoringdetail.MonitoringDetail.init_class_factory(self.classes_path))
        self.add_class_factory(coshsh.contact.Contact, self.classes_path, coshsh.contact.Contact.init_class_factory(self.classes_path))

    def update_item_class_factories(self):
        coshsh.application.Application.update_class_factory(self.get_class_factory(coshsh.application.Application, self.classes_path))
        coshsh.monitoringdetail.MonitoringDetail.update_class_factory(self.get_class_factory(coshsh.monitoringdetail.MonitoringDetail, self.classes_path))
        coshsh.contact.Contact.update_class_factory(self.get_class_factory(coshsh.contact.Contact, self.classes_path))

    def add_datasource(self, **kwargs):
        for key in [k for k in kwargs.keys() if isinstance(kwargs[k], str)]:
            kwargs[key] = re.sub('%.*?%', coshsh.util.substenv, kwargs[key])
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
        try:
            return [ds for ds in self.datasources if ds.name == name][0]
        except Exception:
            return None

    def add_datarecipient(self, **kwargs):
        for key in [k for k in kwargs.keys() if isinstance(kwargs[k], str)]:
            kwargs[key] = re.sub('%.*?%', coshsh.util.substenv, kwargs[key])
        newcls = coshsh.datarecipient.Datarecipient.get_class(kwargs)
        if newcls:
            for key in [attr for attr in self.attributes_for_adapters if hasattr(self, attr)]:
                kwargs['recipe_'+key] = getattr(self, key)
            datarecipient = newcls(**kwargs)
            self.datarecipients.append(datarecipient)
        else:
            logger.warning("could not find a suitable datarecipient")

    def get_datarecipient(self, name):
        try:
            return [dr for dr in self.datarecipients if dr.name == name][0]
        except Exception:
            return None

    def pid_exists(self, pid):
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
        try:
            os.remove(self.pid_file)
        except Exception:
            pass

