# MonitoringDetail — per-application repeating data and credentials

A `MonitoringDetail` is a piece of structured data attached to a host or application: a filesystem, an interface, a port, a URL, a credential. Each detail has a `monitoring_type` that selects how it's interpreted, and `monitoring_0..N` slots that carry the data. At assemble time, coshsh routes details to their parent items and transforms them into clean attributes (a list of filesystem objects, a single SNMP credential object, etc.).

## When you use details vs plain attributes

Use a **monitoring detail** when:

- The data is repeating per-application (filesystems, interfaces, URLs, ports).
- The data is structured (a credential is path + community + version, not a single string).
- A built-in detail type already exists for what you have (avoid re-inventing).
- You want the data to live in a separate normalized table in your CMDB / CSV.

Use a **plain attribute on the Application** (set in datasource or `__init__`) when:

- The data is a single scalar (`port=8080`, `version="19c"`).
- The data is application-wide, not per-resource.
- You have no built-in detail type that fits.

## Anatomy of a detail

```python
md = MonitoringDetail({
    'host_name':       'web01',         # foreign key part 1
    'name':            'os',            # foreign key part 2 — matches Application.name
    'type':            'linux',         # foreign key part 3 — matches Application.type
    'monitoring_type': 'FILESYSTEM',    # selects detail_filesystem.py
    'monitoring_0':    '/var',
    'monitoring_1':    '85%',
    'monitoring_2':    '95%',
    'monitoring_3':    '%',
})
self.add('details', md)
```

The `host_name + name + type` triple identifies the parent. If those three don't match an existing Application's fingerprint, the detail dangles silently — no error, no output, just no effect. **This is the #1 silent failure in coshsh.** Always verify the triple matches.

To attach a detail to the host itself (not an application), omit `name` and `type` (or use empty strings). Most details attach to applications; host-level details are rare and depend on the specific detail type's implementation.

`monitoring_0` through `monitoring_N` are data slots; their meaning depends on `monitoring_type` and is defined by the corresponding `detail_*.py` class in `recipes/default/classes/`.

## Built-in detail types

These are shipped with coshsh in `recipes/default/classes/`. Each has a `detail_<name>.py` defining the slot mapping and a `property` attribute that becomes the attribute name on the parent.

### List-typed (repeat per application)

These produce a list on the application. The template iterates with `{% for x in application.<property> %}`.

| `monitoring_type` | Slots                                                                       | Becomes                              |
| ----------------- | --------------------------------------------------------------------------- | ------------------------------------ |
| `FILESYSTEM`      | 0=path, 1=warning, 2=critical, 3=units (e.g. `%`, `GB`, `MB`)                | `application.filesystems` (list)     |
| `PORT`            | 0=port, 1=protocol (tcp/udp), 2=service_name, 3=warning, 4=critical          | `application.ports` (list)           |
| `INTERFACE`       | 0=name, 1=alias, 2=index, 3=speed, 4=duplex (varies by deployment)           | `application.interfaces` (list)      |
| `URL`             | 0=url, 1=name, 2=timeout, 3=expected_status_or_string                        | `application.urls` (list)            |
| `DATASTORE`       | 0=name, 1=warning, 2=critical, 3=units                                       | `application.datastores` (list)      |
| `TABLESPACE`      | 0=name, 1=warning, 2=critical, 3=units                                       | `application.tablespaces` (list)     |
| `VOLUME`          | 0=name, 1=warning, 2=critical, 3=units                                       | `application.volumes` (list)         |
| `PROCESS`         | 0=process_name, 1=min_instances, 2=max_instances                             | `application.processes` (list)       |
| `ROLE`            | 0=role_name (plus per-role data)                                             | `application.roles` (list)           |
| `TAG`             | 0=tag                                                                        | `application.tags` (list)            |
| `SOCKET`          | 0=path, 1=type (used for unix sockets, named pipes)                          | `application.sockets` (list)         |

### Scalar (one per application)

Adding the same scalar type twice overwrites — the last one wins. Templates access as `{{ application.<property>.<field> }}`.

