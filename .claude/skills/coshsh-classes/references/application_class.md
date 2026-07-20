# Writing app_*.py and os_*.py Classes

Application and OS classes are how coshsh models a specific kind of monitored thing — Linux, Windows 2019, Cisco IOS, Oracle, Apache, your in-house batch processor — and bind it to the templates that produce its service definitions. Structurally they are identical: the `app_` vs `os_` prefix is purely a naming convention to help humans browse the `classes_dir`. Both inherit from `coshsh.application.Application`.

## When you need a new class

Write one whenever:

- A new `type` value comes out of your datasource that you want to monitor differently from the generic case.
- You want to associate a distinct set of `.tpl` files with that type.
- The item needs custom default attributes or computed attributes (e.g. derive `community` from `location`).
- You want custom logic during the assemble phase (e.g. dynamically push the host into a hostgroup based on what applications it has).

If you skip it, applications fall back to the generic `Application` class. They still appear in `recipe.objects['applications']`, but `template_rules = []` by default so no `.tpl` files are rendered for them and no Nagios services are created. The framework will warn you in the log about unhandled application types.

## File naming convention

- `os_<name>.py` for operating systems, firmwares, appliance OSes: `os_linux.py`, `os_windows.py`, `os_cisco_ios.py`, `os_junos.py`, `os_ontap.py`, `os_paloalto.py`.
- `app_<name>.py` for application software running on a host: `app_oracle.py`, `app_mysql.py`, `app_apache.py`, `app_kafka.py`, `app_jvm.py`.

Both are loaded the same way. The convention exists so users can `ls os_*` to see what OSes are supported and `ls app_*` to see what application stacks are supported. Don't fight the convention — it pays off as the class library grows.

## The required structure

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

That's it. The minimum viable class is six effective lines (identifier + class with `template_rules`). Everything else is optional.

## `__mi_ident__(params={})`

The "Managed Item Identifier" function. Called for every `app_*.py` / `os_*.py` module in the `classes_dir` whenever an `Application(row)` is constructed. The first module returning a non-`None` class wins, and that class becomes the type of the newly-constructed object (the framework re-blesses the instance into the returned class).

```python
def __mi_ident__(params={}):
    if coshsh.util.compare_attr("type", params, ".*windows.*"):
        return Windows
    return None
```

**`params` is lowercased on entry** — the framework converts `params['type']` to lowercase before invoking identifier functions for application items. Write your regex against lowercase.

**Match on `type`, not `name`.** `name` is the role of the application instance ("os", "billing_db"); `type` is the kind of software ("windows", "oracle"). `__mi_ident__` is about kinds.

**You can match on multiple attributes** if your data warrants it:

```python
def __mi_ident__(params={}):
    if (compare_attr("type", params, "oracle") and
        compare_attr("version", params, "^(19|21|23)")):
        return ModernOracle
    if compare_attr("type", params, "oracle"):
        return LegacyOracle
    return None
```

**One file may export multiple classes** via a single `__mi_ident__` with branches. This is the right pattern for closely-related variants sharing code through inheritance:

```python
def __mi_ident__(params={}):
    t = params.get("type", "")
    if t.startswith("windows2019"): return Win2019
    if t.startswith("windows2022"): return Win2022
    if t.startswith("windows"):     return WindowsGeneric
    return None

class WindowsGeneric(Application):
    template_rules = [TemplateRule(template="os_windows_common")]

class Win2019(WindowsGeneric):
    template_rules = WindowsGeneric.template_rules + [
        TemplateRule(template="os_windows2019_specific"),
    ]

class Win2022(WindowsGeneric):
    template_rules = WindowsGeneric.template_rules + [
        TemplateRule(template="os_windows2022_specific"),
    ]
```

