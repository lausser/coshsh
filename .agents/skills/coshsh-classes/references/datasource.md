# Writing coshsh Datasources

A datasource is a Python class that fetches inventory data from somewhere (API, database, CSV, LDAP, JSON file, in-memory dict, ...) and translates each record into coshsh `Host`, `Application`, `MonitoringDetail`, `Contact`, and `ContactGroup` objects. This is the single most common extension point in coshsh and where most custom code lives.

## When to write a new datasource

You need a custom datasource when:

- The data lives in a system coshsh doesn't already support (most CMDBs, ITSM platforms, in-house databases, asset trackers).
- The data is in an unsupported file format (XML, custom JSON, YAML, Excel).
- You need to transform/aggregate/enrich raw data before it becomes coshsh items (e.g. join two tables, derive hostgroup from naming convention, normalize OS labels).
- You want to read from a queue, an event bus, a Kubernetes API, or anything dynamic.

You do **not** need a custom datasource for plain CSV — `datasource_csvfile` (`type = csv` in the cookbook) handles that. Look at `recipes/default/classes/datasource_csvfile.py` if you ever need to study a known-working full datasource.

## File location and naming

The file MUST be named `datasource_<something>.py` (the prefix is required — coshsh's loader filters on it) and placed in a directory listed in the recipe's `classes_dir`. Both relative and absolute paths work in `classes_dir`. Coshsh also searches its built-in `recipes/default/classes`, and these built-ins are usable from any recipe.

Conventional names: `datasource_<vendor>.py` (`datasource_netbox.py`), `datasource_<system>.py` (`datasource_cmdbuild.py`), `datasource_<format>.py` (`datasource_json.py`). Keep the name lowercase and short — the cookbook references the class indirectly through the `type =` field, not by filename, so the filename is for humans.

## The five required elements

Every datasource file must contain exactly these five things:

1. Imports (logging, coshsh modules, third-party libs).
2. A module-level `logger = logging.getLogger('coshsh')`.
3. The `__ds_ident__(params={})` function.
4. The class itself, inheriting from `coshsh.datasource.Datasource`.
5. The four methods on the class: `__init__`, `open`, `read`, `close`.

## `__ds_ident__(params={})`

```python
def __ds_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "mycmdb"):
        return MyCmdb
    return None
```

Called by coshsh's class loader for every `datasource_*.py` it finds. The first one that returns a non-`None` class wins. `params` is the full dict of the cookbook's `[datasource_<name>]` section, so `params['type']` is the `type =` line. You can match on any key, but matching on `type` is universal.

Use `compare_attr` not `==` when:

- You want regex matching: `compare_attr("type", params, ".*cmdb.*")`.
- You want case-insensitive matching: `compare_attr("type", params, "MyCmdb", ignorecase=True)`.
- You want negation: `compare_attr("type", params, "!boring_type")`.

Use `params.get("type") == "..."` when you need exact, case-sensitive match and want zero ambiguity.

**Return the class, not an instance.** `return MyCmdb`, never `return MyCmdb()`. The framework instantiates it.

**Multiple classes per file are allowed**, with one `__ds_ident__` that branches:

```python
def __ds_ident__(params={}):
    t = params.get("type", "")
    if t == "cmdb_v1": return CmdbV1
    if t == "cmdb_v2": return CmdbV2
    return None
```

This is useful when versions of the same system share a lot of code via a shared base class.

## `__init__(self, **kwargs)`

```python
def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.url = kwargs["url"]
    self.token = kwargs.get("token")
    self.timeout = int(kwargs.get("timeout", 30))
    self.tls_verify = coshsh.util.str2bool(kwargs.get("tls_verify", "yes"))
```

`kwargs` is everything from the `[datasource_<name>]` section, with cookbook keys as Python kwarg names. So a cookbook with `url = https://...` produces `kwargs['url']`. Required parameters: use `kwargs["..."]` (raises `KeyError` if missing — fine, the cookbook author will see it and fix). Optional with default: `kwargs.get("...", default)`.

**The `super().__init__(**kwargs)` call is non-negotiable** — it sets `self.name` (the datasource's name from the cookbook section), wires up the `add`/`get`/`getall`/`find` helpers, and most importantly assigns the class via the re-blessing mechanism. Skip it and `self.add` will fail with an AttributeError.

The base class also stores `self.objects = {}` initially — but this is rebound inside `read()` (see below).

**Type conversion belongs here.** Cookbook values are always strings. Parse ints, bools, lists in `__init__` so the rest of the class works with proper Python types. `coshsh.util.str2bool` handles `yes/no/true/false/on/off/1/0`.

**Don't open connections in `__init__`.** That's what `open()` is for. The constructor should be cheap, side-effect-free, and never raise — the framework instantiates the datasource just to check if it's the right one, and may instantiate it multiple times during cookbook parsing.

## `open(self)`

```python
def open(self):
    logger.info(f"open datasource {self.name}")
    try:
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {self.token}"
        r = self.session.get(f"{self.url}/health", timeout=self.timeout, verify=self.tls_verify)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise DatasourceNotAvailable(f"cannot reach {self.url}: {e}")
    return True
```

`open()` is called once before `read()`. Use it for anything that establishes a long-lived connection: HTTP session, DB cursor, LDAP bind, opening a large file. Quick file checks also belong here:

```python
def open(self):
    if not os.path.exists(self.dir):
        raise DatasourceNotAvailable(f"data directory {self.dir} not found")
    return True
```

Raise `DatasourceNotAvailable` (not generic `Exception`!) when the source is unreachable. The framework catches this and aborts the recipe cleanly with a useful log message; a generic exception produces an ugly traceback and may corrupt the PID lock.

Raise `DatasourceNotCurrent` if you have a cheap way to check that the source hasn't changed since the last run (e.g. file mtime, ETag) — coshsh will then re-use the previous output, skipping the whole `read/assemble/render/output` cycle. This is a huge optimization for slow sources but is optional.

## `read(self, filter=None, objects={}, force=False, **kwargs)`

The signature is fixed. Don't change parameter names.

```python
def read(self, filter=None, objects={}, force=False, **kwargs):
    self.objects = objects   # this is the recipe's shared registry
    ...
```

The crucial first line is `self.objects = objects`. The `objects` parameter is a *reference* to `recipe.objects` — when you call `self.add('hosts', h)`, the host goes into the recipe's shared store, visible to all subsequent datasources, the assemble phase, and the render phase. Without rebinding `self.objects` here, `self.add` writes to a useless empty dict.

`force` — if `True`, the user passed `--force` and any caching logic should be bypassed.

`filter` — the recipe's `filter = ...` string (may be `None`). Its interpretation is entirely up to your datasource. The convention is a comma-separated list of `key=value` or `key=~regex` pairs that limit which records you process. If you don't implement filtering, just ignore it.

### Adding items: the canonical pattern

```python
for row in raw_records:
    host_params = {
        'host_name': row['name'],
        'address':   row['ip'],
        'alias':     row.get('alias', row['name']),
    }
    # strip None and empty-string values — they render literally in templates
    host_params = {k: v for k, v in host_params.items() if v not in (None, '')}

    h = Host(host_params)
    self.add('hosts', h)

    # hostgroup membership lives on the host object
    if row.get('environment'):
        h.hostgroups.append(f"env_{row['environment'].lower()}")
    if row.get('site'):
        h.hostgroups.append(f"site_{row['site'].lower()}")

    # custom Nagios macros — keys must start with underscore
    h.macros = {
        '_SERIAL':   row.get('serial', ''),
        '_OWNER':    row.get('owner_email', ''),
    }

    # the OS application — convention: name='os', type=<lowercased os string>
    a = Application({
        'host_name': h.host_name,
        'name': 'os',
        'type': row['os_type'].lower(),
    })
    self.add('applications', a)
```

### Application fingerprints and collisions

The fingerprint of an Application is `host_name + name + type`. Two applications with the same fingerprint collide and the later one wins (with attribute merging). This is intentional and lets a second datasource enrich applications from the first.

If a host runs two instances of the same product (e.g. two Oracle DBs), use distinct `name` values:

```python
a1 = Application({'host_name': h.host_name, 'name': 'billing',   'type': 'oracle'})
a2 = Application({'host_name': h.host_name, 'name': 'reporting', 'type': 'oracle'})
self.add('applications', a1)
self.add('applications', a2)
```

### Creating monitoring details

Details are how you attach per-application repeating sub-records (filesystems, interfaces, URLs, ports) or scalar config (SNMP communities, credentials). Add them to `'details'` — `Item.resolve_monitoring_details()` in the assemble phase will route them to the right parent based on `host_name` + `name` + `type`.

```python
for fs in row.get('filesystems', []):
    md = MonitoringDetail({
        'host_name': h.host_name,
        'name': 'os',
        'type': row['os_type'].lower(),
        'monitoring_type': 'FILESYSTEM',
        'monitoring_0': fs['path'],
        'monitoring_1': fs['warn'],
        'monitoring_2': fs['crit'],
        'monitoring_3': fs.get('units', '%'),
    })
    self.add('details', md)
```

The `host_name` + `name` + `type` triple on the detail MUST match the application's triple — otherwise the detail dangles and silently has no effect. The slot mapping (`monitoring_0`, `monitoring_1`, ...) depends on the detail type; see `monitoring_details.md`.

### Contacts and contactgroups

```python
cg = ContactGroup({'contactgroup_name': 'unix_admins'})
self.add('contactgroups', cg)

c = Contact({
    'contact_name': 'jdoe',
    'alias': 'Jane Doe',
    'email': 'jdoe@example.com',
    'service_notification_period': '24x7',
    'host_notification_period': '24x7',
    'service_notification_options': 'w,u,c,r',
    'host_notification_options':    'd,u,r',
})
c.contactgroups.append('unix_admins')   # membership lives on the contact
self.add('contacts', c)

h.contact_groups.append('unix_admins')  # attach group to host
```

The historical lazy form `Contact('jdoe', 'WEBREADWRITE', 'jdoe@...', 'jdoe', '7x24')` (positional args matching contact_name, type, email, pager, period) also exists in some example code — modern code uses the dict-style constructor.

### Multi-datasource collaboration

When a recipe has `datasources = cmdb_api, csv_overrides`, both run in order, both write to the same `recipe.objects`. The second can read what the first wrote:

```python
def read(self, filter=None, objects={}, force=False, **kwargs):
    self.objects = objects
    # first datasource already populated hosts; we add applications to existing hosts
    for row in self._fetch_overrides():
        # find the host that the first datasource created
        existing = self.get('hosts', row['host_name'])
        if existing:
            # enrich it
            existing.alias = row.get('alias', existing.alias)
        else:
            logger.warning(f"override for unknown host {row['host_name']}, skipping")
```

`self.get(type_plural, fingerprint)` returns the item or `None`. `self.getall(type_plural)` returns a list of all items of that type. `self.find(type_plural, fingerprint)` returns `True`/`False`.

For looking up by host_name, the fingerprint of a Host *is* the host_name, so `self.get('hosts', 'web01')` works directly.

### Return value

Return `True` on success, `False` (or raise `DatasourceCorrupt`) on failure. The framework checks this — a `False` return aborts the recipe.

### Logging

Use `logger.info` for high-level progress (one line per phase), `logger.debug` for per-record detail, `logger.warning` for recoverable oddities, `logger.error` before raising. Don't `print()` — coshsh has structured log handling and `print()` bypasses it.

Useful log lines:

```python
logger.info(f"read {len(hosts)} hosts and {len(apps)} applications from {self.name}")
logger.debug(f"adding host {h.host_name} address={h.address}")
logger.warning(f"row {row['id']} has no host_name, skipping")
```

## `close(self)`

```python
def close(self):
    if hasattr(self, 'session'):
        self.session.close()
    return True
```

Called once after `read()`, even if `read()` raised. Clean up connections, file handles, temp files. Should be idempotent and never raise.

## Exception cheat sheet

| When                                    | Raise                       | Effect                                                                |
| --------------------------------------- | --------------------------- | --------------------------------------------------------------------- |
| Source unreachable (network, missing file) | `DatasourceNotAvailable`    | Recipe aborts cleanly with a log message; no PID lock issues          |
| Source reachable but unchanged          | `DatasourceNotCurrent`      | Recipe re-uses last output without re-rendering — major speedup       |
| Source returned bad data                | `DatasourceCorrupt`         | Recipe aborts with a clear error; existing output is left alone       |
| Programmer error / bug                  | Let it propagate            | Stack trace in log, recipe aborts                                     |

Import what you need: `from coshsh.datasource import Datasource, DatasourceNotAvailable, DatasourceNotCurrent, DatasourceCorrupt`.

## Patterns by source type

### REST API (most CMDBs)

```python
import requests
from coshsh.datasource import Datasource, DatasourceNotAvailable

class NetboxLite(Datasource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.url = kwargs["url"].rstrip("/")
        self.token = kwargs["token"]
        self.tls_verify = coshsh.util.str2bool(kwargs.get("tls_verify", "yes"))

    def open(self):
        self.s = requests.Session()
        self.s.headers["Authorization"] = f"Token {self.token}"
        try:
            self.s.get(f"{self.url}/api/", verify=self.tls_verify, timeout=10).raise_for_status()
        except Exception as e:
            raise DatasourceNotAvailable(f"netbox unreachable: {e}")
        return True

    def _paginate(self, path):
        url = f"{self.url}{path}"
        while url:
            j = self.s.get(url, verify=self.tls_verify, timeout=30).json()
            yield from j["results"]
            url = j.get("next")

    def read(self, filter=None, objects={}, force=False, **kwargs):
        self.objects = objects
        for d in self._paginate("/api/dcim/devices/?status=active"):
            ip = (d.get("primary_ip4") or {}).get("address", "").split("/")[0]
            if not ip:
                continue
            h = Host({'host_name': d['name'], 'address': ip})
            self.add('hosts', h)
        return True
```

### Database

```python
import psycopg2

class PgInventory(Datasource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dsn = kwargs["dsn"]

    def open(self):
        try:
            self.conn = psycopg2.connect(self.dsn)
        except psycopg2.OperationalError as e:
            raise DatasourceNotAvailable(f"db connect failed: {e}")
        return True

    def read(self, filter=None, objects={}, force=False, **kwargs):
        self.objects = objects
        with self.conn.cursor() as cur:
            cur.execute("SELECT host_name, ip, os_type FROM inventory.servers WHERE active")
            for host_name, ip, os_type in cur:
                self.add('hosts', Host({'host_name': host_name, 'address': ip}))
                self.add('applications', Application({
                    'host_name': host_name, 'name': 'os', 'type': os_type.lower(),
                }))
        return True

    def close(self):
        if hasattr(self, 'conn'):
            self.conn.close()
        return True
```

### File-based (JSON/YAML/XML)

```python
class JsonInventory(Datasource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.path = kwargs["path"]

    def open(self):
        if not os.path.exists(self.path):
            raise DatasourceNotAvailable(f"{self.path} not found")
        # optional: cheap unchanged-check
        if not self._force_flag and self._mtime_unchanged():
            raise DatasourceNotCurrent
        return True

    def read(self, filter=None, objects={}, force=False, **kwargs):
        self.objects = objects
        with open(self.path) as f:
            data = json.load(f)
        for d in data["hosts"]:
            self.add('hosts', Host(d))
        return True
```

### In-memory / synthetic (testing)

```python
class SimpleSample(Datasource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def open(self):
        return True

    def read(self, filter=None, objects={}, force=False, **kwargs):
        self.objects = objects
        for name, ip, os_ in [('web01', '10.0.0.1', 'linux'), ('db01', '10.0.0.2', 'linux')]:
            self.add('hosts', Host({'host_name': name, 'address': ip}))
            self.add('applications', Application({'host_name': name, 'name': 'os', 'type': os_}))
        return True

    def close(self):
        return True
```

`recipes/default/classes/datasource_simplesample.py` is the canonical reference for this pattern and is a fine starting point for quick tests.

### "Wipe everything" — discard pattern

`recipes/default/classes/datasource_discard.py` clears `recipe.objects`. Place it last in the `datasources =` list to suppress all output of a recipe (useful when the recipe's only purpose is side effects from earlier datasources, e.g. updating an external database).

## Filtering

If you implement the `filter` parameter, the convention is a string like `os_type=linux,environment=~prod.*`:

```python
def _parse_filter(self, fstr):
    """parses 'key=value,key2=~regex' into list of (key, op, value) tuples"""
    if not fstr:
        return []
    rules = []
    for clause in fstr.split(","):
        clause = clause.strip()
        if "=~" in clause:
            k, v = clause.split("=~", 1)
            rules.append((k.strip(), "regex", v.strip()))
        else:
            k, v = clause.split("=", 1)
            rules.append((k.strip(), "eq", v.strip()))
    return rules

def _passes_filter(self, row, rules):
    for k, op, v in rules:
        actual = str(row.get(k, ""))
        if op == "eq" and actual != v:
            return False
        if op == "regex" and not re.search(v, actual):
            return False
    return True
```

Pass the parsed rules into your record loop. Filtering is the right place to enforce environment-based separation between recipes (one recipe for prod, one for dev, both pointing at the same datasource with different filters).

## Performance

coshsh routinely handles tens of thousands of hosts. To stay fast:

- Batch your API/DB queries — one call returning 10000 rows beats 10000 calls returning one row.
- Lazy-fetch details only for hosts you actually emit (use `for` over hosts and fetch details inline rather than pre-fetching all).
- Don't build per-host dicts that you then iterate again — emit items as you encounter them.
- Use `force=True` and a real `DatasourceNotCurrent` check (file mtime, API ETag, DB max(updated_at)) to skip unchanged runs.

A 60000-service recipe should finish in well under a minute. If yours doesn't, the time is almost always in the datasource's data fetch, not in coshsh's own machinery.

## Common pitfalls

1. **Forgetting `self.objects = objects` at the top of `read()`.** Items go nowhere, no error, empty output.
2. **Mismatched casing in `type`.** The framework lowercases application types before `__mi_ident__` matches. Lowercase in your datasource for symmetry.
3. **Passing `None` into constructors.** Renders as literal `None` in Nagios configs. Always strip.
4. **Forgetting `super().__init__(**kwargs)`.** `self.add` raises AttributeError.
5. **Raising generic `Exception` in `open()`.** No clean abort, possible PID lock corruption.
6. **Mutating `self.objects` directly.** Breaks the fingerprinting system. Always use `self.add`.
7. **Naming the file `mydatasource.py` instead of `datasource_my.py`.** Silently ignored.
8. **Returning `MyClass()` from `__ds_ident__`.** TypeError later when the framework tries to instantiate it again with `**kwargs`.

## Studying real examples

When asked to write a datasource for a specific system, search for prior art in coshsh's tree:

- `recipes/default/classes/datasource_csvfile.py` — complete, polished, handles hosts/apps/details/contacts/contactgroups all from CSV. Excellent reference.
- `recipes/default/classes/datasource_simplesample.py` — minimal in-memory example.
- `contrib/classes/datasource_netbox.py` — NetBox API integration.
- `contrib/classes/datasource_svcnow_cmdb_ci.py` — ServiceNow CMDB integration.

When in doubt, mimic the structure of the closest existing example.