| `monitoring_type` | Slots                                                                  | Becomes                                                  |
| ----------------- | ---------------------------------------------------------------------- | -------------------------------------------------------- |
| `LOGIN`           | 0=username, 1=password, 2=optional auth method                          | `application.login` with `.username`, `.password`        |
| `LOGINSNMPV2`     | 0=community, 1=protocol (snmp version)                                  | `application.snmpv2` with `.community`, `.protocol`      |
| `LOGINSNMPV3`     | 0=securityname, 1=authpass, 2=privpass, 3=authproto, 4=privproto         | `application.snmpv3` with corresponding fields           |
| `ACCESS`          | 0=method, 1=host, 2=user, 3=password (e.g. ssh credentials)             | `application.access`                                     |
| `KEYVALUES`       | 0=key, 1=value (one per detail, but multiple details build up a dict)   | merges values into `application.keyvalues` (dict)        |
| `DEPTH`           | 0=numeric depth marker                                                  | `application.depth`                                      |
| `NAGIOSCONF`      | 0=key, 1=value — directly written into the Nagios object definition    | injected as `define ... { <key> <value> }` line          |
| `NAGIOS`          | similar to NAGIOSCONF (legacy variant; check the detail_*.py source)    | varies                                                   |

`KEYVALUES` is the catch-all for "I want to set a custom attribute via a detail row". One row per key:

```python
self.add('details', MonitoringDetail({
    'host_name': 'web01', 'name': 'os', 'type': 'linux',
    'monitoring_type': 'KEYVALUES',
    'monitoring_0': 'maintenance_window',
    'monitoring_1': 'sat 02:00-04:00',
}))
```

Then in the template: `{{ application.maintenance_window }}` or `{{ application.keyvalues.maintenance_window }}` depending on the detail's implementation (check `detail_keyvalues.py`).

`NAGIOSCONF` is the escape hatch for "I need to inject a Nagios directive that coshsh doesn't model directly":

```python
self.add('details', MonitoringDetail({
    'host_name': 'web01',
    'monitoring_type': 'NAGIOSCONF',
    'monitoring_0': 'icon_image',
    'monitoring_1': 'linux40.png',
}))
```

renders an `icon_image linux40.png` line into the host definition. Use sparingly — the right answer is usually a proper attribute and a template.

## Inspecting the built-in detail classes

Don't guess slot meanings — read the source. In coshsh's tree:

```
recipes/default/classes/
├── detail_access.py
├── detail_datastore.py
├── detail_depth.py
├── detail_filesystem.py
├── detail_interface.py
├── detail_keyvalues.py
├── detail_login.py
├── detail_loginsnmpv2.py
├── detail_loginsnmpv3.py
├── detail_nagios.py
├── detail_nagiosconf.py
├── detail_port.py
├── detail_process.py
├── detail_role.py
├── detail_socket.py
├── detail_tablespace.py
├── detail_tag.py
├── detail_url.py
└── detail_volume.py
```

Each file is short (typically 20-60 lines) and contains the `monitoring_type`, the slot-to-attribute mapping, the `property` name, and `property_type` (list vs scalar). When the docs are ambiguous, read the source — it's faster than reverse-engineering from log output.

## Writing a custom `detail_*.py`

For data shapes the built-ins don't cover.

```python
# detail_certificate.py
from coshsh.monitoringdetail import MonitoringDetail

def __detail_ident__(params={}):
    if params.get("monitoring_type") == "CERTIFICATE":
        return MonitoringDetailCertificate
    return None

class MonitoringDetailCertificate(MonitoringDetail):
    property = "certificates"        # becomes application.certificates
    property_type = list             # multiple allowed; result is a list

    def __init__(self, params={}):
        super().__init__(params)
        self.hostname    = params.get("monitoring_0")
        self.port        = int(params.get("monitoring_1", 443))
        self.warn_days   = int(params.get("monitoring_2", 30))
        self.crit_days   = int(params.get("monitoring_3", 7))
        self.sni         = params.get("monitoring_4", self.hostname)
```

Each detail instance has clean named attributes after `__init__`, so templates do `{{ cert.hostname }}` not `{{ cert.monitoring_0 }}`.

For scalar (one-per-application) details, set `property_type = "scalar"` or use a class without that attribute (depending on coshsh version — check an existing scalar detail like `detail_loginsnmpv2.py`).

