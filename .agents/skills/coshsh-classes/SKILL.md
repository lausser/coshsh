---
name: coshsh-classes
description: Write production-quality coshsh code — datasources (datasource_*.py), application/OS classes (app_*.py, os_*.py), monitoring details (detail_*.py), datarecipients (datarecipient_*.py), Jinja2 templates (.tpl), and cookbook (.cfg) configuration. Use whenever the user mentions coshsh, coshsh-cook, generating Nagios/Naemon/Icinga/Shinken/Prometheus configs from inventory/CMDB data, or any of these identifiers — `__ds_ident__`, `__mi_ident__`, `__dr_ident__`, `template_rules`, `TemplateRule`, `MonitoringDetail`, `DatasourceNotAvailable`, `coshsh.application.Application`, `coshsh.datasource.Datasource`. Also use when integrating NetBox/ServiceNow/custom CMDB/CSV/JSON/database with Nagios/Icinga/Naemon through coshsh, even without the word "coshsh" (e.g. "generate Nagios configs from our inventory database"). Framework by Gerhard Lausser at github.com/lausser/coshsh — load before writing any Python that imports `coshsh`.
---

# coshsh-classes

A skill for writing production-quality coshsh code. coshsh is a Python framework by Gerhard Lausser (github.com/lausser/coshsh) that generates monitoring configuration files (Nagios, Naemon, Icinga, Shinken, Prometheus targets, and arbitrary text formats) from inventory data via a plugin architecture of datasources, application/OS classes, monitoring details, Jinja2 templates, and datarecipients.

## The mental model: read this first

coshsh sees the world as **hosts** and the **applications** running on them. There are **no services in the input data**. Services emerge when an application gets matched to a class with `template_rules` that point to Jinja2 `.tpl` files. The `.tpl` files contain the actual `define service { ... }` blocks.

A run of `coshsh-cook --cookbook X.cfg --recipe Y` executes four phases:

1. **Collect.** Each datasource listed in the recipe (in order) has its `open()`, `read()`, `close()` called. Inside `read()` the datasource fetches raw inventory and instantiates `Host`, `Application`, `MonitoringDetail`, `Contact`, `ContactGroup` objects, registering them with `self.add('hosts', h)` etc. All datasources in a recipe share one object registry (`recipe.objects`), so a second datasource can enrich what a first one created.
2. **Assemble.** Raw `MonitoringDetail` objects are resolved and attached as structured attributes to their parent host/application (e.g. all `FILESYSTEM` details for one app become a list at `application.filesystems`). Each item's `wemustrepeat()` (if defined) runs. Each item's `template_rules` are evaluated to decide which `.tpl` files apply.
3. **Render.** Jinja2 renders each selected template against the item, producing a config string stored on the item.
4. **Output.** Each datarecipient gets the populated `recipe.objects` and writes the configs (the default writes one file per `(host, template)` under `objects_dir/dynamic/hosts/<host_name>/<template>.cfg`).

The whole framework is a plugin system glued by **identifier functions**:

| File prefix          | Identifier function     | Purpose                                                                 |
| -------------------- | ----------------------- | ----------------------------------------------------------------------- |
| `datasource_*.py`    | `__ds_ident__(params)`  | Returns the datasource class that handles a given `type=` value         |
| `app_*.py`, `os_*.py`| `__mi_ident__(params)`  | Returns the application/OS class that handles a given application `type` |
| `detail_*.py`        | (module-level constants)| Defines how a `monitoring_type=` value becomes a structured attribute   |
| `datarecipient_*.py` | `__dr_ident__(params)`  | Returns the datarecipient class for a given `type=` value               |

The `params` dict is the raw row from the data (for items) or the cookbook section contents (for datasources/datarecipients). coshsh walks every `classes_dir`, imports each module with the right prefix, calls its identifier, and the first non-`None` return wins. The `Application(row)` constructor then "re-blesses" the instance into the returned class so `a.__class__.__name__` is e.g. `Windows`, not `Application`.

## Mandatory conventions a pro never gets wrong

These rules separate amateur coshsh code from professional code. Internalize them before writing anything.

**File naming.** The prefix is not cosmetic — coshsh's class loader filters on it. `datasource_netbox.py`, `os_linux.py`, `app_oracle.py`, `detail_filesystem.py`, `datarecipient_prometheus.py`. Custom-named files are silently ignored.

**Identifier functions return the class, not an instance.** `return MyClass` — never `return MyClass()`. They take `params={}` and return `None` if they don't handle that type. The convention for matching is `coshsh.util.compare_attr("type", params, "...")` which supports regex; falling back to `params.get("type") == "..."` is fine for exact matches.

**Always `super().__init__(**kwargs)` (datasource) or `super().__init__(params)` (item) as the first line of `__init__`.** The base class wires up `self.objects`, the re-blessing mechanism, default attributes, and `monitoring_details = []`. Skipping it produces objects that look fine but break in obscure ways during assembly.

