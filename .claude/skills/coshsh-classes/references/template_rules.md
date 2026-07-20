# TemplateRule — the contract between classes and templates

A `TemplateRule` is one entry in an application class's `template_rules` list. Each rule answers four questions:

1. **Which template file** should be rendered? (`template=`)
2. **Under what condition** does this rule apply to a given instance? (`needsattr=`, `needsnotattr=`, `valueofattr=`)
3. **What should the output filename be?** (`unique_attr=`, `unique_config=`, `suffix=`)
4. **Which datarecipient should process the output?** (`for_tool=`)

Construct rules with `coshsh.templaterule.TemplateRule(...)`. All parameters are keyword arguments.

## Import

```python
from coshsh.templaterule import TemplateRule
```

## Parameters

### `template` (string, required)

Base name of the `.tpl` file in `templates_dir`, without the `.tpl` extension.

```python
TemplateRule(template="os_linux_default")  # looks for os_linux_default.tpl
```

Coshsh searches every directory in `templates_dir` (recipe-specific paths first, then defaults) and uses the first match. A template that is not found anywhere is logged at ERROR (`cannot find template X`) and **counts as a render error**, once per object that referenced it — the rule produces no output for any of them.

That count feeds `recipe.render_errors`, the `coshsh_recipe_missing_templates` metric, and the `max_render_error_pct` abort decision, so on a recipe that sets a tolerance a forgotten `.tpl` can stop the run from publishing. If a recipe is *meant* to reference templates it does not ship, set `tolerate_missing_templates = yes` on it — the absences stay counted and logged, but leave the abort calculation.

### `needsattr` (string, optional)

Apply this rule only when the application instance has this attribute and its value is truthy (not `None`, not `False`, not empty list/dict/string, not `0`).

```python
TemplateRule(needsattr="filesystems", template="os_linux_fs")
```

Rendered only if `application.filesystems` is non-empty. This is the primary way to make templates conditional on monitoring details — `filesystems` is populated by `FILESYSTEM` details processed during assemble, so the rule fires only when the data has filesystems to monitor.

Other typical `needsattr` values:

| `needsattr=`     | Comes from               | Use case                                |
| ---------------- | ------------------------ | --------------------------------------- |
| `filesystems`    | FILESYSTEM details       | Per-FS disk space checks                |
| `interfaces`     | INTERFACE details        | Per-NIC bandwidth / status checks       |
| `ports`          | PORT details             | TCP/UDP port reachability checks        |
| `urls`           | URL details              | HTTP endpoint checks                    |
| `datastores`     | DATASTORE details        | VMware datastore checks                 |
| `tablespaces`    | TABLESPACE details       | DB tablespace checks                    |
| `volumes`        | VOLUME details           | Storage volume checks                   |
| `login`          | LOGIN detail (scalar)    | Authenticated checks (DB/SSH)           |
| `snmpv2`         | LOGINSNMPV2 detail       | SNMP v2c-based checks                   |
| `snmpv3`         | LOGINSNMPV3 detail       | SNMP v3-based checks                    |

Any custom attribute you set in `__init__` is also a valid `needsattr`:

```python
class Apache(Application):
    template_rules = [
        TemplateRule(template="app_apache_default"),
        TemplateRule(needsattr="vhosts", template="app_apache_vhosts"),
    ]
    def __init__(self, params={}):
        super().__init__(params)
        self.vhosts = params.get('vhosts')  # may be None or list
```

### `needsnotattr` (string, optional)

The inverse: apply only when the attribute is absent or falsy.

```python
TemplateRule(needsnotattr="filesystems", template="os_linux_generic_disk")
```

Use this to provide fallback behavior for items that lack specific details. E.g. "if the host doesn't have explicit filesystem details, do a generic disk check based on `check_by_ssh`".

### `valueofattr` (dict, optional)

Apply only when ALL specified attributes match their expected values exactly.

```python
TemplateRule(
    valueofattr={'environment': 'production', 'critical': True},
    template="os_linux_prod_extras",
)
```

The comparison is exact equality. For regex or fuzzy matching, do the work in `__init__` and set a clean boolean attribute:

```python
def __init__(self, params={}):
    super().__init__(params)
    self.is_prod = bool(re.match(r"prod.*", params.get('environment', '')))
```

Then:

```python
TemplateRule(valueofattr={'is_prod': True}, template="...")
```

### `unique_attr` (list of strings, optional)

Names of instance attributes whose values combine to make the output filename unique.

Default for application output is something like `["name", "type"]`, producing files such as `os_linux_default.cfg` for an application with `name='os', type='linux'`. The default works for most cases; override when you have multiple instances of the same `name+type` (rare) or want a different naming scheme.

### `unique_config` (string, optional)

A format string for the output filename. `%s` placeholders are filled in order from `unique_attr`.

```python
TemplateRule(
    template="app_oracle_default",
    unique_attr=["sid", "host_name"],
    unique_config="oracle_%s_on_%s.cfg",
)
```

Produces e.g. `oracle_BILLING_on_db01.cfg`. If `suffix` is also set, it's appended after the format string's extension is stripped.

### `suffix` (string, optional, default `.cfg`)

File extension for the rendered output.

```python
TemplateRule(template="exporter", suffix="json", for_tool="prometheus")
```

Produces a `.json` file instead of `.cfg`. Use without the leading dot.

### `for_tool` (string, optional)

