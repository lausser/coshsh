# coshsh Cheatsheet — One-Page Quick Reference

Refresh syntax without rereading the deep-dive references. Everything here is covered in depth elsewhere; this is for lookup.

## File naming → recognition prefix → identifier function

| File prefix | What it is | Identifier function | Returns |
|---|---|---|---|
| `datasource_*.py` | Datasource subclass | `__ds_ident__(params)` | class or `None` |
| `app_*.py` | Application subclass | `__mi_ident__(params)` | class or `None` |
| `os_*.py` | Application subclass (OS) | `__mi_ident__(params)` | class or `None` |
| `detail_*.py` | MonitoringDetail subclass | `__detail_ident__(params)` | class or `None` |
| `datarecipient_*.py` | Datarecipient subclass | `__dr_ident__(params)` | class or `None` |

`params` is the cookbook section dict for that section. The identifier returns the class to instantiate, or `None` (silently passed over).

## Datasource skeleton — the 5 methods

```python
from coshsh.datasource import Datasource, DatasourceNotAvailable, DatasourceNotCurrent, DatasourceCorrupt
from coshsh.host import Host
from coshsh.application import Application
from coshsh.monitoringdetail import MonitoringDetail
from coshsh.contactgroup import ContactGroup
from coshsh.contact import Contact

def __ds_ident__(params={}):
    if params.get("type", "").lower() == "myformat":
        return MyDatasource
    return None

class MyDatasource(Datasource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # store kwargs you need: self.name, self.dir, self.url, etc.

    def open(self):
        # connect; raise DatasourceNotAvailable on failure
        pass

    def read(self, filter=None, objects={}, force=False, **kwargs):
        self.objects = objects  # MANDATORY — rebind to the shared dict
        # for each row:
        #   self.add('hosts', Host(row))
        #   self.add('applications', Application(row))
        #   self.add('details', MonitoringDetail(row))
        return True

    def close(self):
        pass
```

## Application / OS skeleton

```python
from coshsh.application import Application
from coshsh.templaterule import TemplateRule

def __mi_ident__(params={}):
    if params["type"].lower() == "redhat":
        return RedHat
    return None

class RedHat(Application):
    template_rules = Application.template_rules + [
        TemplateRule(template="os_linux_default",
                     unique_attr="type"),
        TemplateRule(needsattr="filesystems",
                     template="os_linux_fs"),
    ]
    # optional:
    # def __init__(self, params={}):
    #     super().__init__(params)
    #     ...
    # def wemustrepeat(self):
    #     # second-pass hook after all details attached
    #     pass
```

## MonitoringDetail skeleton (custom)

```python
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params["monitoring_type"] == "MYTYPE":
        return MyDetail
    return None

class MyDetail(MonitoringDetail):
    property = "things"        # bucket name on parent app: app.things = [...]
    property_type = list       # or "scalar"
    # for list type, items get appended; for scalar, last one wins

    def __init__(self, params={}):
        super().__init__(params)
        self.path = params.get("monitoring_0")
        self.alias = params.get("monitoring_1")

    def fingerprint(self):
        return self.path  # used for dedup; uniqueness key
```

## Datarecipient skeleton

```python
from coshsh.datarecipient import Datarecipient

def __dr_ident__(params={}):
    if params["type"] == "myformat":
        return MyDatarecipient
    return None

class MyDatarecipient(Datarecipient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.target = kwargs.get("target")

    def output(self, filter=None, objects={}):
        # objects has 'hosts', 'applications', 'contacts', 'contactgroups'
        # write your output files
        pass
```

## Item required fields

| Class | Required dict keys |
|---|---|
| `Host` | `host_name`, `address` |
| `Application` | `host_name`, `name`, `type` |
| `MonitoringDetail` | `host_name`, `name`, `type`, `monitoring_type`, `monitoring_0..N` |
| `Contact` | `contact_name` |
| `ContactGroup` | `contactgroup_name` |

The `Application` and `MonitoringDetail` `host_name`+`name`+`type` triple **must match exactly** for the detail to attach to the application. This is the #1 silent failure.

## Built-in MonitoringDetail types