**Inside a datasource's `read()`, use `self.add(item_type_plural, instance)`** — `'hosts'`, `'applications'`, `'details'`, `'contacts'`, `'contactgroups'`, `'hostgroups'`. Don't mutate `self.objects` directly; `add` uses `instance.fingerprint()` as the key, which is what later phases expect.

**A host's minimum is `host_name` + `address`.** An application's minimum is `host_name` + `name` + `type`. A monitoring detail's minimum is `host_name` + `monitoring_type` + the `monitoring_0..N` slots that detail type expects. The `host_name` on an Application or Detail is the foreign key linking it to its Host — get it wrong and the item silently dangles.

**`name` vs `type` on an Application.** `type` is what `__mi_ident__` matches on (e.g. `windows2019`, `oracle`, `apache`). `name` is the role of that instance on the host (e.g. `os`, `billing_db`, `intranet`). The convention is `name='os'` for the operating system / firmware / appliance software. The fingerprint for an Application is roughly `host_name+name+type`, so two applications on one host with the same name+type collide. Use `name` to disambiguate (e.g. one Oracle host running two databases: `name='billing_db'` and `name='reporting_db'`, both `type='oracle'`).

**Application class `type` values are lowercased before `__mi_ident__` runs.** Match against lowercase patterns.

**Datasources raise specific exceptions.** `raise DatasourceNotAvailable` when the source can't be reached (network down, file missing). `raise DatasourceNotCurrent` when the source is reachable but has no changes since last run (lets coshsh skip regeneration). `raise DatasourceCorrupt` when the source returned malformed data. Generic `Exception` causes the whole recipe to abort with a stack trace and no graceful handling.

**Don't pass `None` values into item constructors.** A common failure mode: a CSV cell is empty, your code sets `params['alias'] = None`, the template renders `alias None` literally into the Nagios config. Strip `None`s before constructing: `params = {k: v for k, v in params.items() if v is not None}`.

**Every attribute on the dict passed to a constructor becomes an attribute on the object** and is available in templates as `{{ host.foo }}` or `{{ application.foo }}`. This is the primary way to surface data to templates — not via custom methods. Use clean attribute names; they appear verbatim in Jinja2.

**Hostgroup and contactgroup membership is set on the Host/Application, not on the group.** `h.hostgroups.append('linux_servers')` is the idiom. The hostgroup definition file is generated automatically. Same for `h.contact_groups` and `a.contact_groups`.

**Custom Nagios macros go in `h.macros` or `a.macros` as a dict.** Keys must start with `_` (Nagios convention). `h.macros = {'_LOCATION': 'dc1', '_SERIAL': 'X37HX'}` produces `_LOCATION dc1` and `_SERIAL X37HX` in the host definition.

**MonitoringDetail data goes in `monitoring_0`, `monitoring_1`, ... slots.** The slot meaning depends on `monitoring_type` and is defined by the matching `detail_*.py`. For example for `FILESYSTEM`: `monitoring_0` = path, `monitoring_1` = warning, `monitoring_2` = critical, `monitoring_3` = units. Look up the detail class to know the slot ordering.

**`add('details', md)` is the way.** Don't `application.monitoring_details.append(md)` from a datasource — the framework's `resolve_monitoring_details()` in the assemble phase looks at `recipe.objects['details']` and routes details to their parents using the `host_name`/`name`/`type` fields on the detail.

## Quick skeletons

A datasource:

```python
import logging
import coshsh
from coshsh.datasource import Datasource, DatasourceNotAvailable, DatasourceNotCurrent, DatasourceCorrupt
from coshsh.host import Host
from coshsh.application import Application
from coshsh.monitoringdetail import MonitoringDetail
from coshsh.util import compare_attr

logger = logging.getLogger('coshsh')

def __ds_ident__(params={}):
    if compare_attr("type", params, "mycmdb"):
        return MyCmdb
    return None

class MyCmdb(Datasource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.url = kwargs["url"]
        self.token = kwargs.get("token")

    def open(self):
        logger.info(f"opening datasource {self.name}")
        # connect, raise DatasourceNotAvailable on failure
        return True

    def read(self, filter=None, objects={}, force=False, **kwargs):
        for row in self._fetch_hosts():
            h = Host({
                'host_name': row['hostname'],
                'address':   row['ip'],
            })
            self.add('hosts', h)

            a = Application({
                'host_name': h.host_name,
                'name': 'os',
                'type': row['os'].lower(),
            })
            self.add('applications', a)
        return True

    def close(self):
        return True
```

An application/OS class:

```python
import coshsh
from coshsh.application import Application
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr

def __mi_ident__(params={}):
    if compare_attr("type", params, ".*windows.*"):
        return Windows
    return None

class Windows(Application):
    template_rules = [
        TemplateRule(template="os_windows_default"),
        TemplateRule(needsattr="filesystems", template="os_windows_fs"),
    ]
```