Note: `template_rules` is a *class* attribute. When you subclass, either re-declare it (concatenating the parent's, as above) or assign in `__init__` — Python won't merge them automatically.

## `template_rules`

A list of `TemplateRule` instances on the class. This is the contract between the class and the templating system: "for instances of me, render these `.tpl` files (subject to these conditions)". See `template_rules.md` for the full TemplateRule API; common forms:

```python
template_rules = [
    # Always render this template for any instance of this class.
    TemplateRule(template="os_linux_default"),

    # Only render when the application object has a 'filesystems' attribute
    # that is truthy (non-empty list, non-None, non-False). Filesystems come
    # from FILESYSTEM monitoring details processed in the assemble phase.
    TemplateRule(needsattr="filesystems", template="os_linux_fs"),

    # Only render when the application has a 'snmpv2' attribute (set by a
    # LOGINSNMPV2 detail).
    TemplateRule(needsattr="snmpv2", template="os_linux_snmp"),

    # Only render when the application explicitly has 'role' == 'mailserver'.
    TemplateRule(valueofattr={'role': 'mailserver'}, template="os_linux_mail"),
]
```

`TemplateRule(template="X")` makes coshsh look for `X.tpl` in `templates_dir`. If the file is missing, the recipe logs `cannot find template X` at ERROR, counts a render error for every object that referenced it, and continues with other items — but that template's output is lost, and on a recipe with `max_render_error_pct` set it can abort the run so that nothing is published at all. Always create the `.tpl` alongside the class.

## Custom `__init__`

If you want to set defaults, compute derived attributes, or normalize incoming data, override `__init__`:

```python
class Apache(Application):
    template_rules = [
        TemplateRule(template="app_apache_default"),
        TemplateRule(needsattr="vhosts", template="app_apache_vhosts"),
    ]

    def __init__(self, params={}):
        super().__init__(params)            # ALWAYS first
        self.port = params.get('port', 80)
        self.ssl_port = params.get('ssl_port', 443)
        self.ssl_enabled = coshsh.util.str2bool(params.get('ssl', 'no'))
        # derived attribute:
        self.uri = ('https' if self.ssl_enabled else 'http') + f"://localhost:{self.ssl_port if self.ssl_enabled else self.port}"
```

`super().__init__(params)` MUST be the first line. The base class:

- Copies every key in `params` to `self.<key>` as an attribute (so `params['host_name']` becomes `self.host_name`).
- Sets `self.monitoring_details = []`.
- Sets `self.contact_groups = []`.
- Sets `self.config_files = {}` (filled in during render).
- Sets `self.hostgroups = []` (yes, applications can be in hostgroups via their host).
- Initializes the macros dict.

So *after* `super().__init__(params)`, every column from the datasource row is already an attribute, and the templates can use them. Your override is just for defaults, derived values, and normalization.

**Don't pop keys from `params` before super-init** — let the base class see the whole dict. If you need to transform a value, set it on `self` *after* `super().__init__()`:

```python
def __init__(self, params={}):
    super().__init__(params)
    self.version = self._normalize_version(self.version)  # was set by super-init
```

## `wemustrepeat()` — optional custom assemble logic

If you define a method `wemustrepeat(self)` on the class, coshsh calls it during the assemble phase, after monitoring details have been resolved but before templates are rendered. Use it for logic that needs to see the fully-assembled item:

```python
class Linux(Application):
    template_rules = [TemplateRule(template="os_linux_default")]

    def wemustrepeat(self):
        # at this point, self.filesystems is populated from FILESYSTEM details
        # add a hostgroup based on how many filesystems we monitor
        if len(getattr(self, 'filesystems', [])) > 10:
            host = self.host  # the parent Host object
            if 'lots_of_fs' not in host.hostgroups:
                host.hostgroups.append('lots_of_fs')
```

`self.host` is the parent Host object, populated during the assemble phase. From `wemustrepeat()` you can mutate the parent host's hostgroups, contact_groups, macros — these mutations are visible in the host's template when it renders.

`wemustrepeat()` is rarely needed. If you find yourself reaching for it, consider whether the logic belongs in the datasource (closer to the data) or in the template (closer to the output). Reserve `wemustrepeat()` for cross-object reasoning that requires details to be fully resolved.

## Accessing the parent host

Inside a class method or in a template, the parent host of an application is at `self.host` (in code) or `application.host` (in templates):

```python
class Cisco(Application):
    def wemustrepeat(self):
        # mirror snmp community from a host-level macro
        if hasattr(self.host, 'snmp_community') and not hasattr(self, 'community'):
            self.community = self.host.snmp_community
```

```jinja
{{ application.host.address }}
{{ application.host.macros._LOCATION }}
```

## Inheriting from base classes that aren't `Application`

For non-application items (e.g. modeling SNMP traps, custom MIBs, BMC sensors), inherit directly from `coshsh.item.Item`:

```python
import coshsh
from coshsh.item import Item
from coshsh.templaterule import TemplateRule

def __mi_ident__(params={}):
    if params.get("type") == "mib":
        return MibConfig
    return None

class MibConfig(Item):
    id = 'mibconfig'   # singular tag — pluralizes to 'mibconfigs' for recipe.objects key
    my_type = 'mibconfig'
    template_rules = [TemplateRule(template="mib_default")]
    # ... custom methods
```

The class attribute `id` (singular) determines the registry key. Items of this class end up in `recipe.objects['mibconfigs']` and you add them with `self.add('mibconfigs', m)` from your datasource. See the SNMPTT test recipe in coshsh's tree for a full example.

## Attribute naming conventions

Templates access these attributes verbatim — naming hygiene matters.

- Lowercase, underscore-separated: `port`, `ssl_enabled`, `web_root`, `db_user`, `version`.
- Don't shadow built-ins: avoid `type` (already the application type), `name` (already the application name).
- Boolean attributes get an "is_" or just plain verb: `is_clustered`, `enabled`, `audit_logging`.
- Lists in plural: `vhosts`, `instances`, `endpoints`. Scalars in singular.

## Where attributes come from

Three sources, all visible to templates:

1. **Datasource row.** Every key in the dict passed to `Application(params_dict)` becomes a direct attribute via the base `__init__`.
2. **Class `__init__` overrides.** Set in your subclass `__init__`, after the super-init.
3. **Monitoring details.** Resolved during assemble. `FILESYSTEM` details produce `application.filesystems` (list). `LOGINSNMPV2` produces `application.snmpv2` (scalar object with `.community`, `.protocol`). The detail class's `property` and `property_type` class attributes determine the attribute name and type. See `monitoring_details.md`.

## Worked examples

### Operating system class (Linux)

```python
import coshsh
from coshsh.application import Application
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr

def __mi_ident__(params={}):
    if compare_attr("type", params, "(red\\s?hat|rhel|centos|alma|rocky|debian|ubuntu|suse|sles).*"):
        return Linux
    return None

class Linux(Application):
    template_rules = [
        TemplateRule(template="os_linux_default"),
        TemplateRule(needsattr="filesystems", template="os_linux_fs"),
        TemplateRule(needsattr="snmpv2",      template="os_linux_snmp"),
        TemplateRule(needsattr="urls",        template="os_linux_urls"),
    ]

    def __init__(self, params={}):
        super().__init__(params)
        # default check interval if datasource didn't supply one
        if not hasattr(self, 'check_interval'):
            self.check_interval = 5
```

### Application class with custom logic (Oracle)

```python
import coshsh
from coshsh.application import Application
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr

def __mi_ident__(params={}):
    if compare_attr("type", params, "oracle"):
        return Oracle
    return None

class Oracle(Application):
    template_rules = [
        TemplateRule(template="app_oracle_default"),
        TemplateRule(needsattr="tablespaces",   template="app_oracle_ts"),
        TemplateRule(needsattr="login",         template="app_oracle_health"),
        TemplateRule(valueofattr={'role': 'standby'}, template="app_oracle_standby"),
    ]

    def __init__(self, params={}):
        super().__init__(params)
        # the SID is conventionally uppercase
        self.sid = self.name.upper()
        # default port
        self.port = int(params.get('port', 1521))
        # SQL connect string if credentials present
        if hasattr(self, 'username') and hasattr(self, 'password'):
            self.connect_string = f"{self.username}/{self.password}@{self.host_name}:{self.port}/{self.sid}"

    def wemustrepeat(self):
        # if this Oracle is part of a RAC, push its host into the rac hostgroup
        if getattr(self, 'rac_cluster', None):
            self.host.hostgroups.append(f"oracle_rac_{self.rac_cluster}")
```

### Network device firmware class (Cisco IOS)

```python
import coshsh
from coshsh.application import Application
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr

def __mi_ident__(params={}):
    if compare_attr("type", params, "(ios|cisco_ios|catos)"):
        return CiscoIOS
    return None

class CiscoIOS(Application):
    template_rules = [
        TemplateRule(template="os_cisco_ios_default"),
        TemplateRule(needsattr="interfaces", template="os_cisco_ios_if"),
        TemplateRule(needsattr="snmpv2",     template="os_cisco_ios_snmp"),
        TemplateRule(needsattr="snmpv3",     template="os_cisco_ios_snmp_v3"),
        # Prometheus-tagged output for SNMP exporter
        TemplateRule(template="cisco_ios_exporter", suffix="json", for_tool="prometheus"),
    ]
```

### Modeling a non-host item (network site)

```python
import coshsh
from coshsh.item import Item
from coshsh.templaterule import TemplateRule

def __mi_ident__(params={}):
    if params.get("type") == "site":
        return Site
    return None

class Site(Item):
    id = 'site'
    my_type = 'site'
    template_rules = [TemplateRule(template="site_default")]

    @classmethod
    def fingerprint(cls, params):
        return params['site_code']  # custom unique key
```

The datasource would do `self.add('sites', Site(row))`. The default `datarecipient_coshsh_default` writes one config per site under `dynamic/sites/<fingerprint>/site_default.cfg`.

## Class attributes for advanced behaviors

| Class attribute       | Meaning                                                                  |
| --------------------- | ------------------------------------------------------------------------ |
| `template_rules`      | List of TemplateRule — required for any template output                  |
| `id`                  | Singular item type tag (for Item subclasses) — pluralizes to dict key    |
| `my_type`             | Item type label used in some internal lookups                            |
| `lower_columns`       | Optional list of column names to lowercase on incoming params            |

For application classes, `template_rules` is the only one you'll almost always set.

## Pitfalls

1. **Forgetting `super().__init__(params)`.** Half the attributes go missing because the base class did the copying.
2. **Returning the class instance from `__mi_ident__`.** Always return the class, not `MyClass()`.
3. **Matching case-sensitively on `type` when the framework already lowercased it.** Always lowercase your patterns.
4. **Declaring `template_rules = parent.template_rules` and then `.append()`-ing in a subclass.** That mutates the parent's list! Use `template_rules = parent.template_rules + [...]` to create a new list, or re-declare from scratch.
5. **Creating attributes on `self` whose names collide with `Item` internals** (`fingerprint`, `render`, `create_templates`, `resolve_monitoring_details`, `monitoring_details`, `config_files`, `host`). Pick unambiguous names.
6. **Forgetting that without `template_rules`, the class is invisible.** It loads, `__mi_ident__` matches, the instance is re-blessed — but with no rules, no `.tpl` is selected and no output is produced. Always start with at least one default rule.
7. **Heavy work in `__init__`.** Constructors run for every item the framework processes. Keep them fast; put expensive logic in `wemustrepeat()` or earlier in the datasource.