**List types** (multiple instances allowed):

| `monitoring_type` | Slots | Parent attribute |
|---|---|---|
| `FILESYSTEM` | path, warning, critical | `filesystems` |
| `PORT` | port, protocol, warning, critical | `ports` |
| `INTERFACE` | name, alias | `interfaces` |
| `URL` | name, url, expect | `urls` |
| `DATASTORE` | name, warning, critical | `datastores` |
| `TABLESPACE` | name, warning, critical | `tablespaces` |
| `VOLUME` | name, warning, critical | `volumes` |
| `PROCESS` | name, warning, critical | `processes` |
| `ROLE` | name | `roles` |
| `TAG` | name | `tags` |
| `SOCKET` | name | `sockets` |

**Scalar types** (single, last-wins):

| `monitoring_type` | Slots | Parent attribute |
|---|---|---|
| `LOGIN` | username, password | `login` |
| `LOGINSNMPV2` | community | `loginsnmpv2` |
| `LOGINSNMPV3` | user, authkey, privkey, ... | `loginsnmpv3` |
| `ACCESS` | various | `access` |
| `KEYVALUES` | key=value pairs | `keyvalues` |
| `DEPTH` | level | `depth` |
| `NAGIOSCONF` | raw config | `nagiosconf` |
| `NAGIOS` | raw nagios fragment | `nagios` |

## TemplateRule parameters

```python
TemplateRule(
    template="os_linux_fs",           # template file name without .tpl
    needsattr="filesystems",          # only render if app has this attribute
    needsnotattr="nofs",              # only render if app does NOT have this
    valueofattr="version",            # render once per distinct value
    unique_attr="type",               # uniqueness key for the output filename
    unique_config="%s_%s_fs",         # output filename pattern (sprintf-style)
    suffix="cfg",                     # output file extension (default: cfg)
    for_tool="nagios",                # routes to datarecipient with for_tool tag
    prio=1,                           # rendering priority
)
```

## Built-in Jinja2 filters

| Filter | Use | Example |
|---|---|---|
| `\|service` | Render a service block | `{{ host \|service("ping") }}` |
| `\|host` | Render a host block | `{{ host \|host }}` |
| `\|contact` | Render a contact block | `{{ contact \|contact }}` |
| `\|custom_macros` | Emit `_KEY value` lines | `{{ host \|custom_macros }}` |
| `\|re_sub(p,r)` | Regex substitute | `{{ name \|re_sub("[^a-z]","_") }}` |
| `\|re_escape` | Escape for regex | `{{ x \|re_escape }}` |
| `\|rfc3986` | URL-encode | `{{ url \|rfc3986 }}` |
| `\|neighbor_applications` | Sibling apps on same host | `{% for a in app \|neighbor_applications %}` |

## Custom Jinja2 extension naming

Place in `classes_dir`. Discovered by prefix:

| Prefix | Becomes |
|---|---|
| `filter_xxx` | `{{ value \| xxx }}` |
| `is_xxx` | `{% if x is xxx %}` |
| `global_xxx` | `{{ xxx(args) }}` |

Register the file via cookbook: `my_jinja2_extensions = filter_xxx,is_xxx`.

## coshsh.util helpers

```python
from coshsh.util import compare_attr, is_attr, substenv, str2bool

# compare_attr — regex/glob matching
compare_attr("type", params, "windows.*")        # regex match
compare_attr("type", params, "!windows.*")       # NOT match
compare_attr("type", params, "!~windows.*")      # not-regex (explicit)
compare_attr("type", params, "linux|redhat")     # alternatives

# is_attr — check attr exists and is truthy
is_attr("filesystems", app)

# substenv — substitute ${ENV} in strings
substenv("${HOME}/configs")

# str2bool — flexible bool parsing
str2bool("yes")   # True
str2bool("0")     # False
```

## Exceptions a datasource can raise

| Exception | When to raise | What happens |
|---|---|---|
| `DatasourceNotAvailable` | Connect failed, source down | Recipe continues with previous data if `max_delta` allows |
| `DatasourceNotCurrent` | Source returned stale/empty | Recipe aborts; old configs preserved |
| `DatasourceCorrupt` | Data is malformed/unsafe | Recipe aborts hard |