A cookbook (`/etc/coshsh/conf.d/my.cfg`):

```ini
[datasource_inventory]
type = mycmdb
url = https://cmdb.example.com/api
token = %(CMDB_TOKEN)%

[recipe_prod]
datasources = inventory
classes_dir = /etc/coshsh/recipes/prod/classes
templates_dir = /etc/coshsh/recipes/prod/templates
objects_dir = /omd/sites/prod/etc/naemon/conf.d/generated
```

## When to load which reference

`references/datasource.md` — writing custom datasources. Read this whenever the task involves pulling data from anywhere (API, DB, CSV, JSON, LDAP, file). The mandatory read before writing any `datasource_*.py`.

`references/application_class.md` — writing `app_*.py` and `os_*.py` classes. Read this when modeling a new OS, firmware, or piece of software, deciding what templates to associate, or overriding `__init__`/`wemustrepeat`.

`references/template_rules.md` — `TemplateRule` deep dive. Read this when the user asks "how do I generate only X file when condition Y holds" or "how do I name the output file based on Z" or mentions `needsattr`, `valueofattr`, `unique_config`, `for_tool`.

`references/monitoring_details.md` — `MonitoringDetail`, the built-in detail types (FILESYSTEM, PORT, URL, INTERFACE, LOGIN, LOGINSNMPV2, KEYVALUES, ...), the slot conventions, and writing custom `detail_*.py`. Read this whenever the data has per-application repeating sub-records (drives, interfaces, URLs, ports, etc.) or scalar config per application (credentials, SNMP communities).

`references/templates.md` — Jinja2 `.tpl` files, coshsh's custom filters (`|service`, `|host`, `|contact`, `|custom_macros`, `|re_sub`, `|re_escape`, `|rfc3986`, `|neighbor_applications`) and globals (`environ`). Read this when writing or debugging a `.tpl`.

`references/cookbook.md` — Recipe and datasource INI configuration. Read this when writing or modifying `/etc/coshsh/conf.d/*.cfg`, configuring multiple datasources, mappings, environment variable substitution, run-safety protection (`max_delta`, `max_render_error_pct`, `tolerate_missing_templates`), `coshsh-cook` exit codes, or PID/log paths.

`references/datarecipient.md` — writing custom `datarecipient_*.py` for non-Nagios output (Prometheus JSON, database writes, API push, atomic file groups). Read this when the output isn't standard `define {...}` config files or needs to be routed by `for_tool` tags.

`references/util_and_jinja_extensions.md` — `coshsh.util` functions (`compare_attr`, `substenv`, `str2bool`), and writing custom Jinja2 extensions registered via `my_jinja2_extensions` in the recipe.

`references/troubleshooting.md` — debugging recipe runs. Read this when the user reports an error, missing output, wrong class being used, template errors, PID file issues, or "it ran but nothing happened".

`references/cheatsheet.md` — one-page reference: every class, every method signature, every built-in detail type, every built-in Jinja2 filter. Read this first if you just need to refresh syntax.

`assets/` contains starter skeleton files (`datasource_skeleton.py`, `os_skeleton.py`, `app_skeleton.py`, `detail_skeleton.py`, `datarecipient_skeleton.py`, `cookbook_skeleton.cfg`, `template_skeleton.tpl`) that can be copied and adapted. Use them as starting points instead of writing from scratch.

## Workflow when the user asks for code

1. Identify the artifact type (datasource, app/os class, detail, datarecipient, template, cookbook). If unclear, ask one clarifying question.
2. Read the matching reference file(s). Often two are relevant — e.g. a datasource that creates filesystem details needs `datasource.md` *and* `monitoring_details.md`.
3. Start from the appropriate skeleton in `assets/`.
4. Fill in the identifier function, `__init__`, and `read()` (or equivalent).
5. Sanity-check against the "Mandatory conventions" list above before returning code. Common slip-ups: forgetting `super().__init__()`, returning the class instance instead of the class from the identifier, mismatching `type` casing, not stripping `None`s, raising generic `Exception` instead of `DatasourceNotAvailable`.
6. If the code creates new application types, mention which template files the user must also create (one per `TemplateRule.template`). This is not merely cosmetic: a rule whose `.tpl` is absent counts as a render error for every object it fires on, and on a recipe that sets `max_render_error_pct` it can stop the whole recipe from publishing.
7. If the code uses a new detail type, mention that a matching `detail_*.py` must exist (point at `references/monitoring_details.md`).

## When the user is debugging

Read `references/troubleshooting.md`. The shortcut symptom-to-cause table at the top covers about 90% of cases. Always ask for the log output with `--debug` if not provided — coshsh logs are very informative once `log_level = DEBUG` is set.