Place the file in `classes_dir` alongside your other classes. Coshsh's loader finds it via the `detail_` prefix.

## Datasource patterns for creating details

### Inline with the application

```python
for row in db_rows:
    a = Application({'host_name': row['host'], 'name': 'os', 'type': row['os'].lower()})
    self.add('applications', a)

    for fs_row in db_fs_rows_for(row['host']):
        md = MonitoringDetail({
            'host_name': a.host_name, 'name': a.name, 'type': a.type,
            'monitoring_type': 'FILESYSTEM',
            'monitoring_0': fs_row['path'],
            'monitoring_1': fs_row['warn'],
            'monitoring_2': fs_row['crit'],
            'monitoring_3': '%',
        })
        self.add('details', md)
```

The `host_name + name + type` triple is borrowed from the just-created application to guarantee they match.

### From a separate "details table"

```python
for d_row in self._fetch_details():  # already has host_name/name/type/monitoring_*
    md = MonitoringDetail(d_row)
    self.add('details', md)
```

When your CMDB already has a per-host-app details table with matching column names, this one-liner is all you need.

### Helper: build a detail-row from another shape

When the source's column names don't match coshsh's expectations:

```python
def _make_fs_detail(self, host_name, app_name, app_type, fs):
    return MonitoringDetail({
        'host_name': host_name, 'name': app_name, 'type': app_type,
        'monitoring_type': 'FILESYSTEM',
        'monitoring_0': fs['mount_point'],
        'monitoring_1': str(fs['warn_pct']) + '%',
        'monitoring_2': str(fs['crit_pct']) + '%',
        'monitoring_3': '%',
    })
```

## Using details in templates

```jinja
{# default template, no details needed #}
{{ application|service("os_linux_load") }}
    host_name      {{ application.host_name }}
    check_command  check_load
}
```

```jinja
{# fs template, gated by needsattr="filesystems" in the rule #}
{% for fs in application.filesystems %}
{{ application|service("os_linux_fs_" + (fs.path | re_sub('[^a-zA-Z0-9_-]', '_'))) }}
    host_name      {{ application.host_name }}
    check_command  check_disk!{{ fs.warning }}!{{ fs.critical }}!{{ fs.path }}!{{ fs.units }}
}
{% endfor %}
```

```jinja
{# snmp template, gated by needsattr="snmpv2" #}
{{ application|service("os_cisco_ios_uptime") }}
    host_name      {{ application.host_name }}
    check_command  check_snmp_uptime!{{ application.snmpv2.community }}!{{ application.snmpv2.protocol }}
}
```

The attribute names (`fs.path`, `fs.warning`, `application.snmpv2.community`) come from the `detail_*.py` `__init__` method — these are clean Python attribute names, not `monitoring_0` slot accesses.

## Pitfalls

1. **Mismatched host_name/name/type triple.** The most common silent failure. The detail's triple MUST match an existing application's fingerprint. If you don't see expected service definitions, log the application's `(host_name, name, type)` and your details' triples and compare.
2. **Adding a duplicate scalar detail.** Last write wins; earlier ones are clobbered. Add scalars once per application.
3. **Using a `monitoring_type` value without a matching `detail_*.py`.** The detail is created and stored but never resolved into a structured attribute. Templates relying on `needsattr="my_thing"` won't fire.
4. **Bypassing the resolution machinery.** Don't `application.filesystems = [...]` from your datasource — that overrides what the framework will assemble. Add `FILESYSTEM` details and let assemble do the work. (Exception: when you have data the built-ins can't represent and don't want to write a `detail_*.py`, setting an attribute directly is the escape hatch.)
5. **String vs number in numeric slots.** `monitoring_2 = 95` (int) vs `monitoring_2 = "95"` (string) — Jinja2 will render both fine, but template arithmetic (`{{ fs.warning | int + 5 }}`) needs cleanly-typed values. Set types correctly in your custom `detail_*.py`'s `__init__`.
6. **Forgetting to `self.add('details', md)`.** Creating the object alone has no effect; only `add` registers it in `recipe.objects['details']` where assemble looks.