## Item attribute access shortcuts

```python
# In a datasource read():
self.add('hosts', host)              # registers Host in self.objects['hosts']
self.add('applications', app)        # by host_name+name+type triple key
self.add('details', detail)          # attached by host_name+name+type match
self.add('contacts', contact)
self.add('contactgroups', cg)

# After re-blessing, in an Application subclass:
self.host                            # parent Host object
self.host.applications               # sibling apps (list)
self.filesystems                     # detail list (if FILESYSTEM details)
self.contact_groups                  # list of ContactGroup names
self.macros                          # dict of custom macros (renders as _KEY)
```

## Cookbook (INI) section types

```ini
[defaults]
classes_dir = ./classes
templates_dir = ./templates

[recipe_prod]
classes_dir = ./classes,/etc/coshsh/classes
templates_dir = ./templates
datasources = csvfile,inventoryapi
datarecipients = >>>recipient,prometheus
objects_dir = /etc/nagios/conf.d/prod
max_delta = 100:200
max_render_error_pct = 0
tolerate_missing_templates = no
git_init = yes
pid_dir = /var/run/coshsh
my_jinja2_extensions = filter_phone,is_critical

[datasource_csvfile]
type = csv
dir = /var/lib/inventory
name = csvfile

[datasource_inventoryapi]
type = restapi
url = https://inventory.example.com/api
name = inventoryapi

[datarecipient_prometheus]
type = prometheus_sd
target = /etc/prometheus/sd_targets.json

[mapping_locations]
DC1 = datacenter-frankfurt
DC2 = datacenter-amsterdam
```

Substitution syntax:
- `%(VAR)%` — references an env var or another cookbook value
- `@{MAPPING[key]}` — looks up `[mapping_MAPPING]` by `key`

## Running coshsh

```bash
coshsh-cook --cookbook cookbook.cfg                 # all recipes
coshsh-cook --cookbook cookbook.cfg --recipe prod   # one recipe
coshsh-cook --cookbook cookbook.cfg --debug         # verbose
coshsh-cook --cookbook cookbook.cfg --force         # ignore max_delta
```

Exit codes: `0` all recipes fine · `2` bad cookbook or uninterpretable run-safety
value, nothing ran · `3` cannot import coshsh · `4` a recipe aborted on template
errors, its previous output untouched.

Log pattern for a clean recipe: `recipe \S+ completed with 0 problems`. The
whole line also carries the attempt count and, when anything failed, a breakdown:
`completed with 3 problems out of 4213 rendering attempts [1 missing, 2 faulty]`.
An aborted recipe emits no completion line, only `aborted:` at ERROR.

## Phase order (mental model)

1. **collect** — datasources `open` → `read` → `close` populate shared `objects` dict
2. **assemble** — applications re-blessed to subclass; details attached to apps; `wemustrepeat()` runs
3. **render** — template_rules iterated; matching Jinja2 templates rendered per item. Failures are counted in `recipe.render_tally` (`attempts`, `missing`, `errors`); `recipe.render_errors` is a read-only view of the failures that count against the tolerance
4. **abort gate** — if the failure percentage exceeds `max_render_error_pct`, output is skipped entirely and the previous run's files stay untouched
5. **output** — datarecipients write to disk/network; default `>>>recipient` writes to `objects_dir`

## Common silent failures

1. Detail not attaching → triple `host_name`+`name`+`type` mismatch between Application and MonitoringDetail
2. Falls back to `GenericApplication` → `__mi_ident__` returned `None`; check `type` value and lowercasing
3. Template not rendering → `needsattr` references attribute that doesn't exist; check spelling
4. Datasource not loaded → file isn't named `datasource_*.py` or isn't in `classes_dir`
5. `DatasourceNotCurrent` repeatedly → `read()` returned `False` or `self.objects = objects` line missing
6. Nothing published and exit code `4` → not a crash: the recipe exceeded `max_render_error_pct` and deliberately kept the previous output. Read the `aborted:` log line
