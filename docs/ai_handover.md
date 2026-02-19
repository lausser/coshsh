# coshsh Status Quo — AI Agent Reference (February 2026 Baseline)

This document is the single authoritative reference for AI agents working on the coshsh
codebase. It captures the complete state of the project as of February 2026 — the last
version designed, written, and maintained by human contributors.

---

## Table of Contents

- [1. Project Purpose and Use Cases](#1-project-purpose-and-use-cases)
  - [1.1 What coshsh does](#11-what-coshsh-does)
  - [1.2 Core use case: Nagios/Icinga config generation](#12-core-use-case-nagiosicinga-config-generation)
  - [1.3 Use case: OMD integration](#13-use-case-omd-integration)
  - [1.4 Use case: SNMP trap config via check_logfiles](#14-use-case-snmp-trap-config-via-check_logfiles)
  - [1.5 Known deployments and scale](#15-known-deployments-and-scale)
- [2. Architecture Overview](#2-architecture-overview)
  - [2.1 Component diagram](#21-component-diagram)
  - [2.2 The four-phase pipeline](#22-the-four-phase-pipeline)
  - [2.3 Phase dependency chain](#23-phase-dependency-chain)
  - [2.4 The shared objects dictionary](#24-the-shared-objects-dictionary)
- [3. Core Module Reference](#3-core-module-reference)
  - [3.1 generator.py](#31-generatorpy)
  - [3.2 recipe.py](#32-recipepy)
  - [3.3 datasource.py](#33-datasourcepy)
  - [3.4 datarecipient.py](#34-datarecipientpy)
  - [3.5 datainterface.py](#35-datainterfacepy)
  - [3.6 item.py](#36-itempy)
  - [3.7 host.py](#37-hostpy)
  - [3.8 application.py](#38-applicationpy)
  - [3.9 contact.py](#39-contactpy)
  - [3.10 contactgroup.py](#310-contactgrouppy)
  - [3.11 hostgroup.py](#311-hostgrouppy)
  - [3.12 monitoringdetail.py](#312-monitoringdetailpy)
  - [3.13 templaterule.py](#313-templaterulepy)
  - [3.14 vault.py](#314-vaultpy)
  - [3.15 configparser.py](#315-configparserpy)
  - [3.16 jinja2_extensions.py](#316-jinja2_extensionspy)
  - [3.17 dependency.py](#317-dependencypy)
  - [3.18 util.py](#318-utilpy)
- [4. Plugin / Extension System](#4-plugin--extension-system)
  - [4.1 Class factory mechanism](#41-class-factory-mechanism)
  - [4.2 Class path search order and catchall](#42-class-path-search-order-and-catchall)
  - [4.3 Ident function conventions](#43-ident-function-conventions)
  - [4.4 Class file naming prefixes](#44-class-file-naming-prefixes)
  - [4.5 Reversed iteration order](#45-reversed-iteration-order)
  - [4.6 Catchall directories](#46-catchall-directories)
  - [4.7 Hook methods called during assemble](#47-hook-methods-called-during-assemble)
  - [4.8 property_flat and property_attr detail resolution](#48-property_flat-and-property_attr-detail-resolution)
- [5. MonitoringDetail Type Reference](#5-monitoringdetail-type-reference)
  - [5.1 LOGIN](#51-login)
  - [5.2 LOGINSNMPV2](#52-loginsnmpv2)
  - [5.3 LOGINSNMPV3](#53-loginsnmpv3)
  - [5.4 FILESYSTEM](#54-filesystem)
  - [5.5 PORT](#55-port)
  - [5.6 INTERFACE](#56-interface)
  - [5.7 DATASTORE](#57-datastore)
  - [5.8 TABLESPACE](#58-tablespace)
  - [5.9 URL](#59-url)
  - [5.10 TAG](#510-tag)
  - [5.11 ROLE](#511-role)
  - [5.12 DEPTH](#512-depth)
  - [5.13 VOLUME](#513-volume)
  - [5.14 PROCESS](#514-process)
  - [5.15 SOCKET](#515-socket)
  - [5.16 ACCESS](#516-access)
  - [5.17 KEYVALUES](#517-keyvalues)
  - [5.18 NAGIOSCONF](#518-nagiosconf)
  - [5.19 CUSTOM_MACRO](#519-custom_macro)
- [6. INI Configuration File Reference](#6-ini-configuration-file-reference)
  - [6.1 defaults section](#61-defaults-section)
  - [6.2 recipe_NAME section](#62-recipe_name-section)
  - [6.3 datasource_NAME section](#63-datasource_name-section)
  - [6.4 datarecipient_NAME section](#64-datarecipient_name-section)
  - [6.5 vault_NAME section](#65-vault_name-section)
  - [6.6 mapping_NAME section](#66-mapping_name-section)
  - [6.7 prometheus_pushgateway section](#67-prometheus_pushgateway-section)
  - [6.8 Variable substitution](#68-variable-substitution)
  - [6.9 Recipe inheritance via isa](#69-recipe-inheritance-via-isa)
- [7. Jinja2 Template System](#7-jinja2-template-system)
  - [7.1 Template discovery](#71-template-discovery)
  - [7.2 Template caching](#72-template-caching)
  - [7.3 Built-in filters](#73-built-in-filters)
  - [7.4 Built-in tests](#74-built-in-tests)
  - [7.5 Built-in globals](#75-built-in-globals)
  - [7.6 Custom Jinja2 extensions](#76-custom-jinja2-extensions)
  - [7.7 Service filter and NAGIOSCONF](#77-service-filter-and-nagiosconf)
  - [7.8 Template file naming](#78-template-file-naming)
- [8. Output Directory Structure](#8-output-directory-structure)
  - [8.1 dynamic vs static directories](#81-dynamic-vs-static-directories)
  - [8.2 Host configuration files](#82-host-configuration-files)
  - [8.3 Application configuration files](#83-application-configuration-files)
  - [8.4 Group and contact directories](#84-group-and-contact-directories)
  - [8.5 Filename conventions and sanitization](#85-filename-conventions-and-sanitization)
- [9. Delta / Cache Safety Mechanism](#9-delta--cache-safety-mechanism)
  - [9.1 Object counting](#91-object-counting)
  - [9.2 Positive vs negative max_delta](#92-positive-vs-negative-max_delta)
  - [9.3 max_delta_action options](#93-max_delta_action-options)
  - [9.4 safe_output and git reset](#94-safe_output-and-git-reset)
  - [9.5 When to use and when to disable](#95-when-to-use-and-when-to-disable)
- [10. Vault and Secrets Management](#10-vault-and-secrets-management)
  - [10.1 Vault plugin discovery](#101-vault-plugin-discovery)
  - [10.2 @VAULT substitution](#102-vault-substitution)
  - [10.3 %ENV_VAR% substitution](#103-env_var-substitution)
  - [10.4 @MAPPING_NAME substitution](#104-mapping_name-substitution)
  - [10.5 Built-in vault types](#105-built-in-vault-types)
  - [10.6 Recipe-level secret resolution](#106-recipe-level-secret-resolution)
- [11. Hostname Transformations](#11-hostname-transformations)
  - [11.1 strip_domain](#111-strip_domain)
  - [11.2 to_lower / to_upper](#112-to_lower--to_upper)
  - [11.3 append_domain](#113-append_domain)
  - [11.4 resolve_ip](#114-resolve_ip)
  - [11.5 resolve_dns](#115-resolve_dns)
  - [11.6 Configuration and execution order](#116-configuration-and-execution-order)
- [12. Plugin Authoring Guide](#12-plugin-authoring-guide)
  - [12.1 Creating a datasource plugin](#121-creating-a-datasource-plugin)
  - [12.2 Creating an application class plugin](#122-creating-an-application-class-plugin)
  - [12.3 Creating a MonitoringDetail plugin](#123-creating-a-monitoringdetail-plugin)
  - [12.4 Creating a vault plugin](#124-creating-a-vault-plugin)
  - [12.5 Creating a custom Jinja2 extension](#125-creating-a-custom-jinja2-extension)
  - [12.6 Full recipe with vault integration](#126-full-recipe-with-vault-integration)
- [13. Test Infrastructure Guide](#13-test-infrastructure-guide)
  - [13.1 CommonCoshshTest base class](#131-commoncoshshtest-base-class)
  - [13.2 Test recipe fixture layout](#132-test-recipe-fixture-layout)
  - [13.3 Setup and cleanup patterns](#133-setup-and-cleanup-patterns)
  - [13.4 Asserting on generated files](#134-asserting-on-generated-files)
  - [13.5 Testing datasource plugins](#135-testing-datasource-plugins)
  - [13.6 Testing application class plugins](#136-testing-application-class-plugins)
  - [13.7 Running the test suite](#137-running-the-test-suite)
- [14. Edge Cases and Gotchas](#14-edge-cases-and-gotchas)
  - [14.1 Fingerprint collision](#141-fingerprint-collision)
  - [14.2 Ident function priority](#142-ident-function-priority)
  - [14.3 Catchall directory ordering](#143-catchall-directory-ordering)
  - [14.4 DatasourceNotAvailable handling](#144-datasourcenotavailable-handling)
  - [14.5 Jinja2 UndefinedError and render_errors](#145-jinja2-undefinederror-and-render_errors)
  - [14.6 Circular isa inheritance](#146-circular-isa-inheritance)
  - [14.7 Vault backend unreachable](#147-vault-backend-unreachable)
  - [14.8 max_delta with zero baseline](#148-max_delta-with-zero-baseline)
  - [14.9 property_flat gotcha](#149-property_flat-gotcha)
- [15. Prometheus Pushgateway Integration](#15-prometheus-pushgateway-integration)
  - [15.1 Metrics emitted and timing](#151-metrics-emitted-and-timing)
  - [15.2 Configuration](#152-configuration)
  - [15.3 Relationship to recipe execution](#153-relationship-to-recipe-execution)
- [16. OMD Integration](#16-omd-integration)
  - [16.1 What OMD is and where coshsh fits](#161-what-omd-is-and-where-coshsh-fits)
  - [16.2 OMD-specific path conventions](#162-omd-specific-path-conventions)
  - [16.3 Default recipe directory layout](#163-default-recipe-directory-layout)
  - [16.4 Running coshsh-cook inside OMD](#164-running-coshsh-cook-inside-omd)
- [17. SNMP Trap Configuration via check_logfiles](#17-snmp-trap-configuration-via-check_logfiles)
  - [17.1 Use case and context](#171-use-case-and-context)
  - [17.2 Relevant datarecipient and template pattern](#172-relevant-datarecipient-and-template-pattern)
  - [17.3 The testsnmptt test recipe](#173-the-testsnmptt-test-recipe)
- [Appendix A: Quick Reference — All Config Keys](#appendix-a-quick-reference--all-config-keys)
- [Appendix B: Quick Reference — All MonitoringDetail Types](#appendix-b-quick-reference--all-monitoringdetail-types)
- [Appendix C: Class Factory Decision Tree](#appendix-c-class-factory-decision-tree)

---

## 1. Project Purpose and Use Cases

### 1.1 What coshsh does

Coshsh is a framework that transforms inventory data from external datasources into
monitoring configuration files for Nagios, Icinga, Naemon, Shinken, and Prometheus. It is
a *config generator*, not a monitoring engine itself.

A critical design principle: coshsh reads **hosts** and **applications** from its
datasources -- it does NOT read services directly. Nagios service definitions are never
defined in the datasource layer. Instead, services emerge later during the rendering phase
when Jinja2 templates associated with application classes are evaluated. Each application
class declares `template_rules` that point to `.tpl` files, and those template files
contain the `define service { ... }` blocks. This separation means that server
administrators only need to register a hostname, an IP address, and the applications
running on a host; they never need to understand Nagios service definitions, check
commands, or notification options.

### 1.2 Core use case: Nagios/Icinga config generation

The primary use case is reading host and application records from CMDBs, CSV files,
databases, or LDAP directories, and generating complete Nagios-compatible `.cfg` files
via Jinja2 templates.

The workflow is:

1. A **datasource plugin** (Python class placed in `classes_dir`) connects to the
   inventory system and creates `Host` and `Application` objects.
2. Each `Application` is matched to a **class file** (e.g. `os_windows.py`,
   `app_oracle.py`) via the `__mi_ident__` factory function. The class file declares
   which `.tpl` template files apply to that application type.
3. During rendering, the `.tpl` files are evaluated with Jinja2. The host and application
   objects are available as template variables (`{{ host.host_name }}`,
   `{{ application.host_name }}`), and the output is a string containing valid Nagios
   object definitions.
4. The rendered configuration is written to an **output directory** organized per host:
   `<objects_dir>/dynamic/hosts/<host_name>/host.cfg`,
   `<objects_dir>/dynamic/hosts/<host_name>/<app_template>.cfg`, etc.
   Hostgroups, contactgroups, and contacts are written into their own subdirectories.

### 1.3 Use case: OMD integration

Coshsh ships as part of **OMD** (Open Monitoring Distribution,
https://github.com/Consol-Monitoring/omd). When running inside an OMD site, coshsh uses
`%OMD_ROOT%`-based paths for all directory resolution:

- **classes_dir**: `%OMD_ROOT%/etc/coshsh/recipes/<name>/classes` (site-specific),
  with a fallback to `%OMD_ROOT%/share/coshsh/recipes/default/classes` (shipped defaults).
- **templates_dir**: `%OMD_ROOT%/etc/coshsh/recipes/<name>/templates`, with a fallback
  to `%OMD_ROOT%/share/coshsh/recipes/default/templates`.
- **objects_dir**: `%OMD_ROOT%/var/coshsh/configs/<name>`.
- **pid_dir**: `%OMD_ROOT%/tmp/run` (for PID-file-based concurrency protection).
- **log_dir**: `%OMD_ROOT%/var/coshsh`.
- **cookbook config**: typically placed under `~/etc/coshsh/conf.d/<name>.cfg`.

Each OMD site can have multiple recipes, each with its own classes, templates, and output
directory. The `coshsh-cook` command is invoked from the site user context:

```
OMD[mysite]:~$ coshsh-cook --cookbook etc/coshsh/conf.d/myrecipe.cfg --recipe myrecipe
```

### 1.4 Use case: SNMP trap config via check_logfiles

Within OMD, coshsh can also generate configuration for `check_logfiles`, the plugin used
for SNMP trap monitoring. In this use case, coshsh reads trap-related data from
datasources and produces `check_logfiles` configuration files that define which SNMP traps
to watch for and how to translate them into Nagios check results. This enables automated
SNMP trap monitoring setup as part of the same config-generation pipeline that produces
host and service definitions.

Reference: https://omd.consol.de/blog/2017/02/25/snmp-traps-und-omd-teil-1/

### 1.5 Known deployments and scale

Coshsh is used in production at a number of large organizations:

- **City of Munich** (https://bit.ly/2QhNCOJ)
- **BMW** (three-letter car manufacturer based in Munich)
- **Lidl / Kaufland** (https://bit.ly/2L459nH)
- **NetApp** (global storage company -- originally three letters, now four after acquisition)
- A **Chinese car manufacturer** in Shenyang
- An **Austrian crystal company** (Swarovski)
- A **world-wide operating consulting firm**
- A **venerable hanseatic bank**

Performance benchmark: coshsh generates approximately **60,000 services in 10 seconds**,
making it practical for very large monitoring installations where manual configuration
would be impossible.

See also: [Section 6 (INI Configuration File Reference)](#6-ini-configuration-file-reference) for cookbook/recipe config syntax, [Section 12 (Plugin Authoring Guide)](#12-plugin-authoring-guide) for writing datasource and application class plugins, [Section 16 (OMD Integration)](#16-omd-integration) for detailed OMD path conventions.

---

## 2. Architecture Overview

### 2.1 Component diagram

```
                          +-----------+
                          | coshsh-cook|  (CLI entry point)
                          +-----+-----+
                                |
                                v
                          +-----------+
                          | Generator |  (reads cookbook, creates recipes, calls run())
                          +-----+-----+
                                |
                                v
                          +-----------+
                          |  Recipe   |  (central orchestrator: collect/assemble/render/output)
                          +-----+-----+
                                |
             +------------------+------------------+
             |                  |                  |
             v                  v                  v
       +------------+   +---------------+   +-------+
       | Datasource |   | Datarecipient |   | Vault |
       +------------+   +---------------+   +-------+
       (reads hosts &    (writes .cfg files  (resolves
        applications     to objects_dir)      @VAULT[...] secrets)
        from CMDBs,
        CSV, DB, LDAP)

  Recipe also holds the domain model objects:

       +------+   +-------------+   +---------+   +------------------+
       | Host |   | Application |   | Contact |   | MonitoringDetail |
       +------+   +-------------+   +---------+   +------------------+

       +----------+   +--------------+
       | HostGroup|   | ContactGroup |
       +----------+   +--------------+

  Plugin/class file discovery paths:

       classes_dir  ---->  datasource_*.py    (matched via __ds_ident__)
                    ---->  os_*.py, app_*.py  (matched via __mi_ident__)
                    ---->  detail_*.py        (matched via __detail_ident__)
                    ---->  contact_*.py       (matched via __contact_ident__)
                    ---->  datarecipient_*.py (matched via __dr_ident__)
                    ---->  vault_*.py         (matched via __vault_ident__)

       templates_dir --->  host.tpl, *.tpl   (Jinja2 templates for rendering)
```

### 2.2 The four-phase pipeline

The `Generator.run()` method calls four phases on each recipe in sequence. The exact
method names and their responsibilities are:

1. **`recipe.collect()`** -- Iterates over all configured datasources. For each
   datasource, calls `ds.open()`, `ds.read(filter, objects, force)`, and `ds.close()`.
   The datasource's `read()` method creates `Host`, `Application`, `MonitoringDetail`,
   `Contact`, and `ContactGroup` objects and adds them into `recipe.objects` via
   `self.add('hosts', h)`, `self.add('applications', a)`, etc. Returns `True` if all
   datasources were read successfully, `False` if any datasource raised
   `DatasourceNotAvailable`, `DatasourceNotCurrent`, `DatasourceNotReady`, or any other
   exception. If `collect()` returns `False`, the remaining phases are skipped entirely.

2. **`recipe.assemble()`** -- Links the collected objects together. First, it attaches
   `MonitoringDetail` objects from `recipe.objects['details']` to their corresponding
   applications or hosts by matching on `application_fingerprint()`. Then, for each host,
   it calls `host.resolve_monitoring_details()`, `host.create_templates()`,
   `host.create_hostgroups()`, and `host.create_contacts()`. For each application, it
   sets `app.host` to the owning host object, appends the application to
   `host.applications`, calls `app.resolve_monitoring_details()`,
   `app.create_templates()`, `app.create_servicegroups()`, and `app.create_contacts()`.
   Applications that refer to a non-existing host are logged and removed. Finally,
   hostgroup objects are created from the aggregated `host.hostgroups` lists.

3. **`recipe.render()`** -- Applies Jinja2 templates to all objects. Iterates over hosts,
   applications, contactgroups, contacts, hostgroups, and any custom item types in
   `recipe.objects`. For each object, calls `object.render(template_cache, jinja2, recipe)`,
   which loads the `.tpl` files specified in `template_rules`, evaluates them with the
   object as context, and stores the resulting configuration strings in the object's
   `config_files` dict. A `template_cache` dict is shared across all render calls to
   avoid reloading templates. Render errors (e.g. `UndefinedError`) are counted in
   `recipe.render_errors`.

4. **`recipe.output()`** -- Writes rendered configuration to disk via datarecipients.
   For each datarecipient, calls `datarecipient.count_before_objects()` (to count
   existing files for delta checking), `datarecipient.load(None, recipe.objects)` (to
   receive the objects), `datarecipient.cleanup_target_dir()` (to remove stale files from
   the `dynamic` subdirectory), `datarecipient.prepare_target_dir()` (to create directory
   structure), and `datarecipient.output()` (to write `.cfg` files). The default
   datarecipient writes files into `<objects_dir>/dynamic/hosts/<host_name>/`.

### 2.3 Phase dependency chain

The four phases must run in strict sequence because each phase depends on the output of
the previous one:

- **assemble needs collect's output**: The `assemble()` method reads from
  `recipe.objects['hosts']`, `recipe.objects['applications']`, and
  `recipe.objects['details']`. These dicts are populated exclusively during `collect()`.
  If `collect()` has not run (or returned `False`), the objects dicts would be empty and
  there would be nothing to link together.

- **render needs assemble's output**: The `render()` method calls
  `object.render(template_cache, jinja2, recipe)` on each host and application. For
  applications, the template context relies on `app.host` being set (so the template can
  access `{{ application.host.host_name }}`), on monitoring details being resolved (so
  attributes like `application.filesystems` exist), and on `template_rules` being
  initialized via `create_templates()`. All of this linkage happens in `assemble()`. If
  render ran before assemble, applications would not be linked to their hosts, monitoring
  details would not be resolved, and templates would fail or produce incomplete output.

- **output needs render's output**: The `output()` method passes `recipe.objects` to each
  datarecipient, which iterates over the objects and writes their `config_files` dict
  contents to disk. The `config_files` dict on each object is populated during `render()`.
  If output ran before render, every object's `config_files` would be empty and no `.cfg`
  files would be written.

### 2.4 The shared objects dictionary

The `recipe.objects` dict is initialized in `Recipe.__init__()` and serves as the shared
data store across all four phases. Its structure is:

```python
self.objects = {
    'hosts':         {},   # {fingerprint: Host}
    'applications':  {},   # {fingerprint: Application}
    'contacts':      {},   # {fingerprint: Contact}
    'contactgroups': {},   # {fingerprint: ContactGroup}
    'hostgroups':    {},   # {hostgroup_name: HostGroup}  (after assemble; list during assemble)
    'details':       {},   # {fingerprint: MonitoringDetail}
    'commands':      {},   # {fingerprint: object}
    'timeperiods':   {},   # {fingerprint: object}
    'dependencies':  {},   # {fingerprint: object}
    'bps':           {},   # {fingerprint: object}
}
```

Each value is a dict keyed by the object's **fingerprint**. For hosts, the fingerprint is
typically the `host_name`. For applications, it is a composite of
`host_name+name+type`. For contacts, it is the `name`. The fingerprint serves as a
deduplication key -- if a datasource adds the same object twice, the second addition
overwrites the first.

During `collect()`, datasources write into this dict via `self.add(key, object)`. During
`assemble()`, the recipe reads from `objects['hosts']` and `objects['applications']` to
link them and from `objects['details']` to distribute monitoring details. During
`render()`, all objects in the dict have their `config_files` attribute populated. During
`output()`, the entire dict is passed to each datarecipient for file generation.

See also: [Section 3 (Core Module Reference)](#3-core-module-reference) for detailed per-module documentation, [Section 4 (Plugin / Extension System)](#4-plugin--extension-system) for how class files and ident functions are discovered, [Section 7 (Jinja2 Template System)](#7-jinja2-template-system) for template rendering details, [Section 8 (Output Directory Structure)](#8-output-directory-structure) for the file layout produced by datarecipients.

---

## 3. Core Module Reference

### 3.1 generator.py

**Responsibility:** The `Generator` is the top-level orchestrator of the entire coshsh pipeline. It parses one or more INI-format cookbook files, instantiates `Recipe` objects with their associated datasources, datarecipients, and vaults, and then drives the four-phase pipeline (collect, assemble, render, output) for each recipe. It also manages optional Prometheus Pushgateway integration for emitting metrics after each recipe run. The `Generator` does NOT contain any data-model logic, template rendering, or file-writing code -- those responsibilities belong to `Recipe`, the item classes, and the datarecipients respectively.

**Public classes:**

- `Generator` -- Top-level orchestrator that reads cookbook configuration files, creates recipes, and runs the pipeline for each recipe.

**Key methods:**

- `__init__(self)`
  - Initializes the generator with an empty ordered dictionary of recipes (`self.recipes`, an `odict` from `coshsh.util`) and a default log level of `"info"`.
  - No parameters. No preconditions.

- `set_default_log_level(self, default_log_level)`
  - Sets `self.default_log_level` to the given string (e.g. `"info"` or `"debug"`).
  - Called before `read_cookbook()` to influence logging setup.

- `add_recipe(self, *args, **kwargs)`
  - Creates a `coshsh.recipe.Recipe` instance from `**kwargs` and stores it in `self.recipes[kwargs["name"]]`.
  - If recipe creation raises any exception, logs the error and silently continues (the recipe is not added).
  - Precondition: `kwargs` must include a `"name"` key.

- `get_recipe(self, name)`
  - Returns the `Recipe` object for the given name, or `None` if not found.

- `add_pushgateway(self, *args, **kwargs)`
  - Configures Prometheus Pushgateway settings by storing `self.pg_job`, `self.pg_address`, `self.pg_username`, and `self.pg_password` from kwargs.
  - Defaults: job=`"coshsh"`, address=`"127.0.0.1:9091"`, username/password=`None`.

- `run(self)`
  - Iterates over all recipes in `self.recipes`. For each recipe:
    1. Calls `recipe.update_item_class_factories()` to refresh the class factory lookup tables.
    2. Switches logging to the recipe's log file via `coshsh.util.switch_logging()`.
    3. Calls `recipe.pid_protect()` to acquire a PID lock (prevents concurrent runs of the same recipe).
    4. If `recipe.collect()` returns `True`, proceeds to `recipe.assemble()`, `recipe.render()`, and `recipe.output()`.
    5. If Prometheus is configured, pushes metrics (`coshsh_recipe_last_generated`, `coshsh_recipe_number_of_objects`, `coshsh_recipe_last_duration`, `coshsh_recipe_render_errors`, `coshsh_recipe_last_success`) via `pushadd_to_gateway` with grouping keys `hostname`, `username`, `cookbook`, and `recipe`.
    6. Calls `recipe.pid_remove()` to release the PID lock.
  - Exceptions handled: `RecipePidAlreadyRunning` (logged at info, recipe skipped), `RecipePidNotWritable` (logged at error, recipe skipped), `RecipePidGarbage` (logged at error, recipe skipped). Any other exception causes the recipe to be skipped with a generic error log.
  - Side effect: If `self.default_log_level == "debug"`, calls `CoshshDatainterface.dump_classes_usage()` after each recipe. Calls `coshsh.util.restore_logging()` at the end of each recipe iteration.

- `read_cookbook(self, cookbook_files, default_recipe, force, safe_output)`
  - Parses one or more INI cookbook files using `coshsh.configparser.CoshshConfigParser`.
  - Extracts sections by prefix: `vault_*` into vault configs, `mapping_*` into config mappings, `datarecipient_*` into datarecipient configs, `datasource_*` into datasource configs, `recipe_*` into recipe configs.
  - Determines which recipes to run: either from `default_recipe` (comma-separated string), or from the `defaults.recipes` config key, or all non-underscore-prefixed recipe sections.
  - Supports regex-based recipe name matching: if a recipe name does not directly match a section, it tries matching against section names as patterns (longest match first).
  - Sets up logging based on `defaults.log_dir` (fallback: `OMD_ROOT/var/coshsh` or system temp dir), `defaults.log_level`, and `defaults.backup_count` (default: 2).
  - For each recipe: calls `self.add_recipe()`, then adds vaults (via `recipe.add_vault()`), datasources (via `recipe.add_datasource()`), and datarecipients (via `recipe.add_datarecipient()`).
  - If any vault fails to initialize, the entire recipe is removed from `self.recipes` and processing continues with the next recipe.
  - If a `prometheus_pushgateway` section exists with an `address` key, calls `self.add_pushgateway()`.
  - Side effects: stores `self.cookbook_files` as a `___`-joined string of cookbook basenames. Stores `self.log_dir`. Sets environment variables `RECIPE_NAME`, `RECIPE_NAME1`, `RECIPE_NAME2`, etc. (done inside `Recipe.__init__`).
  - Precondition: at least one valid cookbook file must be provided; exits with `sys.exit(2)` if no sections are parsed.

**Usage example:**

The `coshsh-cook` CLI entry point (`bin/coshsh-cook`) drives the full pipeline:

```python
from coshsh.generator import Generator

generator = Generator()
generator.set_default_log_level("info")  # or "debug"
generator.read_cookbook(["cookbook.cfg"], default_recipe=None, force=False, safe_output=False)
generator.run()
```

See also: [3.2 recipe.py](#32-recipepy), [6. INI Configuration File Reference](#6-ini-configuration-file-reference), [15. Prometheus Pushgateway Integration](#15-prometheus-pushgateway-integration)

---

### 3.2 recipe.py

**Responsibility:** The `Recipe` class is the central unit of work in coshsh. It owns the shared `objects` dictionary (hosts, applications, contacts, hostgroups, etc.), manages the Jinja2 template environment, orchestrates class factory initialization for all plugin types, and drives the four pipeline phases: `collect()`, `assemble()`, `render()`, and `output()`. It also handles PID-file-based locking to prevent concurrent runs, datasource filter parsing, and vault secret resolution for datasource/datarecipient configuration values. The `Recipe` does NOT parse cookbook files (that is the Generator's job) and does NOT implement the actual data reading or file writing (those are the responsibilities of datasource and datarecipient plugins).

**Public classes:**

- `EmptyObject` -- A bare `object` subclass used as a namespace container for the Jinja2 `loader` and `env` attributes.
- `RecipePidAlreadyRunning(Exception)` -- Raised when another instance of the same recipe is already running (PID file exists with a live process).
- `RecipePidNotWritable(Exception)` -- Raised when the PID directory or PID file is not writable.
- `RecipePidGarbage(Exception)` -- Raised when the PID file contains non-integer content.
- `Recipe` -- The main pipeline orchestrator for a single recipe configuration.

**Key methods:**

- `__init__(self, **kwargs)`
  - Required kwarg: `name` (string).
  - Notable kwargs: `force`, `safe_output`, `pid_dir`, `templates_dir`, `classes_dir`, `objects_dir`, `datasources` (comma-separated names), `datarecipients` (comma-separated names; `>>>` is an alias for `datarecipient_coshsh_default`), `vaults` (comma-separated names), `max_delta` (string like `"10:20"` or `"5"`, parsed to a tuple of two ints), `max_delta_action`, `filter`, `my_jinja2_extensions`, `git_init` (default `"yes"`; set to `"no"` to disable), `log_file`, `log_dir`, `backup_count`.
  - Performs `%ENV%` substitution via `coshsh.util.substenv` and `@MAPPING_NAME[key]` substitution on all string kwargs.
  - Sets `env_*` kwargs as uppercase environment variables (prefix stripped).
  - Stores any kwargs not in `attributes_for_adapters` into `self.additional_recipe_fields`.
  - Builds `self.classes_path`: starts with the default path (`OMD_ROOT/share/coshsh/recipes/default/classes` or `../recipes/default/classes`), then prepends directories from `classes_dir` (comma-separated), placing directories named `catchall` at the end.
  - Builds `self.templates_path` with the same logic using `templates_dir`.
  - Calls `self.set_recipe_sys_path()` to prepend `classes_path` to `sys.path`.
  - Initializes the Jinja2 environment with `FileSystemLoader(self.templates_path)` and the `jinja2.ext.do` extension. Registers built-in filters: `re_sub`, `re_escape`, `service`, `host`, `contact`, `custom_macros`, `rfc3986`, `neighbor_applications`. Registers the test `re_match` and the global `environ`. Loads custom extensions from `my_jinja2_extensions` if specified (functions prefixed `is_` become tests, `filter_` become filters, `global_` become globals).
  - Initializes `self.objects` with keys: `hosts`, `hostgroups`, `applications`, `details`, `contacts`, `contactgroups`, `commands`, `timeperiods`, `dependencies`, `bps` -- all empty dicts.
  - Calls `self.init_vault_class_factories()`, `self.init_ds_dr_class_factories()`, and `self.init_item_class_factories()`.
  - Parses `self.filter` for per-datasource filter expressions of the form `datasource_name(filter_expression)`, supporting regex patterns for datasource name matching. Results stored in `self.datasource_filters`.
  - If `objects_dir` is set but no explicit `datarecipients`, creates a default `datarecipient_coshsh_default`.
  - Side effects: sets environment variables `RECIPE_NAME`, `RECIPE_NAME1`, `RECIPE_NAME2`, etc. Modifies `sys.path`.

- `collect(self)`
  - Iterates over `self.datasources`. For each: calls `ds.open()`, `ds.read(filter=..., objects=self.objects, force=self.force)`, `ds.close()`.
  - Counts objects before and after each datasource read and logs the differences.
  - Returns `True` if all datasources succeeded. Returns `False` and aborts the collection phase if any datasource raises `DatasourceNotCurrent`, `DatasourceNotReady`, `DatasourceNotAvailable`, or any other exception.
  - Side effect: populates `self.objects` with data from all datasources.

- `assemble(self)`
  - Attaches `MonitoringDetail` objects from `self.objects['details']` to their parent applications or hosts by matching on `detail.application_fingerprint()`. Generic details (fingerprint starting with `*`) are distributed: `*` goes to all hosts, `*+type` goes to all matching applications.
  - For each host: calls `host.resolve_monitoring_details()`, sorts list/tuple attributes, then calls `host.create_templates()`, `host.create_hostgroups()`, `host.create_contacts()`, and sets `host.applications = []`.
  - For each application: links to its host via `self.objects['hosts'][app.host_name]`, appends to `host.applications`, calls `app.resolve_monitoring_details()`, sorts list/tuple attributes, `app.create_templates()`, `app.create_servicegroups()`, `app.create_contacts()`. Orphaned applications (referencing non-existent hosts) are logged and removed from `self.objects['applications']`.
  - Builds hostgroup objects from aggregated `host.hostgroups` lists and calls `create_templates()` and `create_contacts()` on each.
  - Returns `True`.

- `render(self)`
  - Iterates over hosts, applications, contactgroups, contacts, hostgroups, and any other custom object types in `self.objects` (excluding `details`). Calls `item.render(template_cache, self.jinja2, self)` on each.
  - Accumulates render errors in `self.render_errors` (integer count).
  - Uses a shared `template_cache` dictionary to avoid reloading Jinja2 templates.
  - For custom object types: only renders items whose `config_files` attribute is falsy (not already populated by a datasource).
  - Side effect: populates each item's `config_files` dictionary with rendered output.

- `output(self)`
  - Iterates over `self.datarecipients`. For each: calls `count_before_objects()`, `load(None, self.objects)`, `cleanup_target_dir()` (only once per unique `dynamic_dir` to prevent one datarecipient from cleaning another's output), `prepare_target_dir()`, and `output()`.
  - Side effect: writes configuration files to the filesystem via the datarecipient plugins.

- `add_vault(self, **kwargs)`
  - Performs `%ENV%` substitution on string kwargs. Uses `coshsh.vault.Vault.get_class(kwargs)` to find a matching `Vault` subclass. Instantiates it (passing recipe attributes as `recipe_*` kwargs and `additional_recipe_fields`), appends to `self.vaults`, and calls `vault.read()` to populate `self.vault_secrets`.
  - Exception: re-raises any exception from `vault.read()` after logging it as critical.

- `add_datasource(self, **kwargs)`
  - Performs `%ENV%`, `@VAULT[...]` (via `self.substsecret`), and `@MAPPING_NAME[...]` substitution on string kwargs.
  - Uses `Datasource.get_class(kwargs)` to find the matching datasource class, instantiates it (passing recipe attributes as `recipe_*` kwargs), and appends to `self.datasources`.
  - Logs a warning if no suitable class is found.

- `add_datarecipient(self, **kwargs)`
  - Same substitution and class-factory lookup pattern as `add_datasource`, but for `Datarecipient` subclasses. Appends to `self.datarecipients`.
  - Logs a warning if no suitable class is found.

- `get_datasource(self, name)` / `get_datarecipient(self, name)`
  - Returns the datasource/datarecipient object with the given name from `self.datasources`/`self.datarecipients`, or `None` if not found.

- `pid_protect(self)`
  - Checks for an existing PID file. If the file exists and the process is alive, raises `RecipePidAlreadyRunning`. If the file contains garbage, raises `RecipePidGarbage` (handles empty files from full-filesystem scenarios). If the PID directory is not writable, raises `RecipePidNotWritable`. Otherwise writes the current PID and returns the PID file path.
  - Side effect: creates/removes PID files in `self.pid_dir`. PID file name is `coshsh.pid.<sanitized_recipe_name>`.

- `pid_remove(self)`
  - Removes the PID file. Silently ignores errors.

- `pid_exists(self, pid)`
  - Checks whether a process with the given PID exists by calling `os.kill(pid, 0)`. Returns `True` if the process exists, `False` if it does not exist or is not owned by the current user.

- `init_vault_class_factories(self)` / `init_ds_dr_class_factories(self)` / `init_item_class_factories(self)`
  - Initialize the class factory lookup tables for `Vault`, `Datasource`/`Datarecipient`, and `Application`/`MonitoringDetail`/`Contact` respectively by calling each class's `init_class_factory(self.classes_path)`.
  - Stores results via `self.add_class_factory()`.

- `update_item_class_factories(self)`
  - Refreshes the class-level `class_factory` for `Application`, `MonitoringDetail`, and `Contact` from the stored per-recipe factory data. Called by `Generator.run()` before each recipe execution.

- `add_class_factory(self, cls, path, factory)` / `get_class_factory(self, cls, path)`
  - Internal methods for storing/retrieving class factory lists, keyed by class and comma-joined path string, in `self.class_factory` (a nested dict).

- `set_recipe_sys_path(self)` / `unset_recipe_sys_path(self)`
  - Prepends/removes `self.classes_path` entries to/from `sys.path[0:0]` so that plugin modules in class directories can be imported.

- `substsecret(self, match)`
  - Regex substitution callback for `re.sub`. Replaces `@VAULT[identifier]` with the corresponding value from `self.vault_secrets`, or returns the original match string if the identifier is not found.

- `count_before_objects(self)` / `count_after_objects(self)`
  - Delegates to each datarecipient's `count_before_objects()` / `count_after_objects()` and sums the results into `self.old_objects` / `self.new_objects` (tuples of `(hosts_count, apps_count)`).

- `cleanup_target_dir(self)` / `prepare_target_dir(self)`
  - Delegates to each datarecipient's corresponding method.

- `read(self)`
  - Returns `self.objects`. A convenience accessor.

**Class attribute:**

- `attributes_for_adapters` -- List of attribute names that are forwarded to datasources, datarecipients, and vaults as `recipe_*` prefixed parameters: `["name", "force", "safe_output", "pid_dir", "pid_file", "templates_dir", "classes_dir", "objects_dir", "max_delta", "max_delta_action", "classes_path", "templates_path", "filter", "git_init"]`.

**Usage example:**

Recipes are not typically instantiated directly. The `Generator` creates them via `add_recipe()` during `read_cookbook()`:

```python
generator.add_recipe(name="myrecipe", datasources="mydb", datarecipients=">>>",
                     objects_dir="/tmp/coshsh-output", classes_dir="/opt/classes",
                     templates_dir="/opt/templates")
```

Once created, `Generator.run()` calls the pipeline:

```python
recipe.update_item_class_factories()
if recipe.pid_protect():
    if recipe.collect():
        recipe.assemble()
        recipe.render()
        recipe.output()
    recipe.pid_remove()
```

See also: [3.1 generator.py](#31-generatorpy), [3.3 datasource.py](#33-datasourcepy), [3.4 datarecipient.py](#34-datarecipientpy), [4. Plugin / Extension System](#4-plugin--extension-system), [7. Jinja2 Template System](#7-jinja2-template-system)

---

### 3.3 datasource.py

**Responsibility:** The `Datasource` base class defines the interface that all datasource plugins must implement. It provides the `open()` / `read()` / `close()` lifecycle methods, a local `objects` dictionary for staging data, helper methods (`add`, `get`, `getall`, `find`) for managing objects within the datasource, and hostname transformation logic (`transform_hostname`). It also handles automatic "re-blessing" -- if the base `Datasource` class is instantiated directly, it uses the class factory to find the correct subclass and replaces its own `__class__`. The `Datasource` does NOT write output files or manage templates -- it only reads external data and populates the shared objects dictionary.

**Public classes:**

- `DatasourceNotImplemented(Exception)` -- Raised when no matching datasource subclass is found in the class factory.
- `DatasourceNotReady(Exception)` -- Raised when the datasource is temporarily busy (e.g., being updated).
- `DatasourceNotCurrent(Exception)` -- Raised when the datasource data is stale and should not be used.
- `DatasourceNotAvailable(Exception)` -- Raised when the datasource cannot be reached.
- `DatasourceCorrupt(Exception)` -- Raised when the datasource data is corrupt.
- `Datasource(CoshshDatainterface)` -- Base class for all datasource plugins. Inherits from `coshsh.datainterface.CoshshDatainterface`.

**Class attributes:**

- `my_type = 'datasource'` -- Used by `CoshshDatainterface` for logging.
- `class_file_prefixes = ["datasource"]` -- Files matching this prefix are scanned for the ident function.
- `class_file_ident_function = "__ds_ident__"` -- The module-level function name that the class factory looks for in plugin files.
- `class_factory = []` -- Shared class-level list populated by `init_class_factory`.

**Key methods:**

- `__init__(self, **params)`
  - If called on the base `Datasource` class (i.e. `self.__class__ == Datasource`), performs re-blessing: calls `self.__class__.get_class(params)` to find a subclass, reassigns `self.__class__`, and re-invokes `self.__init__(**params)`. Raises `DatasourceNotImplemented` if no matching class is found.
  - If called on a subclass: sets `self.name` from `params["name"]`, initializes `self.hostname_transform_ops` from the `hostname_transform` param (comma-separated list of operation strings, stripped of whitespace), and initializes `self.objects = {}`.
  - Copies all `recipe_*` prefixed params as attributes on `self` (e.g. `self.recipe_name`, `self.recipe_force`) and makes short aliases available in `params` (without the `recipe_` prefix) if they do not already exist.
  - Performs `%ENV%` substitution on all string params via `coshsh.util.substenv`.

- `open(self, **kwargs)`
  - No-op in the base class. Subclasses override to establish connections (e.g., database connections, file handles).

- `read(self, **kwargs)`
  - No-op in the base class. Subclasses override to read data and populate the shared `objects` dictionary. Expected kwargs in practice: `filter` (optional string), `objects` (the recipe's shared objects dict), `force` (boolean).

- `close(self)`
  - No-op in the base class. Subclasses override to release resources.

- `add(self, objtype, obj)`
  - Adds `obj` to `self.objects[objtype]` keyed by `obj.fingerprint()`. Creates the sub-dictionary for `objtype` if it does not yet exist.
  - If `objtype` is `'applications'` and the corresponding host already exists in `self.objects['hosts']` (looked up by `obj.host_name`), sets `obj.host` to the host object.
  - Side effect: calls `obj.record_in_chronicle()` with a message identifying the datasource.

- `get(self, objtype, fingerprint)`
  - Returns the object for the given type and fingerprint, or `None` if not found.

- `getall(self, objtype)`
  - Returns a list of all objects of the given type, or an empty list if the type does not exist in `self.objects`.

- `find(self, objtype, fingerprint)`
  - Returns `True` if `objtype` exists in `self.objects` and `fingerprint` is a key within it; `False` otherwise.

- `transform_hostname(self, hostname)`
  - Applies the transformation operations listed in `self.hostname_transform_ops` to the given hostname string, in order. Supported operations:
    - `strip_domain` -- Removes domain part (splits on `.` and takes the first element). Skips IP addresses (detected via `socket.inet_aton`).
    - `to_lower` -- Converts to lowercase.
    - `to_upper` -- Converts to uppercase.
    - `append_domain` -- Resolves to FQDN via `socket.getfqdn()`.
    - `resolve_ip` -- If the hostname is an IP address, reverse-resolves it to a hostname via `socket.gethostbyaddr()`.
    - `resolve_dns` -- Resolves to FQDN via `socket.getfqdn()`.
  - Logs a warning for unknown operations and for resolution failures (does not raise).
  - Returns the transformed hostname string.

**Usage example:**

Datasource plugins are instantiated by `Recipe.add_datasource()`, which uses the class factory. During `Recipe.collect()`, each datasource is called:

```python
ds.open()
ds.read(filter=filter, objects=self.objects, force=self.force)
ds.close()
```

A minimal datasource plugin file would define:

```python
import coshsh
from coshsh.datasource import Datasource

def __ds_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "mydatasource"):
        return MyDatasource

class MyDatasource(Datasource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # custom initialization

    def open(self):
        pass  # establish connection

    def read(self, **kwargs):
        objects = kwargs.get("objects", {})
        # create Host/Application objects and add to objects dict

    def close(self):
        pass  # release resources
```

See also: [3.5 datainterface.py](#35-datainterfacepy), [3.2 recipe.py](#32-recipepy), [4. Plugin / Extension System](#4-plugin--extension-system), [11. Hostname Transformations](#11-hostname-transformations), [12.1 Creating a datasource plugin](#121-creating-a-datasource-plugin)

---

### 3.4 datarecipient.py

**Responsibility:** The `Datarecipient` base class defines the interface for all output plugins that write generated configuration to the filesystem or other targets. It provides the lifecycle methods `load()`, `output()`, `prepare_target_dir()`, and `cleanup_target_dir()`, as well as delta-safety logic (`count_objects`, `count_before_objects`, `count_after_objects`, `too_much_delta`) that compares the number of hosts and applications before and after a generation run to prevent accidental mass deletion of configuration. It also provides `item_write_config()` for writing an item's rendered config files to disk, and `run_git_init()` for initializing a git repository in the output directory. The `Datarecipient` does NOT read data from external sources or perform template rendering -- it only handles the final output stage.

**Public classes:**

- `DatarecipientNotImplemented(Exception)` -- Raised when no matching datarecipient subclass is found.
- `DatarecipientNotReady(Exception)` -- Raised when the datarecipient target is temporarily busy.
- `DatarecipientNotCurrent(Exception)` -- Raised when the datarecipient target is stale.
- `DatarecipientNotAvailable(Exception)` -- Raised when the datarecipient target cannot be reached.
- `DatarecipientCorrupt(Exception)` -- Raised when the datarecipient target is in a corrupt state.
- `Datarecipient(CoshshDatainterface)` -- Base class for all datarecipient plugins. Inherits from `coshsh.datainterface.CoshshDatainterface`.

**Class attributes:**

- `my_type = 'datarecipient'`
- `class_file_prefixes = ["datarecipient"]` -- Plugin files must start with this prefix.
- `class_file_ident_function = "__dr_ident__"` -- The module-level function name the class factory scans for.
- `class_factory = []`

**Key methods:**

- `__init__(self, **params)`
  - Same re-blessing pattern as `Datasource.__init__`: if called on the base `Datarecipient` class (`self.__class__ == Datarecipient`), looks up the correct subclass via `self.__class__.get_class(params)`, reassigns `self.__class__`, and re-invokes `self.__init__(**params)`. Raises `DatarecipientNotImplemented` if no class matches.
  - If called on a subclass: sets `self.name` from `params["name"]` and initializes `self.objects = {}`.
  - Copies `recipe_*` prefixed params as attributes (and creates short aliases in `params`) and performs `%ENV%` substitution on all string params.

- `load(self, filter=None, objects={})`
  - Stores the given `objects` dictionary as `self.objects`. This is how the recipe hands the shared objects dictionary to the datarecipient before the output phase.
  - Logs the operation at info level.

- `get(self, objtype, fingerprint)`
  - Returns the object for the given type and fingerprint, or the string `'i do not exist. no. no!'` if not found (legacy behavior, differs from `Datasource.get` which returns `None`).

- `getall(self, objtype)`
  - Returns a view of all objects of the given type, or an empty list.

- `find(self, objtype, fingerprint)`
  - Returns `True` if the object exists, `False` otherwise.

- `item_write_config(self, obj, dynamic_dir, objtype, want_tool=None)`
  - Writes the rendered configuration files of `obj` to the filesystem. Creates `dynamic_dir/objtype/` if it does not exist (using `os.makedirs`).
  - Iterates over `obj.config_files[tool][file]` and writes each file's content to `dynamic_dir/objtype/<sanitized_filename>` using `coshsh.util.sanitize_filename()`.
  - If `want_tool` is specified, only files for that specific tool are written; otherwise all tools are written.

- `output(self, filter=None, want_tool=None)`
  - No-op in the base class. Subclasses override to iterate over `self.objects` and call `item_write_config()` for each relevant object type.

- `count_objects(self)`
  - Counts the number of host subdirectories and non-empty application config files (files other than `host.cfg` with non-zero size) under `self.dynamic_dir/hosts/`.
  - Returns a tuple `(host_count, app_count)`. Returns `(0, 0)` on any error (e.g. directory does not exist).

- `count_before_objects(self)` / `count_after_objects(self)`
  - Calls `self.count_objects()` and stores the result in `self.old_objects` / `self.new_objects` respectively.

- `too_much_delta(self)`
  - Computes percentage change for hosts (`self.delta_hosts`) and applications (`self.delta_services`) between `self.old_objects` and `self.new_objects`.
  - If `self.max_delta` is falsy (empty tuple or `None`), always returns `False` (no delta check).
  - For negative `max_delta` values: only a *decrease* exceeding the threshold triggers `True` (increase of any size is accepted). For non-negative values: any change (increase or decrease) whose absolute value exceeds the threshold triggers `True`.
  - Division by zero (going from 0 to N objects) sets delta to 0 (accepted as an initial increase).
  - Returns `True` if delta exceeds threshold, `False` otherwise.

- `prepare_target_dir(self)` / `cleanup_target_dir(self)`
  - No-ops in the base class. Subclasses override to create directory structures and clean up old output.

- `run_git_init(self, path)`
  - Initializes a git repository in the given path by running `git init .`, creating a random temporary file, committing it (`initial dummy-commit add`), then removing it and committing again (`initial dummy-commit rm`). This establishes a baseline for `git reset --hard` safety.
  - Side effects: temporarily changes the working directory via `os.chdir`, runs shell commands via `subprocess.Popen`.

**Usage example:**

Datarecipients are instantiated by `Recipe.add_datarecipient()`. During `Recipe.output()`, each datarecipient is called:

```python
datarecipient.count_before_objects()
datarecipient.load(None, self.objects)
datarecipient.cleanup_target_dir()
datarecipient.prepare_target_dir()
datarecipient.output()
```

The built-in `DatarecipientCoshshDefault` (in `recipes/default/classes/datarecipient_coshsh_default.py`) writes hosts, applications, hostgroups, contactgroups, and contacts to the `dynamic_dir`, performs git commit/push when a `.git` directory exists, and executes delta-safety checks (including `git reset --hard` when `safe_output` is enabled and delta exceeds `max_delta`).

See also: [3.5 datainterface.py](#35-datainterfacepy), [3.2 recipe.py](#32-recipepy), [9. Delta / Cache Safety Mechanism](#9-delta--cache-safety-mechanism), [4. Plugin / Extension System](#4-plugin--extension-system)

---

### 3.5 datainterface.py

**Responsibility:** The `CoshshDatainterface` class is the abstract base class and class-factory engine shared by `Datasource`, `Datarecipient`, `Vault`, `Application`, `MonitoringDetail`, and `Contact`. It provides the generic mechanism for discovering plugin files on the classes path, loading their ident functions, and resolving a parameter dictionary to the correct subclass at runtime. It does NOT contain any domain-specific logic for reading data, writing output, or modeling monitoring objects -- those are the responsibility of its subclasses.

**Public classes:**

- `CoshshDatainterface` -- Base class providing the class factory mechanism for all plugin-based types in coshsh.

**Class attributes:**

- `class_factory = []` -- List of `[path, module, ident_function]` triples. Populated by `init_class_factory()` and shared at the class level by each subclass independently.
- `class_file_prefixes = []` -- Subclasses set this to control which `.py` files are scanned (e.g. `["datasource"]`, `["datarecipient"]`, `["application"]`).
- `class_file_ident_function = ""` -- Subclasses set this to the name of the module-level function to look for (e.g. `"__ds_ident__"`, `"__dr_ident__"`, `"__mi_ident__"`).
- `my_type = ""` -- A human-readable type label used in log messages (e.g. `"datasource"`, `"datarecipient"`).
- `usage_numbers = {}` -- Class-level dictionary tracking how many times each class was resolved by `get_class()`. Keyed by `"path___classname"`.

**Key methods:**

- `init_class_factory(cls, classpath)` (classmethod)
  - Scans the given `classpath` (list of directory paths) in **reversed** order (so the first directory in the path is processed last, giving it highest priority in the final reversed iteration by `get_class`).
  - In each directory, finds `.py` files whose names match `cls.class_file_prefixes` (either exact match or starts-with). Files within each directory are sorted in **reverse** alphabetical order.
  - For each matching file: loads the module via `importlib.util.spec_from_file_location()` and `spec.loader.exec_module()`, then inspects it with `inspect.getmembers(toplevel, inspect.isfunction)` for a function matching `cls.class_file_ident_function`.
  - If found, appends `[absolute_path, module_filename, ident_function]` to the factory list.
  - Calls `cls.update_class_factory(class_factory)` to set the class-level `class_factory`.
  - Returns the factory list.
  - Exceptions: logs critical errors for modules that fail to load but continues processing remaining modules.

- `update_class_factory(cls, class_factory)` (classmethod)
  - Sets `cls.class_factory = class_factory`. Called by `init_class_factory` and also called separately by `Recipe.update_item_class_factories()` to refresh factories before a run.

- `get_class(cls, params={})` (classmethod)
  - Iterates over `cls.class_factory` in **reversed** order. For each `[path, module, class_func]` entry, calls `class_func(params)`.
  - If the ident function returns a class (truthy value), increments `cls.usage_numbers` for that class (keyed as `"path___classname"`) and returns the class.
  - If no ident function matches, logs a debug message and returns `None`.
  - The reversed iteration combined with the reversed loading order means that classes from directories **earlier** in the `classes_path` (higher priority, user-provided) take precedence over default/catchall classes.
  - Exceptions from individual ident functions are caught and printed but do not stop the search.

- `dump_classes_usage(cls)` (classmethod)
  - Prints a summary table of all classes resolved by `get_class()` with their usage counts, sorted ascending by count. Called when running in debug mode (`Generator.run()` calls this if `self.default_log_level == "debug"`).

**Usage example:**

The class factory is typically used indirectly through `Recipe` methods. The internal flow when a recipe adds a datasource:

```python
# During Recipe.__init__() -> init_ds_dr_class_factories():
factory = coshsh.datasource.Datasource.init_class_factory(self.classes_path)
# factory is a list like:
# [["/path/to/datasource_csv.py", "datasource_csv.py", <function __ds_ident__>], ...]

# During Recipe.add_datasource():
newcls = coshsh.datasource.Datasource.get_class({"type": "csv", "name": "myds", ...})
# get_class iterates reversed(factory), calling each __ds_ident__(params).
# The first ident function that returns a class wins.
# newcls is now e.g. DatasourceCsv
datasource_instance = newcls(**kwargs)
```

Direct use of the class factory for custom plugin types follows the same pattern: define `class_file_prefixes`, `class_file_ident_function`, and `my_type` on a subclass of `CoshshDatainterface`, then call `init_class_factory()` with the classes path.

See also: [3.3 datasource.py](#33-datasourcepy), [3.4 datarecipient.py](#34-datarecipientpy), [4. Plugin / Extension System](#4-plugin--extension-system), [4.1 Class factory mechanism](#41-class-factory-mechanism), [4.5 Reversed iteration order](#45-reversed-iteration-order)

### 3.6 item.py

**Responsibility.** `item.py` is the abstract base class for every monitorable object in coshsh (hosts, applications, contacts, contact groups, host groups). It provides the shared mechanics that all objects need: setting attributes from a params dict, managing `monitoring_details`, rendering Jinja2 templates into config file content, and converting list-type attributes between their Python (list) and Nagios-serialized (comma-separated string) forms. It does NOT contain any logic for loading plugin classes from the filesystem (that lives in `CoshshDatainterface` in `datainterface.py`, from which `Item` inherits), nor does it know which specific template rules apply (those are declared on subclasses).

**Public classes.**

| Class | Description |
|---|---|
| `EmptyObject` | Bare `object` subclass used as a namespace when a `MonitoringDetail` sets nested attributes (e.g. `detail.dictionary["ns:key"]` creates an `EmptyObject` on `self.ns`). |
| `Item(coshsh.datainterface.CoshshDatainterface)` | Base class for all monitored objects. Inherits the class-factory plugin mechanism from `CoshshDatainterface`. |

**Key methods.**

`Item.__init__(self, params={})` -- Sets each key in the `params` dict as an attribute on `self`, stripping whitespace from string values unless the subclass sets `dont_strip_attributes` (as a `bool` `True` to suppress all stripping, or as a `list` of attribute names to suppress selectively). Initializes `self.monitoring_details` as an empty list (or copies the class-level default if one exists), `self.config_files` as an empty dict, and `self.object_chronicle` as an empty list. Precondition: `params` is a dict. Side effects: mutates `self`.

`Item.record_in_chronicle(self, message="")` -- Appends `message` to `self.object_chronicle` if it is non-empty. Used for audit trail / debugging.

`Item.write_config(self, target_dir, want_tool=None)` -- Writes all rendered config file content from `self.config_files` to disk under `<target_dir>/hosts/<self.host_name>/`. If `want_tool` is set, only files for that tool are written. Creates directories as needed. Side effects: filesystem writes.

`Item.resolve_monitoring_details(self)` -- Iterates over `self.monitoring_details` and promotes each detail into a proper attribute on the object. The logic handles four cases: generic details (property `"generic"`) that set dict/list/scalar attributes directly; list-typed details that append to a list property; dict-typed details that populate a dict property; and scalar details that set a single property. Details with a `unique_attribute` class attribute cause deduplication. After processing, calls `self.wemustrepeat()` and auto-populates singular property aliases from the first element of a plural list (e.g. `self.port` from `self.ports[0].port`). Side effects: mutates `self`, empties `self.monitoring_details`.

`Item.wemustrepeat(self)` -- Hook method (no-op in the base class). Subclasses override this to perform cross-detail reconciliation after `resolve_monitoring_details` runs, for example merging a LOGIN detail's credentials with a URL detail.

`Item.pythonize(self)` -- Converts Nagios-serialized comma-separated string attributes into Python lists via `str.split(',')`. The affected attributes are: `templates`, `contactgroups`, `contact_groups`, `contacts`, `hostgroups`, `servicegroups`, `members`, `parents`, `host_notification_commands`, `service_notification_commands`. Each attribute is only split if it exists on `self` (guarded by `hasattr`). Called after deserialization from a datasource so that list operations (append, extend, set membership) work correctly. Also called after each `render_cfg_template()` to restore list form after `depythonize()` converted them to strings for rendering.

`Item.depythonize(self)` -- Inverse of `pythonize`: joins list attributes back to comma-separated strings. For all attributes *except* `templates`, the join applies `sorted(list(set(...)))` which **deduplicates** (via `set`) and **sorts** the values alphabetically. The `templates` attribute is joined without deduplication or sorting to preserve template ordering (which can affect Nagios config inheritance). Called by `render_cfg_template()` just before Jinja2 rendering so that template output contains Nagios-compatible comma-separated strings. The pythonize/depythonize cycle means list attributes toggle between list and string form during each template render.

`Item.render_cfg_template(self, jinja2, template_cache, name, output_name, suffix, for_tool, **kwargs)` -- Loads and caches the Jinja2 template `<name>.tpl`, calls `self.depythonize()`, renders the template with `kwargs`, stores the result in `self.config_files[for_tool][output_name.suffix]`, then calls `self.pythonize()` to restore list form. Returns an integer count of render errors. Side effects: may populate `template_cache`, mutates `self.config_files`.

`Item.render(self, template_cache, jinja2, recipe)` -- Iterates `self.template_rules`, evaluates each `TemplateRule`'s `needsattr`/`isattr` conditions against `self`, and for matching rules delegates to `render_cfg_template`. Supports unique config filenames via `unique_config` with `%s` formatting from `unique_attr` (string or list). Returns total render error count.

`Item.fingerprint(self)` -- Returns `"<host_name>+<name>+<type>"` if all three attributes exist, otherwise `"<host_name>"` alone. This is the base fallback; subclasses override it.

See also: `TemplateRule` in [section 3.13](#313-templaterulepy); Jinja2 template system in [section 7](#7-jinja2-template-system); `CoshshDatainterface` in [section 3.5](#35-datainterfacepy).

---

### 3.7 host.py

**Responsibility.** `host.py` defines the `Host` class representing a single monitored host (server, network device, etc.). It normalizes certain columns to lowercase, sets default attribute values, and provides hook methods for subclass customization. It does NOT perform Jinja2 rendering itself (that is inherited from `Item`), nor does it load host data from any source (that is the datasource's job).

**Public classes.**

| Class | Description |
|---|---|
| `Host(coshsh.item.Item)` | Represents one monitored host. |

**Key methods.**

`Host.__init__(self, params={})` -- Lowercases the columns listed in `Host.lower_columns` (`'address'`, `'type'`, `'os'`, `'hardware'`, `'virtual'`, `'location'`, `'department'`). Initializes `self.hostgroups`, `self.contacts`, `self.contact_groups`, and `self.templates` as empty lists, and `self.ports` as `[22]`. Calls `super().__init__(params)`. Sets `self.alias` to `self.host_name` if no alias was provided. Initializes `self.macros` as an empty dict if not already set. Binds `self.fingerprint` as a lambda calling the class-level `fingerprint`. Side effects: mutates `self`.

`Host.fingerprint(cls, params)` (classmethod) -- Returns `"<params['host_name']>"`. This is the identity used for deduplication in the objects dict.

**fingerprint() return value:** `"<host_name>"` -- a single string containing only the host name.

`Host.is_correct(self)` -- Intended to return `True` if `self.host_name` exists and is not `None`. (Note: the current source contains `hasattr(self.host_name)` which is a latent bug -- it passes the attribute value to `hasattr` rather than testing the attribute name on `self`.)

`Host.create_hostgroups(self)` -- Hook method (no-op). Subclasses override to auto-create hostgroup memberships.

`Host.create_contacts(self)` -- Hook method (no-op). Subclasses override to auto-create contact associations.

`Host.create_templates(self)` -- Hook method (no-op). Subclasses override to auto-assign monitoring templates.

**Class attributes.**

- `template_rules` -- Default list containing one `TemplateRule` that renders the `"host"` template unconditionally, passing `self_name="host"`.
- `lower_columns` -- `['address', 'type', 'os', 'hardware', 'virtual', 'location', 'department']`.

See also: `Item` base class in [section 3.6](#36-itempy); `TemplateRule` in [section 3.13](#313-templaterulepy); Jinja2 templates in [section 7](#7-jinja2-template-system).

---

### 3.8 application.py

**Responsibility.** `application.py` defines the `Application` class representing a monitored application (service, process, software component) running on a host. Its `__init__` method uses the class factory to dynamically re-class itself to a specific application subclass (e.g. `os_linux`, `app_oracle_db`) or falls back to `GenericApplication`. It does NOT define monitoring checks directly -- those come from subclass `template_rules` and their Jinja2 templates.

**Public classes.**

| Class | Description |
|---|---|
| `Application(coshsh.item.Item)` | Base class for all application types. Uses the class factory pattern to dynamically select the correct subclass during `__init__`. |
| `GenericApplication(Application)` | Fallback class used when no specific application plugin matches. Only renders output if generic monitorable attributes (processes, filesystems, ports, urls, etc.) are present. |

**Key methods.**

`Application.__init__(self, params)` -- When called on the `Application` base class (not a subclass), lowercases `lower_columns` (`'name'`, `'type'`, `'component'`, `'version'`, `'patchlevel'`), calls `self.__class__.get_class(params)` to find a matching plugin class, reassigns `self.__class__` to the result (or `GenericApplication`), initializes `self.contact_groups` as an empty list, calls `super().__init__(params)`, re-invokes `self.__init__(params)` on the new class, and binds `self.fingerprint` as a lambda. When called on a subclass, does nothing (returns immediately). Side effects: mutates `self.__class__`, mutates `self`.

`Application.fingerprint(cls, params={})` (classmethod) -- Returns `"<host_name>+<name>+<type>"`.

**fingerprint() return value:** `"<host_name>+<name>+<type>"` -- three fields joined by `+`.

`Application.create_servicegroups(self)` -- Hook method (no-op). Subclasses override.

`Application.create_contacts(self)` -- Hook method (no-op). Subclasses override.

`Application.create_templates(self)` -- Hook method (no-op). Subclasses override.

`GenericApplication.render(self, template_cache, jinja2, recipe)` -- Only calls the parent `render` if the application has at least one of `processes`, `filesystems`, `cfgfiles`, `files`, `ports`, `urls`, or `services`. Otherwise returns 0 (no output). This prevents empty config files for unknown application types.

**Class attributes.**

- `class_factory` -- `[]` (populated by `init_class_factory`).
- `class_file_prefixes` -- `["app_", "os_"]`.
- `class_file_ident_function` -- `"__mi_ident__"`.
- `my_type` -- `"application"`.
- `lower_columns` -- `['name', 'type', 'component', 'version', 'patchlevel']`.

See also: `Item` base class in [section 3.6](#36-itempy); class factory mechanism in [section 4](#4-plugin--extension-system); `TemplateRule` in [section 3.13](#313-templaterulepy).

---

### 3.9 contact.py

**Responsibility.** `contact.py` defines the `Contact` class representing a notification contact. Like `Application`, it uses the class factory to dynamically re-class to a specific contact plugin or falls back to `GenericContact`. It handles default values for email, pager, address fields, and notification periods. It does NOT determine how contacts are assigned to hosts or services (that is done during recipe processing).

**Public classes.**

| Class | Description |
|---|---|
| `Contact(coshsh.item.Item)` | Base class for all contact types. Uses class factory for dynamic subclassing. |
| `GenericContact(Contact)` | Fallback contact class. Auto-generates `contact_name` from type, name, and notification period. |

**Key methods.**

`Contact.__init__(self, params)` -- When called on the base `Contact` class, lowercases `lower_columns` (currently empty list), sets default values for `email`, `pager`, `address1` through `address6` (all `None`), `can_submit_commands` (`False`), `contactgroups` (empty list), `custom_macros` (empty dict), `templates` (empty list). Calls `get_class(params)` and re-classes to the result or `GenericContact`. After re-classing, falls back `host_notification_period` and `service_notification_period` to `notification_period` if not explicitly set. Side effects: mutates `self.__class__`, mutates `self`.

`Contact.clean_name(self)` -- Replaces German umlauts in `self.name` using `coshsh.util.clean_umlauts`.

`Contact.fingerprint(cls, params)` (classmethod) -- Returns `"+".join([str(params.get(a, "")) for a in ["name", "type", "address", "userid"]])`.

**fingerprint() return value:** `"<name>+<type>+<address>+<userid>"` -- four fields joined by `+`, with missing fields as empty strings.

`Contact.__str__(self)` -- Returns a human-readable string like `"contact <name> <type> <address> <userid> groups (<contactgroups>)"`.

`GenericContact.__init__(self, params={})` -- Calls `super().__init__`, then `self.clean_name()`, then builds `self.contact_name` as `"unknown_<type>_<name>_<notification_period>"` (with `/` replaced by `_` in the period).

`GenericContact.render(self, template_cache, jinja2, recipe)` -- Delegates to the parent `Contact.render`.

**Class attributes.**

- `class_factory` -- `[]` (populated by `init_class_factory`).
- `class_file_prefixes` -- `["contact_", "contact.py"]`.
- `class_file_ident_function` -- `"__mi_ident__"`.
- `my_type` -- `"application"` (note: this value appears inherited/shared, not `"contact"`).
- `lower_columns` -- `[]`.
- `template_rules` -- One rule rendering the `"contact"` template with `self_name="contact"`, `unique_attr="contact_name"`, `unique_config="contact_%s"`.

See also: `Item` base class in [section 3.6](#36-itempy); `clean_umlauts` in [section 3.18](#318-utilpy); class factory in [section 4](#4-plugin--extension-system).

---

### 3.10 contactgroup.py

**Responsibility.** `contactgroup.py` defines the `ContactGroup` class representing a Nagios contact group. It is a simple `Item` subclass with a fingerprint based on `contactgroup_name`. It does NOT manage membership logic -- members are populated externally by datasources or during recipe processing.

**Public classes.**

| Class | Description |
|---|---|
| `ContactGroup(coshsh.item.Item)` | Represents a Nagios contactgroup with members and a unique name. |

**Key methods.**

`ContactGroup.__init__(self, params={})` -- Initializes `self.members` as an empty list, calls `super().__init__(params)`, and binds `self.fingerprint` as a lambda calling the class-level `fingerprint`.

`ContactGroup.fingerprint(cls, params)` (classmethod) -- Returns `"<params['contactgroup_name']>"`.

`ContactGroup.__str__(self)` -- Returns `"contactgroup <contactgroup_name>"`.

**Class attributes.**

- `template_rules` -- One rule rendering the `"contactgroup"` template with `self_name="contactgroup"`, `unique_attr="contactgroup_name"`, `unique_config="contactgroup_%s"`.

See also: `Item` base class in [section 3.6](#36-itempy); `Contact` in [section 3.9](#39-contactpy).

---

### 3.11 hostgroup.py

**Responsibility.** `hostgroup.py` defines the `HostGroup` class representing a Nagios host group. It overrides `write_config` to write into a `hostgroups/<hostgroup_name>/` subdirectory instead of the default `hosts/<host_name>/` path. It does NOT create host-to-group assignments -- those are driven by `Host.create_hostgroups()` or datasource data.

**Public classes.**

| Class | Description |
|---|---|
| `HostGroup(coshsh.item.Item)` | Represents a Nagios hostgroup with members, contacts, contactgroups, and templates. |

**Key methods.**

`HostGroup.__init__(self, params={})` -- Initializes `self.members`, `self.contacts`, `self.contactgroups`, and `self.templates` as empty lists, then calls `super().__init__(params)`.

`HostGroup.is_correct(self)` -- Always returns `True`.

`HostGroup.write_config(self, target_dir, want_tool=None)` -- Overrides the `Item` base method to write config files into `<target_dir>/hostgroups/<self.hostgroup_name>/` instead of the default hosts path. Creates directories as needed. Side effects: filesystem writes.

`HostGroup.create_members(self)` -- Hook method (no-op). Subclasses override to populate `self.members`.

`HostGroup.create_contacts(self)` -- Hook method (no-op). Subclasses override.

`HostGroup.create_templates(self)` -- Hook method (no-op). Subclasses override.

**Class attributes.**

- `template_rules` -- One rule rendering the `"hostgroup"` template with `self_name="hostgroup"`, `unique_attr="hostgroup_name"`, `unique_config="hostgroup_%s"`.

See also: `Item` base class in [section 3.6](#36-itempy); `Host.create_hostgroups()` in [section 3.7](#37-hostpy).

---

### 3.12 monitoringdetail.py

**Responsibility.** `monitoringdetail.py` defines the `MonitoringDetail` base class, which represents a single piece of supplementary monitoring metadata attached to a host or application (such as a filesystem path, a login credential, a URL, a TCP port, etc.). Like `Application` and `Contact`, it uses the class factory to dynamically select the correct detail subclass based on `monitoring_type`. Individual detail types are implemented as plugin files with the `detail_` prefix. `MonitoringDetail` does NOT resolve itself onto a host or application -- that is done by `Item.resolve_monitoring_details()`.

**Public classes.**

| Class | Description |
|---|---|
| `MonitoringDetailNotImplemented` | Exception raised when no plugin class matches a given `monitoring_type`. |
| `MonitoringDetail(coshsh.item.Item)` | Base class for all monitoring detail types. Uses class factory for dynamic subclass selection. |

**Key methods.**

`MonitoringDetail.__init__(self, params)` -- When called on the base class, lowercases `lower_columns` (`'name'`, `'type'`, `'application_name'`, `'application_type'`). Normalizes `params`: if `'name'` is present it is moved to `'application_name'`; if `'type'` is present it is moved to `'application_type'`. Calls `get_class(params)` and re-classes to the matching detail plugin, or raises `MonitoringDetailNotImplemented` if none matches. Side effects: mutates `self.__class__`, mutates `params` dict.

`MonitoringDetail.fingerprint(self)` -- Returns `id(self)` (the Python object identity). This is intentional: monitoring details have no meaningful natural key, and identity-based deduplication is used in `self.add('details')`.

`MonitoringDetail.application_fingerprint(self)` -- Returns `"<host_name>+<application_name>+<application_type>"` if both application name and type are present, otherwise `"<host_name>"` alone. Used to associate the detail with its parent host or application in the objects dict.

`MonitoringDetail.__eq__(self, other)` / `__ne__` / `__lt__` / `__le__` / `__gt__` / `__ge__` -- Comparison operators based on the tuple `(self.monitoring_type, str(self.monitoring_0))`. This makes details sortable and comparable by type and primary value.

`MonitoringDetail.__repr__(self)` -- Returns `"<monitoring_type> <monitoring_0>"`.

**Class attributes.**

- `class_factory` -- `[]` (populated by `init_class_factory`).
- `class_file_prefixes` -- `["detail_"]`.
- `class_file_ident_function` -- `"__detail_ident__"`.
- `my_type` -- `"detail"`.
- `lower_columns` -- `['name', 'type', 'application_name', 'application_type']`.

See also: `Item.resolve_monitoring_details()` in [section 3.6](#36-itempy); MonitoringDetail type reference in [section 5](#5-monitoringdetail-type-reference); plugin authoring in [section 12.3](#123-creating-a-monitoringdetail-plugin).

---

### 3.13 templaterule.py

**Responsibility.** `templaterule.py` defines the `TemplateRule` class, a pure data object that describes when and how a Jinja2 template should be rendered for a given `Item`. Template rules are declared as class-level lists on `Host`, `Application`, `Contact`, etc. The rendering engine in `Item.render()` evaluates each rule's conditions and delegates to `Item.render_cfg_template()`. `TemplateRule` does NOT perform rendering or template loading itself.

**Public classes.**

| Class | Description |
|---|---|
| `TemplateRule` | Declarative rule binding a Jinja2 template to a condition and output configuration. |

**Key methods.**

`TemplateRule.__init__(self, needsattr=None, isattr=None, template=None, unique_attr="name", unique_config=None, self_name="application", suffix="cfg", for_tool="nagios")` -- Stores all parameters as instance attributes. Parameters:
- `needsattr` -- Attribute name that must exist on the object for this rule to fire. `None` means the rule always fires.
- `isattr` -- Required value or regex pattern that `needsattr` must match. `None` means any value suffices.
- `template` -- Name of the Jinja2 template file (without `.tpl` extension).
- `unique_attr` -- Attribute name (str) or list of attribute names used for unique config filename generation.
- `unique_config` -- Format string for the output filename (e.g. `"app_%s_%s_default"`), or `None` to use the template name.
- `self_name` -- The variable name under which the object is passed into the template context (default `"application"`).
- `suffix` -- File extension for the output file (default `"cfg"`).
- `for_tool` -- Tool namespace for the output file (default `"nagios"`).

`TemplateRule.__str__(self)` -- Returns a debug string showing all rule attributes.

See also: `Item.render()` in [section 3.6](#36-itempy); Jinja2 template system in [section 7](#7-jinja2-template-system); template file naming in [section 7.8](#78-template-file-naming).

---

### 3.14 vault.py

**Responsibility.** `vault.py` defines the `Vault` base class and its associated exceptions. A vault is a pluggable key-value store for secrets (passwords, SNMP communities, API keys). Like other coshsh plugin types, `Vault.__init__` uses the class factory to dynamically select the correct vault backend based on configuration parameters. The base class provides `open`, `read`, `close`, `get`, and `getall` methods. Concrete vault backends (file-based, database-backed, etc.) are plugin files with the `vault` prefix. `Vault` does NOT perform `@VAULT[...]` substitution in templates -- that is done at the recipe level during rendering.

**Public classes.**

| Class | Description |
|---|---|
| `VaultNotImplemented` | Exception raised when no vault plugin matches the given params. |
| `VaultNotReady` | Exception raised when the vault is currently being updated and cannot be read. |
| `VaultNotCurrent` | Exception raised when vault data is stale and it is unsafe to continue. |
| `VaultNotAvailable` | Exception raised when the vault backend is unreachable. |
| `VaultCorrupt` | Exception raised when the vault data is corrupt or unreadable. |
| `Vault(coshsh.datainterface.CoshshDatainterface)` | Base class for all vault backends. Inherits the class factory from `CoshshDatainterface`. |

**Key methods.**

`Vault.__init__(self, **params)` -- Copies any `recipe_*` prefixed params to the corresponding unprefixed name. Applies `%ENV_VAR%` substitution on all string params via `coshsh.util.substenv`. If called on the base `Vault` class, calls `get_class(params)` and re-classes to the matching vault plugin, or raises `VaultNotImplemented`. If called on a subclass, sets `self.name` and initializes `self._data` as an empty dict.

`Vault.open(self, **kwargs)` -- Hook method (no-op). Subclasses override to establish a connection to the vault backend.

`Vault.read(self, **kwargs)` -- Hook method (no-op). Subclasses override to populate `self._data` from the backend.

`Vault.close(self)` -- Hook method (no-op). Subclasses override to close the backend connection.

`Vault.get(self, key)` -- Returns `self._data[key]` or `None` if the key does not exist.

`Vault.getall(self)` -- Returns `list(self._data.values())` or an empty list on error.

**Class attributes.**

- `my_type` -- `'vault'`.
- `class_file_prefixes` -- `["vault"]`.
- `class_file_ident_function` -- `"__vault_ident__"`.
- `class_factory` -- `[]` (populated by `init_class_factory`).

See also: Vault and secrets management in [section 10](#10-vault-and-secrets-management); `CoshshDatainterface` in [section 3.5](#35-datainterfacepy); plugin authoring for vaults in [section 12.4](#124-creating-a-vault-plugin).

---

### 3.15 configparser.py

**Responsibility.** `configparser.py` defines `CoshshConfigParser`, a thin subclass of Python's standard `RawConfigParser`. Its sole additional behavior is implementing `isa`-based section inheritance: after reading the INI file, any section that contains an `isa` key inherits all unset keys from the referenced section. It does NOT perform `%ENV_VAR%` substitution (that happens at the vault/datasource level) or any coshsh-specific key validation.

**Public classes.**

| Class | Description |
|---|---|
| `CoshshConfigParser(RawConfigParser, object)` | Extended config parser with `isa` section inheritance. |

**Key methods.**

`CoshshConfigParser.read(self, files)` -- Calls `super().read(files)` and then iterates over all sections. For any section containing an `isa` key whose value matches the name of another section, copies all keys from the parent section that are not already present in the child (excluding the `isa` key itself). Precondition: the referenced `isa` section must exist. Side effects: mutates the in-memory section data.

See also: INI configuration file reference in [section 6](#6-ini-configuration-file-reference); recipe inheritance via `isa` in [section 6.9](#69-recipe-inheritance-via-isa).

---

### 3.16 jinja2_extensions.py

**Responsibility.** `jinja2_extensions.py` provides custom Jinja2 filters, tests, and global functions that are registered into the Jinja2 environment used by coshsh templates. These include regex matching, regex substitution, Nagios service/host/contact definition formatting with NAGIOSCONF attribute injection, custom macro output, RFC 3986 encoding, neighbor application lookup, and environment variable access. It does NOT manage the Jinja2 environment lifecycle (that is done in `Item.reload_template_path` and the recipe setup).

**Public functions (registered as Jinja2 tests).**

| Function | Description |
|---|---|
| `is_re_match(s, rs, flagstr=None)` | Returns `True` if regex `rs` matches string `s`. Optional `flagstr` is a string of flag characters (`i`, `l`, `m`, `s`, `u`, `x`). |

**Public functions (registered as Jinja2 filters).**

| Function | Description |
|---|---|
| `filter_re_sub(s, rs, repl, flagstr=None, count=0)` | Returns the string with all (or up to `count`) regex matches of `rs` replaced by `repl`. |
| `filter_re_escape(s)` | Returns the string with all regex metacharacters escaped. |
| `filter_service(application, service_description)` | Generates a Nagios `define service { ... }` block, handling NAGIOSCONF overrides and custom macros. If `nagios_config_attributes` matching the service description exist, emits a service template pattern with overrides. |
| `filter_host(host)` | Generates a Nagios `define host { ... }` block, handling NAGIOSCONF overrides and custom macros. |
| `filter_contact(contact)` | Generates a Nagios `define contact { ... }` block, handling NAGIOSCONF overrides and custom macros. |
| `filter_custom_macros(obj)` | Returns a string of Nagios custom macro lines (prefixed with `_`) from `obj.custom_macros` and `obj.macros`. |
| `filter_rfc3986(text)` | Returns an RFC 3986-encoded URL representation of `text`. |
| `filter_neighbor_applications(application)` | Returns all applications belonging to `application.host`. |

**Public functions (registered as Jinja2 globals).**

| Function | Description |
|---|---|
| `global_environ(var, default=None)` | Returns the value of environment variable `var`, or `default`, or `""` if not set and no default. |

**Helper functions (internal).**

| Function | Description |
|---|---|
| `get_re_flags(flagstr)` | Converts a flag string like `"im"` to a combined `re` flags integer. |

See also: Jinja2 template system in [section 7](#7-jinja2-template-system); `filter_service` and NAGIOSCONF in [section 7.7](#77-service-filter-and-nagiosconf); `Item.render_cfg_template()` in [section 3.6](#36-itempy).

---

### 3.17 dependency.py

**Responsibility.** `dependency.py` defines the `Dependency` class, a simple data object representing a parent-child host dependency (i.e. Nagios network hierarchy). It stores `host_name` and `parent_host_name`. It does NOT resolve or validate that the referenced hosts exist -- that is the caller's responsibility.

**Public classes.**

| Class | Description |
|---|---|
| `Dependency` | Represents a host-to-parent-host dependency relationship. |

**Key methods.**

`Dependency.__init__(self, params={})` -- Sets `self.host_name = params["host_name"]` and `self.parent_host_name = params["parent_host_name"]`. Precondition: `params` must contain both keys.

See also: used by datasources to populate the `parents` attribute on `Host` objects.

---

### 3.18 util.py

**Responsibility.** `util.py` provides standalone utility functions and classes used throughout the coshsh codebase. It contains an ordered dictionary class, attribute comparison helpers, string cleaning functions, environment variable substitution, filename sanitization, and the logging setup/switching infrastructure. It does NOT depend on any other coshsh module.

**Public classes.**

| Class | Description |
|---|---|
| `odict(MutableMapping)` | Ordered dictionary that preserves insertion order. Used for `generator.recipes`. |

**Key functions.**

`compare_attr(key, params, strings)` -- Returns `True` if `params[key]` matches any of the given `strings` via `re.match` (case-insensitive). Returns `False` if the key is missing or `None`. Used in `__mi_ident__` functions in application plugin files to test whether params match a given application type.

`is_attr(key, params, strings)` -- Returns `True` if `params[key]` is an exact case-insensitive match to any of the given `strings`. Unlike `compare_attr`, this does not use regex.

`cleanout(dirty_string, delete_chars="", delete_words=[])` -- Removes all characters in `delete_chars` and all substrings in `delete_words` from `dirty_string`, then strips whitespace. Returns the original if `dirty_string` is falsy.

`substenv(matchobj)` -- Regex substitution callback that replaces `%ENV_VAR%` patterns with the corresponding environment variable value, or leaves the pattern unchanged if the variable is not set.

`normalize_dict(the_dict, titles=[])` -- Lowercases all keys in `the_dict`, strips whitespace from values, and additionally lowercases the values of any keys listed in `titles`. Mutates `the_dict` in place.

`clean_umlauts(text)` -- Replaces German umlauts and sharp-s with ASCII equivalents (e.g. `'ss'` for sharp-s, `'oe'` for o-umlaut). Returns the cleaned string.

`sanitize_filename(filename)` -- Replaces characters invalid in filenames (`\ / * ? : " < > | space`) with underscores. If any replacement was made, appends a 4-character MD5 hash suffix to avoid collisions. Returns the sanitized filename.

`setup_logging(logdir=".", logfile="coshsh.log", scrnloglevel=logging.INFO, txtloglevel=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", backup_count=2)` -- Initializes the `coshsh` logger with a `RotatingFileHandler` (20 MB max, configurable backup count) and a stderr `StreamHandler`. Stores configuration on the function object for later use by `switch_logging`. Returns the logger. Side effects: creates log directories, attaches handlers.

`switch_logging(**kwargs)` -- Replaces the file handler on the existing logger with a new one pointing to a different log file. Used when per-recipe logging is configured. Side effects: modifies logger handlers.

`restore_logging()` -- Restores the logger to the original file configured in `setup_logging`.

`get_logger(self, name="coshsh")` -- Returns `logging.getLogger(name)`.

See also: `substenv` is used by `Vault.__init__` ([section 3.14](#314-vaultpy)) and recipe-level config processing; `compare_attr` and `is_attr` are used throughout application plugin `__mi_ident__` functions ([section 4](#4-plugin--extension-system)); `sanitize_filename` is used for output file naming ([section 8.5](#85-filename-conventions-and-sanitization)); logging functions are called from `generator.py` ([section 3.1](#31-generatorpy)).

---

## 4. Plugin / Extension System

### 4.1 Class factory mechanism

The plugin system is built on `CoshshDatainterface` (defined in `coshsh/datainterface.py`), which provides two class-level methods that form the core of runtime plugin discovery: `init_class_factory()` and `get_class()`.

**`init_class_factory(classpath)`** -- Accepts a list of directory paths. It iterates over the directories (in reversed order; see section 4.5) and, for each directory that exists, scans for `.py` files whose filenames match `cls.class_file_prefixes` (either an exact match or a prefix match). For each matching `.py` file, the method:

1. Computes the absolute path to the file.
2. Loads the module using `importlib.util.spec_from_file_location()` and `spec.loader.exec_module()`. This approach is used because plugin files reside in user-configurable directories that are not on `sys.path`, so standard `import` cannot find them.
3. Inspects the loaded module for a function named `cls.class_file_ident_function` (e.g. `__mi_ident__`, `__ds_ident__`).
4. If found, appends a triple `[path, module_filename, ident_func]` to an internal `class_factory` list.

The method then calls `cls.update_class_factory(class_factory)` to replace the class-level `cls.class_factory` list entirely. This means every call to `init_class_factory()` discards all previously registered plugins for that subclass. Module-level code in each plugin file executes at load time as a side effect of `exec_module()`.

**`get_class(params={})`** -- Iterates `cls.class_factory` in reverse order (see section 4.5), calling each registered ident function with the `params` dict. The first ident function that returns a non-None value (a class) wins. That class is returned to the caller, and a usage counter in `cls.usage_numbers` is incremented. If no ident function matches, `None` is returned.

Each `CoshshDatainterface` subclass (`Application`, `Datasource`, `Datarecipient`, `MonitoringDetail`, `Vault`, `Contact`) sets its own `class_file_prefixes` and `class_file_ident_function` to control which files are scanned and which function name is looked up.

Note: `class_factory` is a mutable class-level list shared across all uses of a given subclass. It must be reset (via `init_class_factory` or direct assignment to `[]`) between tests to prevent cross-test contamination.

### 4.2 Class path search order and catchall

The `classpath` passed to `init_class_factory()` is a list of directories searched in order. It is constructed in `Recipe.__init__()` (in `coshsh/recipe.py`) with the following logic:

1. A **default/fallback directory** is determined first. Under OMD this is `$OMD_ROOT/share/coshsh/recipes/default/classes`; otherwise it is `../recipes/default/classes` relative to the coshsh package directory. This is stored as the initial `self.classes_path`.

2. If the recipe configuration specifies a `classes_dir` (a comma-separated list of directories), the list is split and reordered:
   - Directories whose basename is **not** `catchall` are prepended before the default path.
   - The default path stays in the middle.
   - Directories whose basename **is** `catchall` are appended at the end.

The resulting `classes_path` for a recipe with `classes_dir = /site/classes,/site/catchall` would be:

```
["/site/classes", "<default>/recipes/default/classes", "/site/catchall"]
```

This ordering means recipe-specific directories are checked first (highest priority), the built-in default classes directory is checked next, and catchall directories are checked last (lowest priority, broadest matching). See section 4.6 for more on catchall directories.

The same pattern is applied to `templates_path` for Jinja2 template resolution.

### 4.3 Ident function conventions

Each plugin `.py` file must define a module-level ident function with a specific name depending on the plugin type. The ident function receives a `params` dict and must return either a class (indicating a match) or `None` (no match). The four ident function naming conventions are:

**`__ds_ident__(params={})`** -- Used by datasource plugins (files matching `datasource*`). The `params` dict contains datasource configuration attributes; typically the function checks `params["type"]` to decide whether to claim the datasource. Example:

```python
def __ds_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "^csv$"):
        return CsvFile
```

**`__dr_ident__(params={})`** -- Used by datarecipient plugins (files matching `datarecipient*`). Same pattern as `__ds_ident__`, matching on the datarecipient `type`. Example:

```python
def __dr_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "^datarecipient_coshsh_default$"):
        return DatarecipientCoshshDefault
```

**`__mi_ident__(params={})`** -- Used by application/host plugins (files matching `app_*` or `os_*`) and also by contact plugins (files matching `contact_*` or `contact.py`). The `params` dict contains attributes like `name` and `type`. Application ident functions typically use `compare_attr` (regex match) or `is_attr` (exact match) on these fields. Example:

```python
def __mi_ident__(params={}):
    if coshsh.util.is_attr("name", params, "os") and \
       coshsh.util.compare_attr("type", params, r".*linux.*"):
        return Linux
```

**`__detail_ident__(params={})`** -- Used by MonitoringDetail plugins (files matching `detail_*`). The `params` dict contains `monitoring_type` and monitoring data fields. The function typically checks `params["monitoring_type"]` for an exact string match. Example:

```python
def __detail_ident__(params={}):
    if params["monitoring_type"] == "LOGIN":
        return MonitoringDetailLogin
```

**`__vault_ident__(params={})`** -- Used by vault plugins (files matching `vault*`). The `params` dict contains vault configuration attributes. Example:

```python
def __vault_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "naemon_vault"):
        return NaemonVault
```

A single ident function may return different classes depending on the params (e.g. `datasource_csvfile.py` returns `CsvFileRecipe` for type `recipe_csv` and `CsvFile` for type `csv`). If no condition matches, the function implicitly returns `None`, allowing the next registered ident function to be tried.

### 4.4 Class file naming prefixes

Each `CoshshDatainterface` subclass declares which `.py` filenames it will scan via the `class_file_prefixes` class attribute. A file is loaded if its name either exactly matches an entry in `class_file_prefixes` or starts with one of the prefix strings. The conventions are:

| Subclass           | `class_file_prefixes`       | `class_file_ident_function` | Example files                        |
|--------------------|-----------------------------|-----------------------------|--------------------------------------|
| `Application`      | `["app_", "os_"]`           | `__mi_ident__`              | `app_db_mysql.py`, `os_linux.py`     |
| `MonitoringDetail` | `["detail_"]`               | `__detail_ident__`          | `detail_login.py`, `detail_port.py`  |
| `Datasource`       | `["datasource"]`            | `__ds_ident__`              | `datasource_csvfile.py`              |
| `Datarecipient`    | `["datarecipient"]`         | `__dr_ident__`              | `datarecipient_coshsh_default.py`    |
| `Vault`            | `["vault"]`                 | `__vault_ident__`           | `vault_naemon.py`                    |
| `Contact`          | `["contact_", "contact.py"]`| `__mi_ident__`              | `contact_defaults.py`                |

Note that `Contact` uses the same ident function name (`__mi_ident__`) as `Application`, but its `class_file_prefixes` restrict scanning to `contact_*` and `contact.py` files, so there is no conflict. Similarly, `Datasource` and `Datarecipient` both use `"datasource"` and `"datarecipient"` as prefixes respectively (without trailing underscore), so files like `datasource_csvfile.py` and `datarecipient_coshsh_default.py` both match via the startswith check.

When creating a new plugin, the filename must follow these prefix conventions or the class factory scanner will not discover it.

### 4.5 Reversed iteration order

The iteration order in `init_class_factory()` and `get_class()` uses two reversals that work together to give user-supplied classes priority over built-in defaults:

1. **In `init_class_factory()`**: The classpath is iterated using `reversed(classpath)`. Since the classpath is ordered with user/recipe-specific directories first and catchall/default directories last (see section 4.2), reversing means the **default directories are processed first** and the **user directories are processed last**. Within each directory, files are also sorted in reverse order (`sorted(os.listdir(p), reverse=True)`). The result is that user-supplied plugin ident functions are appended to the end of the `class_factory` list.

2. **In `get_class()`**: The `class_factory` list is iterated using `reversed(cls.class_factory)`. This means entries appended last (user-supplied classes) are checked **first**. The first ident function that returns a non-None class wins.

The combined effect is: user-supplied classes always take priority over built-in defaults. If a user provides an `app_custom.py` in their recipe's `classes_dir` that claims the same `type` as a built-in plugin in `recipes/default/classes/`, the user's class will be found first by `get_class()` and will be used. The built-in class is still registered in `class_factory` but will never be reached for params that the user's ident function already claims.

This double-reversal pattern allows local overrides without modifying or removing any core plugin files.

### 4.6 Catchall directories

Catchall directories are directories whose basename is `catchall` (e.g. `/site/recipes/test33/catchall/`). They contain generic, broadly-matching plugin implementations that serve as last-resort fallbacks for any application type not handled by a more specific plugin.

During classpath construction in `Recipe.__init__()`, directories named `catchall` are explicitly separated from the rest and appended to the **end** of `classes_path`:

```python
self.classes_path = [non-catchall dirs] + [default path] + [catchall dirs]
```

Because catchall directories are last in the classpath, the double-reversal mechanism (section 4.5) ensures their ident functions are checked **last** during `get_class()`. A typical catchall plugin uses a very broad regex like `".*"` in its ident function to match any application type:

```python
# In catchall/app_my_generic.py
def __mi_ident__(params={}):
    if coshsh.util.compare_attr("type", params, ".*"):
        return MyGenericApplication
```

This pattern ensures that every application gets at least some monitoring configuration, even if no specific plugin exists for its type. Without a catchall, applications with unrecognized types would have no matching class and would produce no monitoring config output.

Catchall directories are optional. If no directory named `catchall` appears in `classes_dir`, no catchall behavior is applied. Multiple catchall directories can be specified; all will be appended at the end of the classpath in their original comma-separated order.

See also: [section 3.5 datainterface.py](#35-datainterfacepy), [section 12 Plugin Authoring Guide](#12-plugin-authoring-guide)

### 4.7 Hook methods called during assemble

After `resolve_monitoring_details()` runs on each host and application during `Recipe.assemble()`, a series of hook methods are called. These hooks are no-ops in the base classes (`Item`, `Host`, `Application`) but are designed for subclasses to override.

**Call sequence for hosts** (in `Recipe.assemble()`):

```
host.resolve_monitoring_details()
    └── internally calls host.wemustrepeat()
host.create_templates()
host.create_hostgroups()
host.create_contacts()
```

**Call sequence for applications:**

```
app.resolve_monitoring_details()
    └── internally calls app.wemustrepeat()
app.create_templates()
app.create_servicegroups()
app.create_contacts()
```

**`wemustrepeat()`** -- Called at the end of `resolve_monitoring_details()`, after all details have been promoted to attributes but before host/application creation hooks run. This is the only place where cross-detail reconciliation can happen, because all detail objects have been resolved by this point. Typical use cases:

- Merging LOGIN credentials with URL details (e.g. injecting username/password into a URL string)
- Setting custom macros from detail attributes (e.g. SSH port from a LOGIN detail becomes a macro on the host)
- Conditionally adding hostgroups based on detail values (e.g. cluster membership from a detail adds the host to a cluster hostgroup)

```python
# Example: an os_linux application merging SSH login details
class AppOsLinux(Application):
    def wemustrepeat(self):
        if hasattr(self, 'login'):
            self.ssh_port = getattr(self.login, 'port', '22')
            self.host.macros['_SSH_PORT'] = self.ssh_port
```

**`create_hostgroups()`** -- Called on hosts after detail resolution. Override to derive hostgroup membership from resolved attributes (e.g. OS type, location, department). Defined in `host.py`.

**`create_contacts()`** -- Called on both hosts and applications. Override to derive contact/contactgroup assignments from resolved attributes. Defined in `host.py` and `application.py`.

**`create_templates()`** -- Called on both hosts and applications. Override to dynamically add or remove template rules based on resolved attributes. Useful when template selection depends on runtime data rather than static class definitions. Defined in `host.py` and `application.py`.

**`create_servicegroups()`** -- Called on applications only. Override to define service group membership based on application attributes. Defined in `application.py`.

**Important ordering note:** Hostgroups from `application.wemustrepeat()` are only collected into `recipe.objects['hostgroups']` *after* all applications have been processed. This means an application's `wemustrepeat()` can modify `self.host.hostgroups` and the change will be picked up when the recipe iterates hosts to collect hostgroup memberships.

### 4.8 property_flat and property_attr detail resolution

When `resolve_monitoring_details()` processes a detail, the detail class's class-level attributes control how the detail's data is stored on the parent object. These three attributes interact:

**`property_flat`** (default: not set / `False`)

When `property_flat = True` on a detail class whose `property_type` is a scalar (e.g. `str`, `int`), the resolution sets the parent attribute to the *value* of the detail's property, not the detail object itself. This means the attribute on the parent is a plain Python value, not a `MonitoringDetail` instance.

```python
# detail_role.py
class MonitoringDetailRole(MonitoringDetail):
    property = "role"
    property_type = str
    property_flat = True
    # Result: application.role == "webserver" (a string)
    # Without property_flat: application.role == <MonitoringDetailRole object>
```

**`property_attr`** (default: not set)

When `property_attr` is set on a list-typed detail class, the resolution appends only the named attribute from the detail object instead of the entire detail. Combined with `property_flat = True` (which is typical), this produces a flat list of simple values.

```python
# detail_tag.py
class MonitoringDetailTag(MonitoringDetail):
    property = "tags"
    property_type = list
    property_flat = True
    property_attr = "tag"
    # Result: application.tags == ["web", "prod", "critical"] (list of strings)
    # Without property_attr: application.tags == [<MonitoringDetailTag>, ...] (list of objects)
```

**`unique_attribute`** (default: not set)

When `unique_attribute` is set on a list-typed detail class, the resolution enforces deduplication by the named attribute. If a new detail has the same `unique_attribute` value as an existing detail in the list, the old entry is **replaced** (not duplicated). This is replacement-instead-of-append semantics.

```python
# detail_filesystem.py
class MonitoringDetailFilesystem(MonitoringDetail):
    property = "filesystems"
    property_type = list
    unique_attribute = "path"
    # If two FILESYSTEM details have path="/var", the second replaces the first.
    # Result: each filesystem path appears exactly once.
```

**Interaction matrix:**

| `property_type` | `property_flat` | `property_attr` | `unique_attribute` | Result on parent |
|---|---|---|---|---|
| `list` | no | no | no | List of detail objects |
| `list` | no | no | yes | List of detail objects, deduplicated by `unique_attribute` |
| `list` | yes | `"attr"` | no | Flat list of `detail.attr` values |
| `str`/`int` | yes | -- | -- | Scalar value (`detail.property_name`) |
| `str`/`int` | no | -- | -- | Detail object itself |
| `dict` | -- | -- | -- | Dict of `detail.key` → `detail.value` |

See also: [section 5 MonitoringDetail Type Reference](#5-monitoringdetail-type-reference), [section 14.9 property_flat gotcha](#149-property_flat-gotcha).

---

## 5. MonitoringDetail Type Reference

### 5.1 LOGIN

**monitoring_type**: `"LOGIN"` | **property**: `login` | **property_type**: `str`

| Column | Attribute | Description |
|--------|-----------|-------------|
| monitoring_0 | `username` | Login username |
| monitoring_1 | `password` | Login password |

After resolution, the parent object gets `self.login` set to the MonitoringDetailLogin instance. Access credentials via `application.login.username` and `application.login.password` in templates.

```jinja2
{{ application.login.username }}
```

### 5.2 LOGINSNMPV2

**monitoring_type**: `"LOGINSNMPV2"` | **property**: `loginsnmpv2` | **property_type**: `str`

| Column | Attribute | Description |
|--------|-----------|-------------|
| monitoring_0 | `community` | SNMP community string (default `"public"`). Prefix with `v1:` or `v2:` to force protocol version. |

Derived attribute: `protocol` (int, 1 or 2, default 2).

```jinja2
-C {{ application.loginsnmpv2.community }}
```

### 5.3 LOGINSNMPV3

**monitoring_type**: `"LOGINSNMPV3"` | **property**: `loginsnmpv3` | **property_type**: `str`

| Column | Attribute | Description |
|--------|-----------|-------------|
| monitoring_0 | `securityname` | SNMPv3 security name |
| monitoring_1 | `authprotocol` | Auth protocol (e.g. MD5, SHA) |
| monitoring_2 | `authkey` | Auth passphrase |
| monitoring_3 | `privprotocol` | Privacy protocol (e.g. DES, AES) |
| monitoring_4 | `privkey` | Privacy passphrase |
| monitoring_5 | `context` | SNMP context |

Derived attribute: `securitylevel` (`"noAuthNoPriv"`, `"authNoPriv"`, or `"authPriv"`).

### 5.4 FILESYSTEM

**monitoring_type**: `"FILESYSTEM"` | **property**: `filesystems` | **property_type**: `list` | **unique_attribute**: `path`

| Column | Attribute | Default | Description |
|--------|-----------|---------|-------------|
| monitoring_0 | `path` | (required) | Filesystem mount path |
| monitoring_1 | `warning` | `"10"` | Warning threshold |
| monitoring_2 | `critical` | `"5"` | Critical threshold |
| monitoring_3 | `units` | `"%"` | Threshold unit |
| monitoring_4 | `optional` | `"0"` | Boolean: filesystem may not exist |
| monitoring_5 | `iwarning` | `"0"` | Inode warning threshold |
| monitoring_6 | `icritical` | `"0"` | Inode critical threshold |

After resolution, `application.filesystems` is a list of MonitoringDetailFilesystem objects. The `unique_attribute = "path"` enables per-filesystem config files via `TemplateRule.unique_config`.

```jinja2
{% for fs in application.filesystems %}
  {{ fs.path }} {{ fs.warning }}:{{ fs.critical }}
{% endfor %}
```

### 5.5 PORT

**monitoring_type**: `"PORT"` | **property**: `ports` | **property_type**: `list`

| Column | Attribute | Default | Description |
|--------|-----------|---------|-------------|
| monitoring_0 | `port` | (required) | Port number |
| monitoring_1 | `warning` | `"1"` | Warning threshold (response time) |
| monitoring_2 | `critical` | `"10"` | Critical threshold (response time) |

After resolution, `application.ports` (or `host.ports`) is a list. Note: Host.__init__ defaults `self.ports = [22]`.

### 5.6 INTERFACE

**monitoring_type**: `"INTERFACE"` | **property**: `interfaces` | **property_type**: `list`

| Column | Attribute | Description |
|--------|-----------|-------------|
| monitoring_0 | `name` | Interface name (e.g. `eth0`) |

### 5.7 DATASTORE

**monitoring_type**: `"DATASTORE"` | **property**: `datastores` | **property_type**: `list`

| Column | Attribute | Default | Description |
|--------|-----------|---------|-------------|
| monitoring_0 | `name` | (required) | Datastore name |
| monitoring_1 | `warning` | `"10"` | Warning threshold |
| monitoring_2 | `critical` | `"5"` | Critical threshold |
| monitoring_3 | `units` | `"%"` | Threshold unit |

Derived: `path` = `"/vmfs/volumes/{name}"`.

### 5.8 TABLESPACE

**monitoring_type**: `"TABLESPACE"` | **property**: `tablespaces` | **property_type**: `list`

| Column | Attribute | Default | Description |
|--------|-----------|---------|-------------|
| monitoring_0 | `name` | (required) | Tablespace name |
| monitoring_1 | `warning` | `"10"` | Warning threshold |
| monitoring_2 | `critical` | `"5"` | Critical threshold |
| monitoring_3 | `units` | `"%"` | Threshold unit |

### 5.9 URL

**monitoring_type**: `"URL"` | **property**: `urls` | **property_type**: `list`

| Column | Attribute | Default | Description |
|--------|-----------|---------|-------------|
| monitoring_0 | `url` | (required) | Full URL to monitor |
| monitoring_1 | `warning` | `"5"` | Warning response time |
| monitoring_2 | `critical` | `"10"` | Critical response time |
| monitoring_3 | `url_expect` | `None` | Expected response content |

The URL is parsed using `urllib.parse.urlparse`, exposing `scheme`, `netloc`, `path`, `hostname`, `port`, `username`, `password`, `query`, `fragment` as attributes.

### 5.10 TAG

**monitoring_type**: `"TAG"` | **property**: `tags` | **property_type**: `list` | **property_flat**: `True` | **property_attr**: `tag`

| Column | Attribute | Description |
|--------|-----------|-------------|
| monitoring_0 | `tag` | Tag string |

After resolution, `application.tags` is a flat list of tag strings (not objects), because `property_flat = True` and `property_attr = "tag"` extracts just the `tag` attribute.

```jinja2
{% if "critical" in application.tags %}...{% endif %}
```

### 5.11 ROLE

**monitoring_type**: `"ROLE"` | **property**: `role` | **property_type**: `str` | **property_flat**: `True`

| Column | Attribute | Description |
|--------|-----------|-------------|
| monitoring_0 | `role` | Role string (e.g. `"master"`, `"slave"`) |

After resolution, `application.role` is a plain string (the last one wins if multiple ROLE details exist).

### 5.12 DEPTH

**monitoring_type**: `"DEPTH"` | **property**: `monitoring_depth` | **property_type**: `int` | **property_flat**: `True`

| Column | Attribute | Default | Description |
|--------|-----------|---------|-------------|
| monitoring_0 | `monitoring_depth` | `1` | Monitoring depth level (0=ignore, 1=minimum, n=expert) |

After resolution, `application.monitoring_depth` is an integer.

### 5.13 VOLUME

**monitoring_type**: `"VOLUME"` | **property**: `volumes` | **property_type**: `list`

| Column | Attribute | Default | Description |
|--------|-----------|---------|-------------|
| monitoring_0 | `name` | (required) | Volume name |
| monitoring_1 | `warning` | `"10"` | Warning threshold |
| monitoring_2 | `critical` | `"5"` | Critical threshold |
| monitoring_3 | `units` | `"%"` | Threshold unit |

### 5.14 PROCESS

**monitoring_type**: `"PROCESS"` | **property**: `processes` | **property_type**: `list`

| Column | Attribute | Default | Description |
|--------|-----------|---------|-------------|
| monitoring_0 | `name` | (required) | Process name |
| monitoring_1 | `warning` | `"1:1"` | Warning range |
| monitoring_2 | `critical` | `"1:"` | Critical range |
| monitoring_3 | `alias` | same as `name` | Display alias |

### 5.15 SOCKET

**monitoring_type**: `"SOCKET"` | **property**: `socket` | **property_type**: `str`

| Column | Attribute | Default | Description |
|--------|-----------|---------|-------------|
| monitoring_0 | `socket` | (required) | Socket path or address |
| monitoring_1 | `warning` | `"1"` | Warning threshold |
| monitoring_2 | `critical` | `"10"` | Critical threshold |

### 5.16 ACCESS

**monitoring_type**: `"ACCESS"` | **property**: `access` | **property_type**: `str` | **property_flat**: `True`

| Column | Attribute | Description |
|--------|-----------|-------------|
| monitoring_0 | `access` | Access mode string |

### 5.17 KEYVALUES

**monitoring_type**: `"KEYVALUES"` | **property**: `generic` | **property_type**: `dict`

| Column | Attribute | Description |
|--------|-----------|-------------|
| monitoring_0 | key 1 | First key name |
| monitoring_1 | value 1 | First key value |
| monitoring_2 | key 2 | Second key name (optional) |
| monitoring_3 | value 2 | Second key value (optional) |
| monitoring_4 | key 3 | Third key name (optional) |
| monitoring_5 | value 3 | Third key value (optional) |

Stores key-value pairs in `self.dictionary`. After resolution, pairs are merged into the parent's `generic` dict. Up to 3 key-value pairs per detail row.

There is also a `KEYVALUESARRAY` variant (same file) with `property_type = list` that appends values to lists keyed by the same names, enabling multi-value accumulation.

### 5.18 NAGIOSCONF

**monitoring_type**: `"NAGIOSCONF"` | **property**: `nagios_config_attributes` | **property_type**: `list`

| Column | Attribute | Description |
|--------|-----------|-------------|
| monitoring_0 | `name` | Service description to override |
| monitoring_1 | `attribute` | Nagios directive name (e.g. `max_check_attempts`) |
| monitoring_2 | `value` | Directive value. If `attribute` ends with `groups`, value is wrapped in a list. |

Used by the `service`, `host`, and `contact` Jinja2 filters to generate the two-tier template pattern. See [§7.7](#77-service-filter-and-nagiosconf).

Note: There is also a `"NAGIOS"` type (in `detail_nagios.py`) with `property = "generic"`, `property_type = str`, that stores a generic attribute/value pair via `monitoring_0` (attribute) and `monitoring_1` (value).

### 5.19 CUSTOM_MACRO

**monitoring_type**: `"CUSTOMMACRO"` | **property**: `custom_macros` | **property_type**: `dict`

| Column | Attribute | Description |
|--------|-----------|-------------|
| monitoring_0 | `key` | Macro name (rendered with `_` prefix in Nagios config) |
| monitoring_1 | `value` | Macro value |

After resolution, `application.custom_macros` is a dict. The `custom_macros` Jinja2 filter renders these as `_KEY VALUE` lines in the service/host/contact definition.

---

## 6. INI Configuration File Reference

### 6.1 defaults section

The `[defaults]` section provides fallback values that are consumed by `generator.read_cookbook()` before any recipe is instantiated. It also determines which recipes to run when no `--recipe` CLI flag is given.

| Key | Type | Default | Effect |
|-----|------|---------|--------|
| `recipes` | comma-separated string | (all non-underscore-prefixed recipes) | List of recipe names to execute when `--recipe` is not passed on the command line. Example: `recipes = prod,nonprod`. |
| `log_dir` | directory path | `$OMD_ROOT/var/coshsh` or system temp dir | Directory where coshsh writes its rotating log files. Supports `%ENV_VAR%` substitution. |
| `log_level` | string (`info` or `debug`) | `info` | Controls console and file log verbosity. Can be overridden by the `--default-log-level` CLI flag. |
| `pid_dir` | directory path | system temp dir | Default PID-file directory for all recipes that do not specify their own `pid_dir`. Supports `%ENV_VAR%` substitution. |
| `backup_count` | integer | `2` | Number of rotated log file backups to keep (passed to `RotatingFileHandler`). |

Any key defined in `[defaults]` that is not consumed by the generator is silently ignored. The `[defaults]` section does **not** participate in `isa` inheritance and does **not** supply fallback values to recipe, datasource, or datarecipient sections -- it is only read by the generator itself.

### 6.2 recipe_NAME section

A `[recipe_NAME]` section defines a single generation pipeline. The section name minus the `recipe_` prefix becomes the recipe's name (lowercased). All string values undergo `%ENV_VAR%` and `@MAPPING_NAME[key]` substitution during `Recipe.__init__()`.

| Key | Type | Default | Effect |
|-----|------|---------|--------|
| `objects_dir` | directory path | (none -- required if no `datarecipients` key) | Output directory for generated config files. Used by the implicit `datarecipient_coshsh_default`. If `datarecipients` is also set, both are accepted. A trailing `//` suppresses the `dynamic/` subdirectory. |
| `datasources` | comma-separated string | (required) | Ordered list of datasource names (referencing `[datasource_NAME]` sections) to collect data from. |
| `datarecipients` | comma-separated string | (implicit `datarecipient_coshsh_default` when only `objects_dir` is given) | List of datarecipient names. The special token `>>>` is a shorthand alias for `datarecipient_coshsh_default` — it is expanded during `Recipe.__init__()` before any datarecipient objects are created. This allows compact configs like `datarecipients = >>>,SIMPLESAMPLE` which expands to `datarecipient_coshsh_default,SIMPLESAMPLE`. When `>>>` (or `datarecipient_coshsh_default`) is present, the default datarecipient is auto-constructed with the recipe's `objects_dir`, `max_delta`, `max_delta_action`, and `safe_output` settings. |
| `classes_dir` | comma-separated directory paths | built-in `recipes/default/classes` | Directories to search for application, datasource, datarecipient, and monitoring-detail plugin classes. Directories named `catchall` are placed at the end of the search path. |
| `templates_dir` | comma-separated directory paths | built-in `recipes/default/templates` | Directories to search for Jinja2 template files. Catchall directories are placed last. |
| `classes_path` | (derived, read-only) | computed from `classes_dir` | The resolved list of class directories (internal use). Not normally set in config. |
| `templates_path` | (derived, read-only) | computed from `templates_dir` | The resolved list of template directories (internal use). Not normally set in config. |
| `max_delta` | string (`N` or `N:M`) | (empty -- no delta check) | Maximum allowed percentage change in hosts and applications between runs. Format `hosts_pct:apps_pct`. A negative value (e.g. `-10:-10`) only guards against shrinkage; a positive value guards against change in either direction. Passed to the default datarecipient. |
| `max_delta_action` | string (path or `git_reset_hard_and_clean`) | `None` | Action to execute when the delta threshold is exceeded. If set to an executable file path, that script is run in the `dynamic_dir`. The value `git_reset_hard_and_clean` triggers a `git reset --hard` followed by `git clean -f -d`. |
| `safe_output` | boolean string (`true`/`false`) | `false` | When `true` and `max_delta` is exceeded and the output directory is a git repo, automatically reverts via `git reset --hard` and `git clean -f -d`. Can be overridden by the `--safe-output` CLI flag. |
| `pid_dir` | directory path | from `[defaults]` or system temp dir | Directory for the PID lock file that prevents concurrent recipe runs. |
| `vaults` | comma-separated string | (none) | List of vault names (referencing `[vault_NAME]` sections) whose secrets become available for `@VAULT[key]` substitution in datasource/datarecipient parameters. |
| `filter` | string | (none) | Per-datasource filter expressions. Format: `DATASOURCE(filter_value)` where `DATASOURCE` is the datasource name and `filter_value` is passed to that datasource's `read()` method. Multiple filters are comma-separated: `filter = ds1(kaas),ds2(kees)`. The datasource name portion may be a regex pattern — if it does not match a datasource name literally, it is auto-anchored with `^...$` and tested against all datasource names. Direct name matches always take precedence over regex matches (two-pass resolution). The regex `(([^,^(^)]+)\((.*?)\))` parses each `name(value)` pair. |
| `git_init` | `yes` or `no` | `yes` | Whether the default datarecipient should initialize a git repository in the output directory on first run. Set to `no` to disable. |
| `log_file` | filename | (none) | Override the log filename for this recipe. Supports `%ENV_VAR%` substitution (e.g. `coshsh_%RECIPE_NAME%.log`). |
| `log_dir` | directory path | from `[defaults]` | Override the log directory for this recipe only. |
| `backup_count` | integer | from `[defaults]` | Override the log rotation backup count for this recipe. |
| `my_jinja2_extensions` | comma-separated string | (none) | Names of custom Jinja2 filter/test/global functions to load from a `my_jinja2_extensions` module on `sys.path`. Functions prefixed `is_` become tests, `filter_` become filters, `global_` become globals. |
| `isa` | string | (none) | Name of another `[recipe_...]` section to inherit keys from. See [section 6.9](#69-recipe-inheritance-via-isa). |
| `env_*` | string | (none) | Any key starting with `env_` sets an environment variable during `Recipe.__init__()`. The prefix `env_` is stripped and the remaining key is uppercased: `env_foo = bar` sets `os.environ["FOO"] = "bar"`. This happens early in recipe initialization (before datasources are created), so environment variables are available to datasource plugins, vault backends, and Jinja2 templates. Example: `env_mibdirs = /usr/share/snmp/mibs` sets `os.environ["MIBDIRS"]`. Values undergo the same `%ENV_VAR%` and `@MAPPING` substitution as all other recipe keys. |
| `force` | (injected at runtime) | from CLI `--force` flag | Not set in config -- injected by the generator. When `true`, datasources re-read even if cache is fresh. |

Recipe names also set automatic environment variables: `RECIPE_NAME` is the full name, and `RECIPE_NAME1`, `RECIPE_NAME2`, etc. are the underscore-split components (1-indexed). These can be referenced in config values as `%RECIPE_NAME%`, `%RECIPE_NAME1%`, etc.

Any key not listed above that does not start with `recipe_` is stored in `additional_recipe_fields` and forwarded to datasource/datarecipient constructors as `recipe_<key>`.

### 6.3 datasource_NAME section

Each `[datasource_NAME]` section defines one data source. The section name suffix (after `datasource_`) becomes the datasource's logical name within the recipe.

| Key | Type | Default | Effect |
|-----|------|---------|--------|
| `type` | string | (required) | Identifies which datasource plugin to load via `__ds_ident__`. |
| `name` | string | section name suffix | Logical name for the datasource instance. |
| `hostname_transform` | comma-separated string | (none) | Pipeline of hostname transformation operations applied left-to-right. See [§11](#11-hostname-transformations). |
| `filter` | string | (none) | Filter expression passed to the datasource's `read()` method. Plugin-specific semantics. |
| `recipe_*` | (any) | (none) | Any key starting with `recipe_` is forwarded from the recipe config to the datasource constructor and also exposed with the `recipe_` prefix stripped. |

Additional keys are plugin-specific (e.g. a CSV datasource might accept `dir`, `delimiter`; a database datasource might accept `hostname`, `username`, `password`). All string values undergo `%ENV_VAR%` and `@VAULT[key]` substitution before reaching the plugin constructor.

### 6.4 datarecipient_NAME section

Each `[datarecipient_NAME]` section defines one output target.

| Key | Type | Default | Effect |
|-----|------|---------|--------|
| `type` | string | (required) | Identifies which datarecipient plugin to load via `__dr_ident__`. |
| `name` | string | section name suffix | Logical name for the datarecipient instance. |
| `objects_dir` | directory path | from recipe `objects_dir` | Base directory for output files (the "dynamic_dir"). |
| `max_delta` | string (`N:M`) | (none) | Override the recipe-level max_delta for this recipient. Format: `hosts_pct:apps_pct`. |
| `safe_output` | boolean string | `false` | Enable git-based rollback when delta is exceeded. |
| `want_tool` | string | (none) | Only write config files rendered under this tool key (e.g. `"nagios"`, `"prometheus"`). If unset, write all tools. |
| `git_init` | `yes`/`no` | `yes` | Whether to auto-initialise a git repo in the output directory. |

### 6.5 vault_NAME section

Each `[vault_NAME]` section defines a secrets backend.

| Key | Type | Default | Effect |
|-----|------|---------|--------|
| `type` | string | (required) | Identifies which vault plugin to load via `__vault_ident__`. |
| `name` | string | section name suffix | Logical name for the vault. |

Additional keys are plugin-specific (e.g. `vault_pass` accepts `password_file`; `vault_naemon` accepts `vault_dir`). Vault sections are processed BEFORE datasource/datarecipient sections so that `@VAULT[key]` tokens in those sections can be resolved.

### 6.6 mapping_NAME section

A `[mapping_NAME]` section is a simple key-value lookup table. Keys and values are arbitrary strings.

```ini
[mapping_environments]
prod = production-monitoring.example.com
staging = staging-monitoring.example.com
dev = dev-monitoring.example.com
```

Values from mapping sections are referenced in other config values using the `@MAPPING_NAME[key]` syntax:

```ini
[datasource_cmdb]
hostname = @mapping_environments[prod]
```

### 6.7 prometheus_pushgateway section

The optional `[prometheus_pushgateway]` section enables metrics export after recipe runs.

| Key | Type | Default | Effect |
|-----|------|---------|--------|
| `url` | URL string | (none) | The Pushgateway endpoint URL (e.g. `http://localhost:9091`). |
| `job` | string | (none) | The Prometheus job label for pushed metrics. |

When configured, `Generator.run()` pushes object count and timing metrics to the Pushgateway after all recipes complete. Requires the optional `prometheus_client` Python package.

### 6.8 Variable substitution

Three substitution mechanisms are available in INI config values, evaluated at different times:

**1. `%ENV_VAR%` -- Environment variable substitution**

Any `%NAME%` token is replaced with the value of the environment variable `NAME`. Handled by `coshsh.util.substenv()` via `re.sub`. If the variable is not set, the token is left unchanged (for debugging visibility). Evaluated when each config value is consumed (datasource/datarecipient/vault constructor).

```ini
objects_dir = %OMD_ROOT%/var/coshsh/configs/objects
```

**2. `@VAULT[key]` -- Vault secret substitution**

Any `@VAULT[key]` token is replaced with the secret value stored under `key` in the recipe's vault(s). Handled by `recipe.substsecret()`. Evaluated AFTER vaults have been opened and read, but BEFORE datasource/datarecipient constructors run.

```ini
[datasource_cmdb]
password = @VAULT[cmdb_password]
```

**3. `@MAPPING_NAME[key]` -- Mapping table lookup**

Any `@mapping_name[key]` token is replaced with the value from the corresponding `[mapping_name]` INI section. Case-insensitive on the mapping name. Evaluated during `add_datasource`/`add_datarecipient`.

```ini
hostname = @mapping_environments[prod]
```

**Evaluation order:** `%ENV_VAR%` is resolved first (at each consumption point), then `@VAULT[key]` (during add_datasource/add_datarecipient), then `@MAPPING[key]` (same time as vault).

### 6.9 Recipe inheritance via isa

The `isa` key in a `[recipe_NAME]` section enables single-level inheritance from another recipe section. Any key defined in the parent but missing in the child is copied to the child at parse time.

```ini
[recipe_base]
classes_dir = /opt/coshsh/classes
templates_dir = /opt/coshsh/templates
objects_dir = /var/coshsh/configs

[recipe_production]
isa = recipe_base
objects_dir = /var/coshsh/configs/production
# Inherits classes_dir and templates_dir from recipe_base
# objects_dir is NOT inherited because it is defined locally
```

**Constraints:**
- One level deep only: if `recipe_base` itself has `isa`, that grandparent is NOT followed.
- The `isa` key itself is never copied to the child.
- No cycle detection (the single-level constraint makes cycles impossible to trigger).
- Inheritance is evaluated once at parse time; later programmatic changes are not retroactively inherited.

See also: [§10 Vault and Secrets Management](#10-vault-and-secrets-management)

---

## 7. Jinja2 Template System

### 7.1 Template discovery

`Recipe.__init__()` creates a Jinja2 `FileSystemLoader` with `self.templates_path` -- a list of directories searched in order. The Jinja2 `Environment` is stored as `recipe.jinja2.env`. When `Item.render_cfg_template()` needs a template, it calls `self.jinja2.env.get_template(template_name + ".tpl")`, which searches the directories in `templates_path` order and returns the first match.

The `templates_path` is constructed similarly to `classes_path`: recipe-specific `templates_dir` directories come first, followed by the built-in `recipes/default/templates` as a fallback. This means user templates override built-in ones with the same name.

The `jinja2.ext.do` extension is loaded by default (enabling the `{% do %}` statement in templates). `trim_blocks` is set to `True` to remove the first newline after block tags.

### 7.2 Template caching

A `template_cache` dict is created fresh at the start of each `recipe.render()` call. When `Item.render_cfg_template()` is called, it checks `template_cache[template_name]` before calling `jinja2.env.get_template()`. If the template was already loaded for a previous object in the same recipe, the cached parsed template is reused.

This means:
- Templates are parsed from disk once per recipe run, then reused for all objects.
- The cache is NOT shared across recipes -- each recipe gets its own.
- The cache is NOT persisted between Generator runs.

### 7.3 Built-in filters

All built-in filters are defined in `coshsh/jinja2_extensions.py` and registered in `Recipe.__init__()`.

| Filter | Signature | Description |
|--------|-----------|-------------|
| `re_sub` | `value \| re_sub(pattern, repl[, flags[, count]])` | Regex search-and-replace. `flags` is a string of characters: `i` (IGNORECASE), `m` (MULTILINE), `s` (DOTALL), etc. |
| `re_escape` | `value \| re_escape` | Escape regex metacharacters in the string. |
| `service` | `application \| service(service_description)` | Generate a Nagios `define service {}` block. See [§7.7](#77-service-filter-and-nagiosconf). |
| `host` | `host \| host` | Generate a Nagios `define host {}` block with the same two-tier NAGIOSCONF pattern as `service`. |
| `contact` | `contact \| contact` | Generate a Nagios `define contact {}` block with the same two-tier NAGIOSCONF pattern. |
| `custom_macros` | `obj \| custom_macros` | Render custom macro lines (prefixed with `_`) from `obj.custom_macros` and `obj.macros` dicts. |
| `rfc3986` | `text \| rfc3986` | Percent-encode a string into a `rfc3986://` URI. Used for dashboard action URLs. |
| `neighbor_applications` | `application \| neighbor_applications` | Return all applications sharing the same host (`application.host.applications`). |

### 7.4 Built-in tests

| Test | Signature | Description |
|------|-----------|-------------|
| `re_match` | `value is re_match(pattern[, flags])` | Returns `True` if the regex `pattern` matches `value` (uses `re.search`, not `re.match`). `flags` is a string of flag characters (`i`, `m`, `s`, etc.). |

Example in a template:
```jinja2
{% if application.type is re_match("oracle.*", "i") %}
...
{% endif %}
```

### 7.5 Built-in globals

| Global | Signature | Description |
|--------|-----------|-------------|
| `environ` | `environ(var[, default])` | Read environment variable `var` at render time. Returns `default` (or `""`) if not set. |

Example:
```jinja2
{{ environ("OMD_ROOT", "/opt/omd") }}/lib/nagios/plugins/check_http
```

### 7.6 Custom Jinja2 extensions

The recipe config key `my_jinja2_extensions` accepts a comma-separated list of function names. `Recipe.__init__()` imports each name from a module called `my_jinja2_extensions` (which must be importable, e.g. placed in the recipe's `classes_dir` which is added to `sys.path`) and registers it based on its prefix:

- `is_*` --> Jinja2 test (prefix stripped, e.g. `is_my_check` becomes test `my_check`)
- `filter_*` --> Jinja2 filter (prefix stripped, e.g. `filter_shorten` becomes filter `shorten`)
- `global_*` --> Jinja2 global (prefix stripped, e.g. `global_lookup` becomes global `lookup`)

```ini
[recipe_myrecipe]
my_jinja2_extensions = filter_shorten, is_my_check, global_lookup
```

### 7.7 Service filter and NAGIOSCONF

The `service` filter (`filter_service`) implements a two-tier output pattern central to coshsh's config-override model.

**Without NAGIOSCONF attributes:** A simple `define service {}` block is emitted containing the `service_description`, `contact_groups`, and custom macros.

**With NAGIOSCONF attributes:** When an application has `nagios_config_attributes` (MonitoringDetail type NAGIOSCONF) matching the `service_description`, the filter emits TWO definitions:

1. A **concrete service** containing the NAGIOSCONF attribute overrides (e.g. `max_check_attempts 5`) and a `use` directive pointing to a generated template.
2. A **template service** (`register 0`) containing the base `service_description`, `contact_groups`, and custom macros, named `{service_description}_{host_name}`.

This lets Nagios admins override individual service attributes per-host (via NAGIOSCONF MonitoringDetails from the datasource) without duplicating the entire service definition. The `host` and `contact` filters use the same pattern.

### 7.8 Template file naming

Template files use the `.tpl` extension. The filename (without `.tpl`) is referenced in `TemplateRule(template="filename")`. Common naming conventions:

- `os_<type>_default` -- Host OS templates (e.g. `os_linux_default.tpl`, `os_windows_default.tpl`)
- `app_<type>_<name>` -- Application templates (e.g. `app_oracle_default.tpl`)
- `host.tpl` -- Base host definition template
- `contact.tpl` -- Base contact definition template

The output config file is named `{template_name}.{suffix}` by default (e.g. `os_linux_default.cfg`). When `TemplateRule.unique_config` is set, the output filename is derived from unique_config + unique_attr values instead, enabling per-instance files (e.g. one `.cfg` per filesystem).

See also: [§5 MonitoringDetail Type Reference](#5-monitoringdetail-type-reference), [§12.2 Creating an application class plugin](#122-creating-an-application-class-plugin)

---

## 8. Output Directory Structure

### 8.1 dynamic vs static directories

The recipe's `objects_dir` is the root output directory. Within it, two subdirectories serve distinct purposes:

- **`dynamic/`** -- Contains ALL generated configuration files. This entire directory is recreated on every coshsh run: old files are deleted by `cleanup_target_dir()`, then new files are written by `output()`. Never hand-edit files here.
- **`static/`** -- Contains hand-maintained configuration files that coshsh does NOT touch. Templates, contacts, or other config that should persist across runs belong here.

When `safe_output` is enabled, the `dynamic/` directory is a git repository. On delta violations, `git reset --hard` + `git clean -f -d` reverts to the last committed state.

### 8.2 Host configuration files

Each host gets its own subdirectory under `dynamic/hosts/`:

```
dynamic/hosts/<host_name>/host.cfg        # Host definition
dynamic/hosts/<host_name>/os_linux_default.cfg  # OS template output
```

The `host.cfg` file is rendered from the host's template rules. The directory name is the host's `host_name` attribute.

### 8.3 Application configuration files

Application config files are written into the host's directory:

```
dynamic/hosts/<host_name>/<template_name>.cfg
dynamic/hosts/<host_name>/<unique_config>.cfg   # When TemplateRule.unique_config is set
```

For example, a filesystem-monitoring application with `unique_config = "app_%s_fs"` produces one file per filesystem:

```
dynamic/hosts/server01/app_slash_fs.cfg
dynamic/hosts/server01/app_data_fs.cfg
```

### 8.4 Group and contact directories

```
dynamic/hostgroups/hostgroup_<name>.cfg    # One file per hostgroup
dynamic/contacts/<contact_name>/contact.cfg  # Contact definitions
```

HostGroup overrides `write_config()` to write to the `hostgroups/` subdirectory instead of a per-host directory.

### 8.5 Filename conventions and sanitization

All output filenames pass through `coshsh.util.sanitize_filename()`:

1. Non-alphanumeric characters (except `.`, `-`, `_`) are replaced with `_`.
2. If the sanitized name differs from the original, a 4-character MD5 suffix (from the original name) is appended to prevent collisions. Two different original names that sanitize to the same string get distinct MD5 suffixes.
3. If the name is already clean, no suffix is added (preserving stable filenames).

Example: `check_http/ssl` becomes `check_http_ssl_a1b2.cfg`.

---

## 9. Delta / Cache Safety Mechanism

### 9.1 Object counting

The datarecipient counts objects at two points:

1. **`count_before_objects()`** -- Called before `cleanup_target_dir()`. Counts host directories and non-empty application files on disk via `count_objects()`. Stored as `self.old_objects = (hosts, apps)`.
2. **`count_after_objects()`** -- Called after `output()` has written all files. Same filesystem-level count. Stored as `self.new_objects = (hosts, apps)`.

The count is filesystem-based (not in-memory), measuring what was ACTUALLY written to disk.

### 9.2 Positive vs negative max_delta

`max_delta` is specified as `"hosts_pct:apps_pct"` (e.g. `"10:20"`). The sign controls which direction of change is guarded:

**Negative max_delta (e.g. `-20:-20`):** Only guards against SHRINKAGE. An increase of any size is accepted. This is the common safety mode: if a datasource suddenly returns far fewer hosts (e.g. database connectivity issue), coshsh blocks the output. But if new hosts appear, that is always safe. Triggers when: `delta < max_delta` (i.e. shrunk more than the threshold).

**Positive max_delta (e.g. `20:20`):** Guards against change in EITHER direction. Any change larger than the threshold (increase or decrease) is flagged. Triggers when: `abs(delta) > max_delta`.

### 9.3 max_delta_action options

When `too_much_delta()` returns True, the action depends on the `max_delta_action` configuration:

- **(not set)**: The delta violation is logged as a warning but output proceeds normally.
- **`git_reset_hard_and_clean`** or path to executable: If `safe_output` is enabled, triggers the git rollback. If a path is given, that script is executed in the dynamic_dir.

### 9.4 safe_output and git reset

When `safe_output = true` and the output directory is a git repository:

1. After `output()` completes, `count_after_objects()` runs.
2. `too_much_delta()` compares old vs new counts.
3. If the delta is too large, `git reset --hard` followed by `git clean -f -d` reverts the dynamic directory to the last committed state, effectively undoing the current run's output.
4. The datarecipient bootstraps the git repo on first run via `run_git_init()`, which creates a repo with two dummy commits to establish a valid baseline for `git reset`.

### 9.5 When to use and when to disable

**Use in production:** Enable `safe_output` + negative `max_delta` (e.g. `-30:-30`) to protect against datasource failures that return incomplete data. This prevents accidentally deleting monitoring configs for hosts that simply weren't read.

**Disable during development:** When iterating on datasource or application plugins, delta violations are expected. Set `max_delta` to a large value or omit it entirely.

**First run caveat:** When `count_before` is 0 (empty directory), delta is forced to 0 regardless of how many objects are written. See [§14.8](#148-max_delta-with-zero-baseline).

See also: [§6.2 recipe_NAME section](#62-recipe_name-section)

---

## 10. Vault and Secrets Management

### 10.1 Vault plugin discovery

Vault plugins are discovered through the same class factory mechanism as datasources. Plugin files must:
- Have filenames starting with `vault` (matching `class_file_prefixes = ["vault"]`)
- Define a `__vault_ident__(params)` function that returns a Vault subclass or `None`

The vault class factory is initialised by `recipe.init_vault_class_factory()` using the recipe's classpath.

### 10.2 @VAULT substitution

Any `@VAULT[key]` token in an INI config value is replaced with the corresponding secret from `recipe.vault_secrets`. The substitution is performed by `recipe.substsecret()` using regex matching on `@VAULT\[(.+?)\]`.

**Resolution order:**
1. `generator.read_cookbook()` processes `[vault_*]` sections first.
2. `recipe.add_vault()` instantiates the vault plugin, calls `vault.open()` and `vault.read()`.
3. All key-value pairs from the vault are stored in `recipe.vault_secrets`.
4. Only then are `[datasource_*]` and `[datarecipient_*]` sections processed.
5. During `add_datasource()` / `add_datarecipient()`, every `@VAULT[key]` token is replaced.

### 10.3 %ENV_VAR% substitution

Any `%NAME%` token is replaced with `os.environ["NAME"]`. Handled by `coshsh.util.substenv()` via `re.sub('%.*?%', substenv, value)`. If the environment variable is not set, the token is left unchanged (literal `%NAME%` remains in the value).

This substitution happens at multiple points: in datasource/datarecipient/vault constructors when processing their params.

### 10.4 @MAPPING_NAME substitution

`[mapping_NAME]` sections are key-value lookup tables. Any `@mapping_name[key]` token in a config value is replaced with the corresponding value from the mapping section. Case-insensitive on the mapping name.

Example:
```ini
[mapping_servers]
db = database.example.com

[datasource_cmdb]
hostname = @mapping_servers[db]
# resolves to: hostname = database.example.com
```

### 10.5 Built-in vault types

The built-in vault plugins are located in `recipes/default/classes/`. Check for `vault*.py` files. Common types include:

- **vault_pass**: Reads secrets from a password-store-compatible file. Config key: `password_file`.
- **vault_naemon**: Reads secrets from Naemon/Nagios-format vault files. Config key: `vault_dir`.

Custom vault plugins can be placed in the recipe's `classes_dir` to add support for HashiCorp Vault, AWS Secrets Manager, or any other backend.

### 10.6 Recipe-level secret resolution

`recipe.substsecret(value)` performs the `@VAULT[key]` replacement. It is called automatically during `add_datasource()` and `add_datarecipient()` for every string parameter value. The method iterates `self.vault_secrets` (a flat dict populated by all vaults in the recipe) and replaces matching tokens.

**Critical timing constraint:** Vaults MUST be loaded (via `add_vault()`) BEFORE datasources and datarecipients. This is enforced by `generator.read_cookbook()` which processes vault sections first. If vault loading fails, unresolved `@VAULT[key]` tokens will be passed as literal strings to plugin constructors, likely causing authentication failures.

See also: [§6.8 Variable substitution](#68-variable-substitution)

---

## 11. Hostname Transformations

### 11.1 strip_domain

Removes everything after the first dot. `server01.example.com` becomes `server01`. Skipped for bare IP addresses (detected via `socket.inet_aton()`).

### 11.2 to_lower / to_upper

`to_lower` lowercases the entire hostname. `to_upper` uppercases it. Applied to the result of the previous transform in the pipeline.

### 11.3 append_domain

Resolves the short hostname to its FQDN via `socket.getfqdn()`. If DNS resolution fails, the hostname is left unchanged.

### 11.4 resolve_ip

Reverse-resolves an IP address to a hostname via `socket.gethostbyaddr()`. If the input is not an IP or resolution fails, the hostname is left unchanged.

### 11.5 resolve_dns

Forward-resolves the hostname to its FQDN via `socket.getfqdn()`. Similar to `append_domain` but may produce different results depending on DNS configuration.

### 11.6 Configuration and execution order

Configured via the `hostname_transform` key in a `[datasource_NAME]` section:

```ini
[datasource_cmdb]
type = csv
hostname_transform = strip_domain, to_lower
```

Operations are parsed as a comma-separated list and executed left-to-right. Order matters: `strip_domain,to_lower` first removes the domain suffix then lowercases, which differs from `to_lower,strip_domain` when the domain contains uppercase characters.

The transform is applied by calling `datasource.transform_hostname(hostname)` inside the datasource's `read()` method, typically before creating Host objects.

See also: [§6.3 datasource_NAME section](#63-datasource_name-section)

---

## 12. Plugin Authoring Guide

### 12.1 Creating a datasource plugin

**Step 1: Create the plugin file** `datasource_mydatasource.py` in your recipe's `classes_dir`:

```python
import coshsh
from coshsh.datasource import Datasource
from coshsh.host import Host
from coshsh.application import Application
from coshsh.monitoringdetail import MonitoringDetail
from coshsh.util import compare_attr

def __ds_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "mydatasource"):
        return MyDatasource

class MyDatasource(coshsh.datasource.Datasource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dir = kwargs.get("dir", ".")

    def open(self, **kwargs):
        pass  # Open connections, files, etc.

    def read(self, filter=None, objects={}, **kwargs):
        self.objects = objects
        # Create a host
        hostdata = {
            'host_name': 'myserver01',
            'address': '10.0.0.1',
            'type': 'server',
            'os': 'linux',
            'hardware': 'vmware',
            'virtual': 'vs',
            'notification_period': '7x24',
        }
        self.add('hosts', coshsh.host.Host(hostdata))
        # Create an application on that host
        appdata = {
            'host_name': 'myserver01',
            'name': 'myapp',
            'type': 'myapptype',
        }
        self.add('applications', coshsh.application.Application(appdata))

    def close(self):
        pass  # Clean up connections
```

**Step 2: Configure the recipe INI:**

```ini
[datasource_myds]
type = mydatasource
dir = /path/to/data

[recipe_myrecipe]
classes_dir = /path/to/my/classes
templates_dir = /path/to/my/templates
objects_dir = /var/coshsh/output
datasources = myds
```

### 12.2 Creating an application class plugin

**Step 1: Create the plugin file** `app_myapptype.py`:

```python
import coshsh
from coshsh.application import Application
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr

def __mi_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "myapptype"):
        return MyApp

class MyApp(coshsh.application.Application):
    template_rules = [
        TemplateRule(
            template="app_myapptype_default",
        ),
        TemplateRule(
            needsattr="filesystems",
            template="app_myapptype_fs",
            unique_attr="path",
            unique_config="app_myapptype_%s_fs",
        ),
    ]

    def __init__(self, params={}):
        super().__init__(params)
        self.port = params.get("port", 8080)
```

**Step 2: Create the template file** `app_myapptype_default.tpl`:

```
{{ application | service("myapp_check") }}
  host_name                       {{ application.host_name }}
  use                             app_myapptype_default
  check_command                   check_myapp!{{ application.port }}
}
```

**Step 3: Template with list-type MonitoringDetail** `app_myapptype_fs.tpl`:

```
{% for fs in application.filesystems %}
{{ application | service("myapp_fs_" + fs.path) }}
  host_name                       {{ application.host_name }}
  use                             app_myapptype_fs
  check_command                   check_disk!{{ fs.warning }}!{{ fs.critical }}!{{ fs.path }}
}
{% endfor %}
```

### 12.3 Creating a MonitoringDetail plugin

**Scalar type example** (`detail_mylogin.py`):

```python
import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "MYLOGIN":
        return MonitoringDetailMyLogin

class MonitoringDetailMyLogin(coshsh.monitoringdetail.MonitoringDetail):
    property = "mylogin"        # attribute name on parent object
    property_type = str          # scalar: parent.mylogin = this_object

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.username = params["monitoring_0"]
        self.password = params["monitoring_1"]
```

After resolution: `application.mylogin.username`, `application.mylogin.password`.

**List type example** (`detail_mydisk.py`):

```python
import coshsh
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "MYDISK":
        return MonitoringDetailMyDisk

class MonitoringDetailMyDisk(coshsh.monitoringdetail.MonitoringDetail):
    property = "mydisks"         # attribute name on parent object
    property_type = list          # list: parent.mydisks.append(this_object)
    unique_attribute = "mount"   # enables per-instance config files

    def __init__(self, params):
        self.monitoring_type = params["monitoring_type"]
        self.mount = params["monitoring_0"]
        self.warning = params.get("monitoring_1", "10")
        self.critical = params.get("monitoring_2", "5")
```

After resolution: `application.mydisks` is a list of MonitoringDetailMyDisk objects.

### 12.4 Creating a vault plugin

```python
import coshsh
from coshsh.vault import Vault
from coshsh.util import compare_attr

def __vault_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "my_vault"):
        return MyVault

class MyVault(Vault):
    def __init__(self, **params):
        super().__init__(**params)
        self.vault_path = params.get("vault_path")
        self._data = {}

    def open(self, **kwargs):
        pass  # Connect to vault backend

    def read(self, **kwargs):
        # Read secrets and populate self._data
        # Example: read from a simple key=value file
        with open(self.vault_path) as f:
            for line in f:
                if '=' in line:
                    k, v = line.strip().split('=', 1)
                    self._data[k.strip()] = v.strip()
        return self._data

    def get(self, key):
        return self._data.get(key)

    def getall(self):
        return self._data
```

### 12.5 Creating a custom Jinja2 extension

**Step 1: Create `my_jinja2_extensions.py`** in the recipe's `classes_dir`:

```python
import re

def filter_truncate(s, length=80):
    """Truncate a string to the given length."""
    return s[:length] if len(s) > length else s

def is_valid_ip(s):
    """Test if a string is a valid IPv4 address."""
    parts = s.split('.')
    return len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)

def global_site_name():
    """Return the monitoring site name."""
    return "production-monitoring"
```

**Step 2: Configure in recipe INI:**

```ini
[recipe_myrecipe]
my_jinja2_extensions = filter_truncate, is_valid_ip, global_site_name
```

**Step 3: Use in templates:**

```jinja2
{{ application.description | truncate }}
{% if application.address is valid_ip %}...{% endif %}
{{ site_name() }}
```

### 12.6 Full recipe with vault integration

```ini
[defaults]
log_dir = /var/log/coshsh
pid_dir = /var/run/coshsh

[vault_secrets]
type = my_vault
vault_path = /etc/coshsh/secrets.conf

[mapping_environments]
prod = production-db.example.com
staging = staging-db.example.com

[datasource_cmdb]
type = mydatasource
hostname = @mapping_environments[prod]
username = coshsh_reader
password = @VAULT[cmdb_password]
hostname_transform = strip_domain, to_lower

[datasource_details]
type = csv
dir = %DATA_DIR%/monitoring_details

[datarecipient_nagios]
type = datarecipient_coshsh_default
objects_dir = %OMD_ROOT%/var/coshsh/configs/production
max_delta = -30:-30
safe_output = true
want_tool = nagios

[recipe_production]
classes_dir = /opt/coshsh/classes/production, /opt/coshsh/classes/shared
templates_dir = /opt/coshsh/templates/production, /opt/coshsh/templates/shared
objects_dir = %OMD_ROOT%/var/coshsh/configs/production
datasources = cmdb, details
datarecipients = nagios
vaults = secrets
my_jinja2_extensions = filter_truncate, is_valid_ip
```

See also: [§4 Plugin / Extension System](#4-plugin--extension-system), [§6 INI Configuration File Reference](#6-ini-configuration-file-reference)

---

## 13. Test Infrastructure Guide

### 13.1 CommonCoshshTest base class

All coshsh tests inherit from `CommonCoshshTest` (defined in `tests/common_coshsh_test.py`), which extends `unittest.TestCase`.

Key features of `CommonCoshshTest`:
- **`setUp()`**: Resets ALL class_factory lists to `[]` (Application, MonitoringDetail, Contact, Datasource, Datarecipient) to prevent cross-test contamination. Changes working directory to the tests directory. Creates a fresh `Generator` instance.
- **`tearDown()`**: Removes generated objects directories (only if they are under the tests directory). Restores the original working directory.
- **`setUpConfig(configfile, default_recipe, ...)`**: Calls `generator.set_default_log_level()` then `generator.read_cookbook()`.
- **`setUpObjectsDir()`**: Removes and recreates the `_objectsdir` directory.

**WHY class_factory reset:** The class_factory is a mutable class-level list. Without resetting it between tests, plugins registered by one test would leak into subsequent tests, causing unpredictable ident function matches.

### 13.2 Test recipe fixture layout

Each test recipe lives under `tests/recipes/<testname>/`:

```
tests/recipes/test10/
├── classes/
│   ├── datasource_simplesample.py   # Test datasource plugin
│   ├── app_db_mysql.py              # Application class plugin
│   └── detail_custom.py             # Custom detail type (optional)
└── templates/
    └── app_db_mysql_default.tpl     # Jinja2 template
```

The cookbook config file is typically in `tests/etc/coshsh.cfg` (shared) or a test-specific `.cfg` file.

### 13.3 Setup and cleanup patterns

**Pattern 1: Class-level config attributes** (preferred for simple tests):

```python
class CoshshTest(CommonCoshshTest):
    _configfile = "etc/coshsh.cfg"
    _objectsdir = "./var/objects/test10"
```

When `_configfile` is set, `setUp()` automatically calls `setUpConfig()`. When `_objectsdir` is set, `setUp()` automatically calls `setUpObjectsDir()`.

**Pattern 2: Manual setup in test method:**

```python
def test_something(self):
    self.setUpConfig("etc/coshsh.cfg", "test10")
    recipe = self.generator.get_recipe("test10")
    # ... test logic ...
```

### 13.4 Asserting on generated files

After running the pipeline, assert on the generated output:

```python
# Check file existence
self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/myhost/host.cfg"))

# Check file content
with open("var/objects/test10/dynamic/hosts/myhost/app_mysql_default.cfg") as f:
    content = f.read()
self.assertIn("check_command", content)
self.assertIn("check_mysql", content)

# Check object counts
self.assertEqual(len(recipe.objects["hosts"]), 5)
self.assertEqual(len(recipe.objects["applications"]), 10)
```

### 13.5 Testing datasource plugins

Pattern: create a Generator, read the cookbook, get the datasource, manually add objects, then verify:

```python
def test_datasource_reads_hosts(self):
    self.setUpConfig("etc/coshsh.cfg", "test3")
    recipe = self.generator.get_recipe("test3")
    recipe.collect()
    self.assertTrue("test_host_0" in recipe.objects["hosts"])
```

Or inject objects manually via the datasource:

```python
def test_manual_object_creation(self):
    self.setUpConfig("etc/coshsh.cfg", "test10")
    ds = self.generator.get_recipe("test10").get_datasource("csv10.1")
    ds.objects = self.generator.get_recipe("test10").objects
    ds.add("hosts", coshsh.host.Host({
        'host_name': 'myhost', 'address': '10.0.0.1',
        'type': 'server', 'os': 'linux', ...
    }))
    self.assertTrue("myhost" in self.generator.get_recipe("test10").objects["hosts"])
```

### 13.6 Testing application class plugins

**Complete runnable example** (model your tests on this pattern):

```python
import os
import coshsh
from tests.common_coshsh_test import CommonCoshshTest


class CoshshTest(CommonCoshshTest):

    def test_mysql_application_with_port_detail(self):
        # Step 1: Set up the generator with a cookbook
        self.setUpConfig("etc/coshsh.cfg", "test10")
        recipe = self.generator.get_recipe("test10")
        ds = recipe.get_datasource("csv10.1")
        ds.objects = recipe.objects

        # Step 2: Create a host
        ds.add("hosts", coshsh.host.Host({
            'host_name': 'dbserver01',
            'address': '10.0.0.100',
            'type': 'Server',
            'os': 'Red Hat 6.0',
            'hardware': 'vmware',
            'virtual': 'vs',
            'notification_period': '7x24',
            'location': 'datacenter1',
            'department': 'dba',
        }))

        # Step 3: Create an application (type "mysql" triggers app_db_mysql.py)
        ds.add("applications", coshsh.application.Application({
            'name': 'production_db',
            'type': 'mysql',
            'component': '',
            'version': '',
            'patchlevel': '',
            'host_name': 'dbserver01',
            'check_period': '7x24',
        }))

        # Step 4: Add a MonitoringDetail (PORT detail)
        ds.add("details", coshsh.monitoringdetail.MonitoringDetail({
            'host_name': 'dbserver01',
            'name': 'production_db',
            'type': 'mysql',
            'monitoring_type': 'PORT',
            'monitoring_0': 3307,
        }))

        # Step 5: Verify objects were created
        self.assertIn("dbserver01", recipe.objects["hosts"])
        self.assertIn("dbserver01+production_db+mysql",
                       recipe.objects["applications"])

        # Step 6: Run assemble to link details to applications
        recipe.assemble()

        # Step 7: Verify application attributes
        host = recipe.objects["hosts"]["dbserver01"]
        app = host.applications[0]
        self.assertTrue(hasattr(app, "port"))
        self.assertEqual(app.port, 3307)
```

### 13.7 Running the test suite

```bash
# Run all tests
pytest tests/ -q

# Run a single test file
pytest tests/test_application_mysql.py -q

# Run a single test method
pytest tests/test_application_mysql.py::CoshshTest::test_create_server -v

# Expected output format:
# 97 passed, 1 failed in 31.56s
```

The test suite runs from the repository root. All paths in cookbook configs are relative to the `tests/` directory (where `setUp()` changes to).

---

## 14. Edge Cases and Gotchas

### 14.1 Fingerprint collision

**Observed behaviour:** When two objects have the same `fingerprint()` return value, the later one silently overwrites the earlier one in `recipe.objects[type][fingerprint]`. No warning is logged.

**Reason:** This is by design for deduplication. If the same host appears in two datasources, the second read silently replaces the first, ensuring each logical entity exists exactly once.

**Gotcha for callers:** If your datasource creates objects with insufficiently unique fingerprints, data loss occurs silently. For example, two different applications on the same host with the same `name` and `type` will collide because `Application.fingerprint()` returns `host_name + "+" + name + "+" + type`. Always verify that your fingerprint components are unique within the expected scope.

### 14.2 Ident function priority

**Observed behaviour:** `get_class()` iterates the `class_factory` list in reverse order and returns the first match. This means the last-registered class wins.

**Reason:** `init_class_factory()` processes classpath directories in reverse, so user-supplied directories (which appear first in classpath) are appended last to `class_factory`. Reversing in `get_class()` means user classes are checked before defaults.

**Gotcha for callers:** If two ident functions in the same directory both match the same params, the one loaded later (alphabetical file order within the directory) wins because it was appended to `class_factory` later. To guarantee priority, ensure your ident function is more specific (returns `None` for cases the other should handle) rather than relying on file naming order.

### 14.3 Catchall directory ordering

**Observed behaviour:** Directories containing "catchall" in their path are always appended to the END of `classpath`, regardless of where they appear in the `classes_dir` config value. Their ident functions typically match broadly (e.g. `re.match(".*", params["type"])`).

**Reason:** Catchall directories provide fallback/default implementations. They must be lowest priority so that specific user plugins always win.

**Gotcha for callers:** If you accidentally name a directory "catchall" when it contains specific (not fallback) plugins, those plugins will have lowest priority and may never match because a more specific plugin in a non-catchall directory matches first. Avoid the word "catchall" in directory names unless the directory truly contains fallback plugins.

### 14.4 DatasourceNotAvailable handling

**Observed behaviour:** When a datasource raises `DatasourceNotAvailable`, `DatasourceNotCurrent`, or `DatasourceNotReady` during `collect()`, the recipe sets `data_valid = False`, logs the error, and **aborts the entire collection phase** -- no further datasources are read. `collect()` returns `False`, and the recipe's pipeline stops (no assemble, render, or output).

**Reason:** Partial data is considered dangerous. If one datasource fails, the merged result is incomplete, which could cause the output phase to delete config for hosts/applications that simply weren't read. Aborting early is safer than producing partial output.

**Gotcha for callers:** There is no "skip this datasource and continue" mode. If you have an optional datasource that may be unavailable, you must handle the unavailability inside the datasource plugin itself (e.g. return empty data instead of raising the exception).

### 14.5 Jinja2 UndefinedError and render_errors

**Observed behaviour:** When a Jinja2 template references an undefined variable or raises any exception during rendering, `Item.render_cfg_template()` catches the exception, logs it, and increments `self.render_errors`. The object's remaining templates continue to render. The recipe continues with other objects.

**Reason:** One broken template or one object with missing attributes should not prevent the entire monitoring configuration from being generated. Partial output (with the broken object's config missing) is better than no output at all.

**Gotcha for callers:** The `render_errors` counter is aggregated at the recipe level. After `recipe.render()`, check `recipe.render_errors > 0` to detect problems. The generated config will be incomplete for objects that had rendering errors -- their config files will simply be absent from the output directory. There is no automatic retry or fallback template.

### 14.6 Circular isa inheritance

**Observed behaviour:** The `isa` mechanism in `CoshshConfigParser` does NOT detect cycles. If `recipe_a` has `isa = recipe_b` and `recipe_b` has `isa = recipe_a`, the parser does not enter an infinite loop because inheritance is one-level deep: it copies keys from the named parent section but does not follow the parent's own `isa` key.

**Reason:** The single-level depth constraint makes true cycles impossible to trigger. The `isa` key itself is explicitly excluded from being copied (`not key == "isa"` guard).

**Gotcha for callers:** While circular `isa` does not crash, it also does not do what you might expect. In the `A -> B -> A` case, `A` gets keys from `B`, and `B` gets keys from `A`, but neither gets grandparent keys. Multi-level inheritance (A -> B -> C where A should inherit from both B and C) is not supported. Flatten your hierarchy or duplicate keys explicitly.

### 14.7 Vault backend unreachable

**Observed behaviour:** When `vault.open()` or `vault.read()` raises an exception during `recipe.add_vault()`, the vault is not loaded into `recipe.vault_secrets`. If any `@VAULT[key]` tokens remain unresolved in subsequent datasource/datarecipient parameters, those parameters will contain literal `@VAULT[key]` strings, likely causing authentication failures or misconfiguration.

**Reason:** Vault resolution happens early (before datasource instantiation) precisely to fail fast. If a vault is unreachable, the generator logs the error and may remove the entire recipe from execution (depending on the exception type).

**Gotcha for callers:** Always test vault connectivity before production runs. If using `safe_output`, the git rollback will preserve the last known-good config. Without `safe_output`, an unreachable vault can result in datasources receiving placeholder credentials and potentially producing empty or incorrect output.

### 14.8 max_delta with zero baseline

**Observed behaviour:** When `count_before` is 0 (fresh install, empty output directory), the delta percentage calculation catches the `ZeroDivisionError` and sets `delta_hosts = 0` and `delta_services = 0`. This means **any number of new objects is accepted** on the first run, regardless of `max_delta` settings.

**Reason:** On a fresh install, going from 0 to N objects is expected and should not be blocked. The percentage-based delta is meaningless when the baseline is zero.

**Gotcha for callers:** After the first run populates the output directory, subsequent runs will have a non-zero baseline and `max_delta` will take effect. If your first run produces an unexpectedly small number of objects (e.g. due to a datasource misconfiguration), that small number becomes the baseline, and a corrected second run producing many more objects could trigger `max_delta`. Consider running without `max_delta` on the initial deployment, then enabling it once the baseline is established.

### 14.9 property_flat gotcha

**Observed behaviour:** When a `MonitoringDetail` subclass declares `property_flat = True` with a scalar `property_type` (e.g. `str`, `int`), `resolve_monitoring_details()` stores the **value** of the detail's property attribute on the parent object, not the detail object itself. For example, with `MonitoringDetailRole` (`property = "role"`, `property_type = str`, `property_flat = True`), after resolution `application.role` is a plain string like `"webserver"`, not a `MonitoringDetailRole` instance.

**Reason:** This is intentional. Scalar details like ROLE, DEPTH, and TAG are simple values that don't need the overhead of a full detail object. The `property_flat` flag makes templates simpler: `{{ application.role }}` works directly instead of requiring `{{ application.role.role }}`.

**Gotcha for callers:** Because the detail object is not stored, you cannot access other attributes of the detail (like `monitoring_type`) through the parent object. Code like `application.role.monitoring_type` will raise an `AttributeError` because `application.role` is a string, not a `MonitoringDetailRole`. If you need access to the full detail object, do not use `property_flat = True`. Similarly, for list-typed details with `property_attr`, `application.tags` is a list of strings (not detail objects), so `application.tags[0].monitoring_type` will also fail.

---

## 15. Prometheus Pushgateway Integration

### 15.1 Metrics emitted and timing

When a Prometheus Pushgateway is configured, `Generator.run()` pushes metrics after each recipe completes. Metrics include:

- Object counts (hosts, applications, contacts, etc.) per recipe
- Timing information for each pipeline phase
- Render error counts

Metrics are pushed using the `prometheus_client` library's `push_to_gateway()` function. The library is optional -- if not installed, metrics are silently skipped.

### 15.2 Configuration

```ini
[prometheus_pushgateway]
address = http://localhost:9091
job = coshsh
```

The `address` key specifies the Pushgateway URL. The `job` key sets the Prometheus job label. Both are read by `generator.read_cookbook()` and stored via `generator.add_pushgateway()`.

### 15.3 Relationship to recipe execution

Metrics are pushed at the end of each recipe's pipeline execution within `Generator.run()`. If a recipe fails (e.g. `collect()` returns `False`), partial metrics may still be pushed. If the Pushgateway is unreachable, a warning is logged but the recipe execution is not affected.

---

## 16. OMD Integration

### 16.1 What OMD is and where coshsh fits

OMD (Open Monitoring Distribution) is a pre-packaged monitoring platform that bundles Nagios/Naemon/Icinga with add-ons (Thruk, Check_MK, PNP4Nagios, etc.) into site-based installations. Each OMD site runs under its own user with a home directory at `/omd/sites/<sitename>/`.

coshsh fits into OMD as the configuration generator: it reads inventory data from external sources and writes Nagios/Naemon-format `.cfg` files into the site's configuration directory. The monitoring core then reads these files.

### 16.2 OMD-specific path conventions

Within an OMD site, paths use `%OMD_ROOT%` (resolved to `/omd/sites/<sitename>`):

| Path | Purpose |
|------|---------|
| `%OMD_ROOT%/etc/coshsh/conf.d/` | Cookbook config files |
| `%OMD_ROOT%/var/coshsh/configs/<recipe>/` | Generated config output (`objects_dir`) |
| `%OMD_ROOT%/share/coshsh/recipes/<recipe>/classes/` | Recipe-specific class plugins |
| `%OMD_ROOT%/share/coshsh/recipes/<recipe>/templates/` | Recipe-specific Jinja2 templates |
| `%OMD_ROOT%/var/log/coshsh/` | Log files |
| `%OMD_ROOT%/tmp/coshsh/` | PID files |

### 16.3 Default recipe directory layout

A typical OMD site with one recipe called `production`:

```
/omd/sites/mysite/
├── etc/coshsh/conf.d/
│   └── production.cfg          # Cookbook INI file
├── share/coshsh/recipes/production/
│   ├── classes/                 # Plugin .py files
│   │   ├── datasource_cmdb.py
│   │   ├── app_oracle.py
│   │   └── detail_custom.py
│   └── templates/               # Jinja2 .tpl files
│       ├── app_oracle_default.tpl
│       └── os_linux_default.tpl
└── var/coshsh/configs/production/
    ├── dynamic/                 # Generated output
    │   ├── hosts/
    │   ├── hostgroups/
    │   └── contacts/
    └── static/                  # Hand-maintained config
```

### 16.4 Running coshsh-cook inside OMD

```bash
# As the OMD site user:
OMD[mysite]:~$ coshsh-cook --cookbook etc/coshsh/conf.d/production.cfg --recipe production

# Or with environment variables already set by OMD:
OMD[mysite]:~$ coshsh-cook --cookbook %OMD_ROOT%/etc/coshsh/conf.d/production.cfg
```

The `coshsh-cook` script is the CLI entry point. It instantiates a `Generator`, calls `read_cookbook()`, then `run()`. Within OMD, `%OMD_ROOT%` is automatically available as an environment variable.

---

## 17. SNMP Trap Configuration via check_logfiles

### 17.1 Use case and context

coshsh can generate `check_logfiles` configuration for SNMP trap monitoring. In this use case, SNMP trap definitions (from `.snmptt` files parsed from MIBs) are transformed into `check_logfiles` config files that monitor trap log files for specific OIDs and generate Nagios service alerts.

### 17.2 Relevant datarecipient and template pattern

The SNMP trap use case typically uses a specialised datarecipient (type `snmp_exporter` or similar) that writes `check_logfiles` `.cfg` files instead of standard Nagios host/service configs. The datasource reads `.snmptt` files and creates objects representing trap definitions.

### 17.3 The testsnmptt test recipe

The `tests/recipes/testsnmptt/` directory contains a complete working example:

- `classes/datasource_snmptt.py` -- Datasource that reads `.snmptt` files from `data/snmptt/`
- `data/snmptt/*.snmptt` -- Sample SNMP trap translation files (e.g. `SM10-R2-MIB.snmptt`)
- Generated output in `tests/var/objects/testsnmptt/`
- Reference output in `tests/etc/check_logfiles/snmptt/*.cfg`

This test recipe can be used as a reference for implementing SNMP trap monitoring configuration generation.

---

## Appendix A: Quick Reference — All Config Keys

| Section | Key | Type | Default |
|---------|-----|------|---------|
| `[defaults]` | `log_dir` | path | (none) |
| `[defaults]` | `pid_dir` | path | system temp |
| `[defaults]` | `backup_count` | int | (none) |
| `[recipe_*]` | `classes_dir` | comma-sep paths | built-in |
| `[recipe_*]` | `templates_dir` | comma-sep paths | built-in |
| `[recipe_*]` | `objects_dir` | path | (required) |
| `[recipe_*]` | `max_delta` | `N:M` | (none) |
| `[recipe_*]` | `max_delta_action` | string/path | (none) |
| `[recipe_*]` | `safe_output` | bool | `false` |
| `[recipe_*]` | `pid_dir` | path | from defaults |
| `[recipe_*]` | `datasources` | comma-sep | (required) |
| `[recipe_*]` | `datarecipients` | comma-sep | `>>>` (default) |
| `[recipe_*]` | `vaults` | comma-sep | (none) |
| `[recipe_*]` | `filter` | string | (none) |
| `[recipe_*]` | `git_init` | `yes`/`no` | `yes` |
| `[recipe_*]` | `log_file` | filename | (none) |
| `[recipe_*]` | `log_dir` | path | from defaults |
| `[recipe_*]` | `my_jinja2_extensions` | comma-sep | (none) |
| `[recipe_*]` | `isa` | string | (none) |
| `[recipe_*]` | `env_*` | string | (none) |
| `[datasource_*]` | `type` | string | (required) |
| `[datasource_*]` | `name` | string | section suffix |
| `[datasource_*]` | `hostname_transform` | comma-sep | (none) |
| `[datasource_*]` | `filter` | string | (none) |
| `[datarecipient_*]` | `type` | string | (required) |
| `[datarecipient_*]` | `name` | string | section suffix |
| `[datarecipient_*]` | `objects_dir` | path | from recipe |
| `[datarecipient_*]` | `max_delta` | `N:M` | (none) |
| `[datarecipient_*]` | `safe_output` | bool | `false` |
| `[datarecipient_*]` | `want_tool` | string | (none) |
| `[datarecipient_*]` | `git_init` | `yes`/`no` | `yes` |
| `[vault_*]` | `type` | string | (required) |
| `[vault_*]` | `name` | string | section suffix |
| `[mapping_*]` | *(any key)* | string | (user-defined) |
| `[prometheus_pushgateway]` | `address` | URL | (none) |
| `[prometheus_pushgateway]` | `job` | string | (none) |

---

## Appendix B: Quick Reference — All MonitoringDetail Types

| monitoring_type | property | property_type | Key params | Result attribute |
|----------------|----------|---------------|------------|------------------|
| `LOGIN` | `login` | str | monitoring_0=user, monitoring_1=pass | `.login.username`, `.login.password` |
| `LOGINSNMPV2` | `loginsnmpv2` | str | monitoring_0=community | `.loginsnmpv2.community`, `.loginsnmpv2.protocol` |
| `LOGINSNMPV3` | `loginsnmpv3` | str | monitoring_0..5=security params | `.loginsnmpv3.securityname`, etc. |
| `FILESYSTEM` | `filesystems` | list | monitoring_0=path, 1=warn, 2=crit | `.filesystems[].path`, `.warning`, `.critical` |
| `PORT` | `ports` | list | monitoring_0=port, 1=warn, 2=crit | `.ports[].port`, `.warning`, `.critical` |
| `INTERFACE` | `interfaces` | list | monitoring_0=name | `.interfaces[].name` |
| `DATASTORE` | `datastores` | list | monitoring_0=name, 1=warn, 2=crit | `.datastores[].name`, `.path` |
| `TABLESPACE` | `tablespaces` | list | monitoring_0=name, 1=warn, 2=crit | `.tablespaces[].name` |
| `URL` | `urls` | list | monitoring_0=url, 1=warn, 2=crit, 3=expect | `.urls[].url`, `.scheme`, `.hostname` |
| `TAG` | `tags` | list (flat) | monitoring_0=tag | `.tags` = list of strings |
| `ROLE` | `role` | str (flat) | monitoring_0=role | `.role` = string |
| `DEPTH` | `monitoring_depth` | int (flat) | monitoring_0=level | `.monitoring_depth` = int |
| `VOLUME` | `volumes` | list | monitoring_0=name, 1=warn, 2=crit | `.volumes[].name` |
| `PROCESS` | `processes` | list | monitoring_0=name, 1=warn, 2=crit, 3=alias | `.processes[].name` |
| `SOCKET` | `socket` | str | monitoring_0=socket | `.socket.socket` |
| `ACCESS` | `access` | str (flat) | monitoring_0=access | `.access` = string |
| `KEYVALUES` | `generic` | dict | monitoring_0=key1, 1=val1, 2=key2, 3=val2 | `.generic[key]` = value |
| `NAGIOSCONF` | `nagios_config_attributes` | list | monitoring_0=svc, 1=attr, 2=val | `.nagios_config_attributes[].name`, `.attribute`, `.value` |
| `CUSTOMMACRO` | `custom_macros` | dict | monitoring_0=key, monitoring_1=value | `.custom_macros[key]` = value |

---

## Appendix C: Class Factory Decision Tree

```
Caller creates object: Application(params)
    │
    ▼
Application.__init__(params) detects self.__class__ == Application (generic)
    │
    ▼
Application.get_class(params) called
    │
    ▼
Iterate class_factory list IN REVERSE
    │
    ├── For each entry [path, module, ident_func]:
    │     │
    │     ▼
    │   Call ident_func(params)
    │     │
    │     ├── Returns None → skip, try next
    │     │
    │     └── Returns SubClass → MATCH FOUND
    │           │
    │           ▼
    │         Return SubClass
    │
    └── No match found → Return None
          │
          ▼
        GenericApplication used (or error for Datasource/Datarecipient)

If SubClass returned:
    │
    ▼
self.__class__ = SubClass    (rebless)
    │
    ▼
self.__init__(params)        (re-invoke as the concrete class)
    │
    ▼
SubClass.__init__ runs → sets template_rules, custom attributes, etc.
```

**Key points:**
- `class_factory` is populated by `init_class_factory()` which walks classpath directories in reverse.
- User directories are checked first (highest priority) because of the double-reversal pattern.
- First match wins — if two ident functions both match, the one from the higher-priority directory takes precedence.
- The "rebless" pattern (`self.__class__ = SubClass`) mutates the object in-place rather than constructing a new one.

**Assemble-phase hook call sequence** (runs later, during `Recipe.assemble()`):

```
For each host:
    host.resolve_monitoring_details()
        ├── promote each detail → attribute on host
        └── host.wemustrepeat()           ← cross-detail reconciliation hook
    host.create_templates()               ← dynamic template rule hook
    host.create_hostgroups()              ← derived hostgroup hook
    host.create_contacts()                ← derived contact hook

For each application:
    app.host = recipe.objects['hosts'][app.host_name]
    app.resolve_monitoring_details()
        ├── promote each detail → attribute on app
        └── app.wemustrepeat()            ← cross-detail reconciliation hook
    app.create_templates()                ← dynamic template rule hook
    app.create_servicegroups()            ← service group hook
    app.create_contacts()                 ← derived contact hook

After all applications:
    Collect host.hostgroups → recipe.objects['hostgroups']
    (This is why app.wemustrepeat() can modify host.hostgroups)
```