A tag that custom datarecipients can use to route output. Items with rules tagged `for_tool="prometheus"` get picked up by a `datarecipient_prometheus_*.py` that filters on that tag; items with the default (`None`) `for_tool` get picked up by the standard file-writing recipient.

Combined with a custom datarecipient, this is how coshsh generates output for non-Nagios targets:

```python
class CiscoSwitch(Application):
    template_rules = [
        # Goes to dynamic/hosts/<host>/os_cisco_ios_default.cfg
        TemplateRule(template="os_cisco_ios_default"),
        # Goes to wherever datarecipient_prometheus_snmp puts it
        TemplateRule(template="snmp_exporter_target",
                     suffix="json",
                     for_tool="prometheus"),
    ]
```

### `prio` (int, optional, rarely needed)

Processing priority. Lower numbers process earlier. Default 0. Only matters when rule ordering affects naming collisions, which is uncommon. Don't set this unless you have a concrete reason.

## How the framework evaluates rules

For each item (Host, Application, etc.) during the assemble phase, coshsh:

1. Walks the class's `template_rules` (and inherited ones from parent classes if not overridden).
2. For each rule, checks `needsattr` / `needsnotattr` / `valueofattr` against the item.
3. For each rule that applies, registers the template to be rendered.
4. During render, runs Jinja2 on each registered template, producing a config string.
5. Stores the string in `item.config_files[<filename>]`.
6. The default datarecipient writes one file per entry in `item.config_files`.

Rules that don't apply are silently skipped. There's no error for an inapplicable rule.

## Common patterns

### "One default plus optional add-ons"

```python
template_rules = [
    TemplateRule(template="os_linux_default"),                          # always
    TemplateRule(needsattr="filesystems", template="os_linux_fs"),      # if FS data
    TemplateRule(needsattr="urls", template="os_linux_urls"),           # if URL data
    TemplateRule(needsattr="snmpv2", template="os_linux_snmp"),         # if SNMP data
]
```

This is the typical shape of an OS class. The default template defines core checks (ping, basic system); the conditional ones add resource-specific checks.

### "Environment-aware"

```python
template_rules = [
    TemplateRule(template="app_default"),
    TemplateRule(valueofattr={'environment': 'production'},
                 template="app_extra_paranoid"),
    TemplateRule(valueofattr={'environment': 'production'},
                 needsattr="ha_partner",
                 template="app_ha_failover_check"),
]
```

Multiple conditions on a single rule combine with AND.

### "Fallback when no details"

```python
template_rules = [
    TemplateRule(template="os_aix_default"),
    TemplateRule(needsattr="filesystems",    template="os_aix_fs"),
    TemplateRule(needsnotattr="filesystems", template="os_aix_default_fs"),
]
```

When the datasource provided filesystem details, render the detailed per-FS template; otherwise render a generic single-check fallback.

### "Multi-target output"

```python
template_rules = [
    TemplateRule(template="os_cisco_ios_nagios"),                          # default
    TemplateRule(template="os_cisco_ios_grafana", suffix="json",
                 for_tool="grafana"),                                      # for grafana
    TemplateRule(template="os_cisco_ios_prom", suffix="json",
                 for_tool="prometheus"),                                   # for prometheus
]
```

The recipe lists all three datarecipients (`>>>`, `grafana_writer`, `prometheus_writer`), each one filters on its tag.

### "Custom filename based on instance attribute"

```python
template_rules = [
    TemplateRule(
        template="db_instance",
        unique_attr=["host_name", "sid"],
        unique_config="db_%s_%s_check.cfg",
    ),
]
```

Produces e.g. `db_db01_BILLING_check.cfg`.

## Subclassing and inheritance

`template_rules` is a class attribute. Subclasses inherit it but should NOT mutate it via `.append()` — they'd mutate the parent's list. The safe patterns:

```python
class WindowsBase(Application):
    template_rules = [TemplateRule(template="os_windows_common")]

# concatenate to make a new list:
class Win2019(WindowsBase):
    template_rules = WindowsBase.template_rules + [
        TemplateRule(template="os_windows2019_specific"),
    ]

# or re-declare from scratch:
class Win2022(WindowsBase):
    template_rules = [
        TemplateRule(template="os_windows_common"),
        TemplateRule(template="os_windows2022_specific"),
    ]
```

## Pitfalls

1. **Forgetting the `.tpl` file.** The class registers a rule, the assemble phase succeeds, the render phase logs `cannot find template X`, and no output is produced for that rule. This counts as a render error and can abort a recipe that sets `max_render_error_pct`. Always pair every `TemplateRule(template="X")` with `templates/X.tpl`.
2. **Empty list considered falsy.** `needsattr="filesystems"` won't fire if `filesystems = []`. This is usually what you want, but be aware.
3. **`valueofattr` is exact equality.** No regex. Process the value in `__init__` if you need patterns.
4. **`unique_config` without enough `unique_attr` placeholders.** If `unique_config = "foo_%s.cfg"` but `unique_attr = ["a", "b"]`, the extra value is ignored. Always match the count.
5. **Spaces in `unique_attr` values.** Filesystem path or anything with spaces makes an ugly filename. Sanitize in `__init__` by setting a derived attribute.
6. **`suffix="cfg"` vs `suffix=".cfg"`.** Without the dot is the convention coshsh uses; either is usually handled, but match the existing codebase style. Default is already `.cfg` so don't set it unless you mean a different extension.
