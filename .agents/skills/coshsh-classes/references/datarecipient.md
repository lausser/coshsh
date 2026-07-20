# Writing Custom Datarecipients (datarecipient_*.py)

A datarecipient takes the populated `recipe.objects` after the render phase and produces output — files, API calls, database writes, anything. The default recipient (`datarecipient_coshsh_default`, referenced as `>>>` in recipes) writes one config file per `item.config_files` entry in `<objects_dir>/dynamic/hosts/<host_name>/<template>.cfg`. You write a custom one when:

- The output isn't files (DB rows, API push, queue messages).
- The output is files but in a non-default location or layout (Prometheus targets, Alertmanager configs, an external tool's JSON).
- You want to filter what's written based on `for_tool=` tags on `TemplateRule`s.
- You need to write a single aggregated file from many items (e.g. one big JSON instead of per-host files).
- You need to do something with the objects beyond just writing their `config_files` (e.g. push to ServiceNow as monitoring records).

## File location and naming

`datarecipient_<name>.py` in any `classes_dir`. The framework's loader filters by the `datarecipient_` prefix; other names are ignored.

## The required structure

```python
import logging
import coshsh
from coshsh.datarecipient import Datarecipient
from coshsh.util import compare_attr

logger = logging.getLogger('coshsh')

def __dr_ident__(params={}):
    if compare_attr("type", params, "my_recipient"):
        return MyRecipient
    return None

class MyRecipient(Datarecipient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # store config from the cookbook section

    def output(self, filter=None, objects={}):
        # produce side effects based on objects
        return True
```

Same identifier pattern as datasources: `__dr_ident__(params)` returns the class for a matching `type`. Same `super().__init__(**kwargs)` requirement.

## `__dr_ident__(params={})`

Selected via the `type =` line in the cookbook's `[datarecipient_<name>]` section. Same conventions as `__ds_ident__` — return the class (not an instance), handle multiple types via branches, use `compare_attr` for regex matching.

## `__init__(self, **kwargs)`

```python
def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.output_path = kwargs["output_path"]
    self.format      = kwargs.get("format", "json")
```

`kwargs` comes from the `[datarecipient_<name>]` cookbook section. The base class sets `self.name` (the section name without prefix), `self.objects_dir` (from the recipe), and a few other internals.

## `output(self, filter=None, objects={})`

The single method that matters. Called by the recipe after render. `objects` is `recipe.objects` — same shape as inside a datasource's `read()`:

```python
objects = {
    'hosts': {'web01': <Host>, 'web02': <Host>, ...},
    'applications': {'web01+os+linux': <Application>, ...},
    'details': {...},
    'contacts': {...},
    'contactgroups': {...},
    'hostgroups': {...},
    # plus any custom item types your datasources added
}
```

Each item has its `config_files` dict populated by render — keys are filenames (from `TemplateRule.unique_config` + `suffix`) and values are the rendered config strings. Plus each item has its full set of attributes still accessible.

```python
def output(self, filter=None, objects={}):
    for host_name, host in objects.get('hosts', {}).items():
        for filename, content in host.config_files.items():
            # decide whether to write, where, how
            self._write_file(host, filename, content)

    for app_key, app in objects.get('applications', {}).items():
        for filename, content in app.config_files.items():
            self._write_file_for_app(app, filename, content)
    return True
```

Return `True` on success, `False` (or raise) on failure.

## Filtering by `for_tool`

The whole point of custom datarecipients is often to route output by tag. `TemplateRule(template="...", for_tool="prometheus")` produces config_files entries marked for "prometheus". A recipient can filter:

```python
def output(self, filter=None, objects={}):
    for items in objects.values():
        for item in items.values():
            for filename, content in item.config_files.items():
                # find the template rule that produced this file
                rule = item.template_rule_for_file(filename)  # or inspect template_rules
                if rule and rule.for_tool == "prometheus":
                    self._write_prom_target(item, filename, content)
    return True
```

The default datarecipient does the opposite — it skips files whose template rule has a non-None `for_tool` (those are "claimed" by a specialized recipient).

## Worked example: Prometheus SNMP targets

```python
import json
import logging
import os
import coshsh
from coshsh.datarecipient import Datarecipient
from coshsh.util import compare_attr

logger = logging.getLogger('coshsh')

def __dr_ident__(params={}):
    if compare_attr("type", params, "snmp_exporter"):
        return SnmpExporterRecipient
    return None

class SnmpExporterRecipient(Datarecipient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output_path = kwargs["output_path"]

    def output(self, filter=None, objects={}):
        os.makedirs(self.output_path, exist_ok=True)
        targets = []

        for app in objects.get('applications', {}).values():
            # the application's class has a rule tagged for_tool="prometheus"
            for filename, content in app.config_files.items():
                if not filename.endswith(".json"):
                    continue
                try:
                    target = json.loads(content)
                    targets.append(target)
                except json.JSONDecodeError as e:
                    logger.error(f"bad json in {filename}: {e}")

        # write one aggregated targets file
        out = os.path.join(self.output_path, "snmp_targets.json")
        with open(out, "w") as f:
            json.dump(targets, f, indent=2)
        logger.info(f"wrote {len(targets)} prometheus snmp targets to {out}")
        return True
```

Cookbook usage:

```ini
[datarecipient_snmp_targets]
type        = snmp_exporter
output_path = /etc/prometheus/snmp_targets

[recipe_network]
datasources    = cmdb
datarecipients = >>>, snmp_targets
classes_dir    = ...
templates_dir  = ...
objects_dir    = /etc/naemon/conf.d/generated/network
```

The `>>>` ensures the standard Nagios configs still get written; `snmp_targets` handles the Prometheus-tagged ones.

## Worked example: atomic file writer (one file per item type)

When you want one file per item-type rather than one per (host, template):

```python
class AtomicRecipient(Datarecipient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output_path = kwargs["output_path"]
        self.items_to_handle = [s.strip() for s in kwargs.get("items", "").split(",") if s.strip()]

    def output(self, filter=None, objects={}):
        os.makedirs(self.output_path, exist_ok=True)
        for item_type in self.items_to_handle:
            chunks = []
            for item in objects.get(item_type, {}).values():
                chunks.extend(item.config_files.values())
            out = os.path.join(self.output_path, f"{item_type}.conf")
            with open(out, "w") as f:
                f.write("\n".join(chunks))
            logger.info(f"wrote {len(chunks)} {item_type} configs to {out}")
        return True
```

Cookbook:

```ini
[datarecipient_atomic_mibs]
type         = atomic
output_path  = /etc/check_logfiles/mibs
items        = mibconfigs
```

This is the pattern in coshsh's SNMPTT test recipe — one big file per item type rather than one file per item.

## Worked example: database writer

```python
import psycopg2
import json

class DbAuditRecipient(Datarecipient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dsn = kwargs["dsn"]

    def output(self, filter=None, objects={}):
        try:
            conn = psycopg2.connect(self.dsn)
        except psycopg2.OperationalError as e:
            logger.error(f"audit db unreachable: {e}")
            return False

        try:
            with conn.cursor() as cur:
                cur.execute("BEGIN")
                cur.execute("TRUNCATE coshsh_audit")
                for host in objects.get('hosts', {}).values():
                    cur.execute(
                        "INSERT INTO coshsh_audit (host_name, address, attributes) VALUES (%s, %s, %s)",
                        (host.host_name, host.address, json.dumps({
                            k: v for k, v in host.__dict__.items()
                            if isinstance(v, (str, int, float, bool, list, dict))
                        })),
                    )
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        return True
```

This recipient produces no files — it just records the inventory into a database. Useful for auditing what coshsh generated vs what's running.

## Filter parameter

`output(self, filter=None, ...)` receives the recipe's `filter =` string, same as a datasource. Most recipients ignore it; some use it to scope what they write. The convention (if used) is the same as for datasources.

## `max_delta` support

The default datarecipient implements `max_delta` change protection (comparing old and new file counts). If you write a recipient that produces files in a stable layout, consider implementing `max_delta` too — the base `Datarecipient` class has hooks for it. For non-file output (DB rows, API calls), `max_delta` usually doesn't apply.

## Interaction with the default recipient (`>>>`)

When a recipe lists `datarecipients = >>>, my_custom`, the default recipient runs alongside. The two should not write to the same files. Conventional separation:

- Default `>>>` writes Nagios configs into `<objects_dir>/dynamic/`. It skips `for_tool`-tagged files (those are "claimed" elsewhere).
- Custom recipients write to their own paths and only handle items/files they care about.

If you write a recipient that wholly supersedes the default, drop `>>>` from `datarecipients =` and only list yours.

## Pitfalls

1. **Forgetting `super().__init__(**kwargs)`.** Base class internals (logger setup, name) aren't wired.
2. **Returning a class instance from `__dr_ident__`.** Always the class itself.
3. **Writing to `<objects_dir>/dynamic/` from a custom recipient.** Collides with the default. Custom recipients use their own `output_path`.
4. **Iterating `objects` without `.get(..., {})`.** A recipe with no contacts has no `'contacts'` key in `objects` at all. Use `.get()` to avoid `KeyError`.
5. **Mutating items in `output()`.** This is the output phase — items should be considered read-only here. Mutations don't affect anything since no further phase runs, but they may confuse you when debugging.
6. **Forgetting to `os.makedirs(output_path, exist_ok=True)`.** First-run failure when the directory doesn't exist.
7. **Not handling render errors.** Some items may have empty `config_files` because their templates failed to render. Don't assume every item has output.
8. **Assuming `output()` always runs.** When a recipe sets `max_render_error_pct` and exceeds it, the whole output phase is skipped — your datarecipient is never called, deliberately, so the previous run's state survives untouched. This matters most for recipients with external side effects (API push, database write): design them so that *not* being called is a safe outcome, and never treat "no call this run" as "there is nothing to monitor".
