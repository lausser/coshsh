# Writing .tpl Templates (Jinja2)

A `.tpl` file is a Jinja2 template that renders into a configuration block. Coshsh feeds each item (Host, Application, ...) through its associated templates during the render phase, producing strings that the datarecipient writes to files. Templates are where the Nagios `define host { ... }`, `define service { ... }`, `define contact { ... }` blocks actually live.

## File location and naming

Templates go in a `templates_dir` listed by the recipe. The filename is `<template_name>.tpl` where `<template_name>` matches the `template=` parameter of a `TemplateRule`. Coshsh ships defaults in `recipes/default/templates/` — these are searched too, so you can override a default by putting a same-named file in your recipe's `templates_dir`.

Conventional names mirror class names:

- `host.tpl` — the generic host definition (one is required somewhere in the search path).
- `os_linux_default.tpl`, `os_linux_fs.tpl`, `os_windows_default.tpl`, ... — per OS, per add-on.
- `app_oracle_default.tpl`, `app_apache_vhosts.tpl`, ... — per application, per add-on.
- `contact.tpl`, `contactgroup.tpl`, `hostgroup.tpl` — for the corresponding object types.

## What's in scope inside a template

The variable name depends on the item being rendered:

- Host templates see `host` — `{{ host.host_name }}`, `{{ host.address }}`, `{{ host.macros }}`, `{{ host.hostgroups }}`, `{{ host.alias }}`.
- Application templates see `application` — `{{ application.host_name }}`, `{{ application.name }}`, `{{ application.type }}`, plus every attribute the datasource or class set.
- Contact templates see `contact`. Contactgroup templates see `contactgroup`. Hostgroup templates see `hostgroup`.

Every attribute that exists on the Python object is reachable from the template, including:

- Attributes from the datasource row (whatever keys you put in the dict passed to the constructor).
- Attributes set in your custom `__init__`.
- Attributes from resolved monitoring details (`application.filesystems`, `application.snmpv2`, etc.).
- Method results — call them with `()`: `{{ application.fingerprint() }}`.
- The parent host of an application: `{{ application.host.address }}` (set during assemble).

## Coshsh's custom Jinja2 filters

These come built-in from `coshsh/jinja2_extensions.py`. They make templates concise and idiomatic.

### `|service("name")`

The most important filter. Renders the canonical service header line and registers the service for uniqueness tracking. Use it at the start of every `define service` block.

```jinja
{{ application|service("os_linux_check_load") }}
    host_name      {{ application.host_name }}
    check_command  check_load!5.0,4.0,3.0!10.0,8.0,5.0
    use            generic-service
}
```

Expands roughly to:

```
define service {
    service_description    os_linux_check_load
```

The exact expansion is internal — just use the filter and never write `define service { service_description ...` by hand. The filter ensures unique service descriptions and may add framework-managed attributes.

### `|host("name")` and `|contact("name")`

The host and contact equivalents. Typically used in `host.tpl` and `contact.tpl`:

```jinja
{{ host|host(host.host_name) }}
    address       {{ host.address }}
    alias         {{ host.alias | default(host.host_name) }}
    {{ host|custom_macros }}
}
```

### `|custom_macros`

Renders an item's `macros` dict as Nagios macro lines:

```jinja
{{ host|custom_macros }}
```

For `host.macros = {'_LOCATION': 'dc1', '_SERIAL': 'X37'}`, expands to:

```
    _LOCATION    dc1
    _SERIAL      X37
```

Always include this in `host.tpl` and any application template where you want custom macros to surface. Without it, the macros dict is set but never rendered.

### `|re_sub(pattern, replacement)`

Regex substitution. Indispensable for sanitizing free-form data into Nagios-safe identifiers.

```jinja
{{ application|service("fs_" + (fs.path | re_sub('[^a-zA-Z0-9_-]', '_'))) }}
```

Turns `/var/log` into `_var_log`, producing `fs__var_log`. Nagios service descriptions can't contain certain characters; `re_sub` is your cleanup tool.

### `|re_escape`

Escapes a string for use inside a regex pattern.

```jinja
{{ "8.7.x" | re_escape }}    {# → 8\.7\.x #}
```

### `|rfc3986`

URL-encodes a string per RFC 3986. Useful when constructing check_http URLs with parameters.

```jinja
check_http -u "/health?service={{ application.name | rfc3986 }}"
```

### `|neighbor_applications(name=..., type=...)`

Returns other applications on the same host, optionally filtered by name or type. Useful for cross-app dependencies — "if this app is on a host that also runs Oracle, add an Oracle-dependency check".

```jinja
{% set oracles = application | neighbor_applications(type="oracle") %}
{% if oracles %}
{# this host runs oracle; reference it here #}
{% for o in oracles %}
    {# ... #}
{% endfor %}
{% endif %}
```

## Built-in globals

### `environ`

The OS environment, accessible as a dict-like object.

```jinja
{# Different commands per OMD site #}
check_command  check_by_ssh!--site {{ environ.OMD_SITE }}!check_health
```

## Standard Jinja2 features

Coshsh imposes no restrictions on Jinja2; the full feature set is available.

### Conditionals

```jinja
{% if application.is_clustered %}
    {# ... clustered-only services ... #}
{% else %}
    {# ... standalone-only services ... #}
{% endif %}
```

### Loops over details

```jinja
{% for fs in application.filesystems %}
{{ application|service("os_linux_fs_" + (fs.path | re_sub('[^a-zA-Z0-9_-]', '_'))) }}
    host_name       {{ application.host_name }}
    check_command   check_disk!{{ fs.warning }}!{{ fs.critical }}!{{ fs.path }}!{{ fs.units }}
}
{% endfor %}
```

### Filters: defaults and conversions

```jinja
host_name   {{ host.host_name }}
alias       {{ host.alias | default(host.host_name) }}
parents     {{ host.parents | join(",") | default("") }}
notification_period  {{ host.notification_period | default("24x7") }}
contact_groups       {{ host.contact_groups | join(",") }}
```

`default(...)` is critical — applies the fallback when the attribute is undefined or empty. Without it, missing attributes raise `UndefinedError` and the template fails to render.

### Macros (reusable template chunks)

Jinja2 has its own macro feature (different from Nagios macros):

```jinja
{# at the top of the template, or in a separate file imported with {% import %} #}
{% macro service_block(app, name, command) %}
{{ app|service(name) }}
    host_name       {{ app.host_name }}
    check_command   {{ command }}
    use             generic-service
}
{% endmacro %}

{# ... later ... #}
{{ service_block(application, "os_linux_load", "check_load") }}
{{ service_block(application, "os_linux_users", "check_users") }}
```

This is great for repetitive service blocks within one OS.

### Comments

```jinja
{# this is a Jinja2 comment, stripped from output #}
# this is a comment, included literally in the output (Nagios syntax)
```

## A complete `host.tpl`

```jinja
define host {
    use             generic-host
    host_name       {{ host.host_name }}
    address         {{ host.address }}
    alias           {{ host.alias | default(host.host_name) }}
{% if host.parents %}
    parents         {{ host.parents | join(",") }}
{% endif %}
{% if host.hostgroups %}
    hostgroups      {{ host.hostgroups | join(",") }}
{% endif %}
{% if host.contact_groups %}
    contact_groups  {{ host.contact_groups | join(",") }}
{% endif %}
    {{ host|custom_macros }}
}
```

## A complete application template (`os_linux_default.tpl`)

```jinja
{{ application|service("os_linux_check_ping") }}
    host_name       {{ application.host_name }}
    check_command   check_ping!100.0,20%!500.0,60%
    use             generic-service
}

{{ application|service("os_linux_check_load") }}
    host_name       {{ application.host_name }}
    check_command   check_load!5,4,3!10,8,6
    use             generic-service
}

{{ application|service("os_linux_check_users") }}
    host_name       {{ application.host_name }}
    check_command   check_users!5!10
    use             generic-service
}

{{ application|service("os_linux_check_ssh") }}
    host_name       {{ application.host_name }}
    check_command   check_ssh
    use             generic-service
}
```

## A complete add-on template (`os_linux_fs.tpl`)

```jinja
{% for fs in application.filesystems %}
{{ application|service("os_linux_fs_" + (fs.path | re_sub('[^a-zA-Z0-9_-]', '_'))) }}
    host_name       {{ application.host_name }}
    check_command   check_disk!{{ fs.warning }}!{{ fs.critical }}!{{ fs.path }}
    use             generic-service
    notes           {{ fs.units | default('%') }} thresholds
}
{% endfor %}
```

## Custom Jinja2 extensions

You can add your own filters, tests, and globals beyond coshsh's built-ins. Define them in a Python module, place it in a `classes_dir`, and list them in the recipe:

```ini
[recipe_my_recipe]
my_jinja2_extensions = my_helpers.filter_kvfmt, my_helpers.is_prod_host
```

The naming convention:

- `filter_<name>` → registers as filter `name`, usable as `{{ x | name }}`.
- `is_<name>` → registers as test `name`, usable as `{% if x is name %}`.
- `global_<name>` → registers as global, usable as `{{ name() }}` or `{{ name }}`.

```python
# my_helpers.py
def filter_kvfmt(d, sep=" "):
    """Render a dict as space-separated key=value pairs."""
    return sep.join(f"{k}={v}" for k, v in d.items())

def is_prod_host(host):
    return host.host_name.startswith("prod-")

def global_now():
    import datetime
    return datetime.datetime.now().isoformat()
```

Template usage:

```jinja
{# {{ application.labels | kvfmt }} → key1=val1 key2=val2 #}

{% if host is prod_host %}
    notification_options  d,u,r,f,s
{% endif %}

# generated at {{ now() }}
```

## Pitfalls

1. **`UndefinedError: 'x' is undefined`.** The template references an attribute that doesn't exist on the item. Either set the attribute in the datasource/`__init__`, or use `{{ x | default(...) }}`.
2. **Missing newline after `{{ ... }}`.** Jinja2 strips trailing newlines around tags differently than you might expect. If output looks merged, add explicit newlines or use `{%- ... -%}` (with hyphens) to control whitespace.
3. **Hand-writing `define service { service_description X` instead of `{{ application|service("X") }}`.** Loses framework-managed registration and risks duplicate service descriptions.
4. **Slashes and spaces in service descriptions.** Nagios doesn't allow many special characters in `service_description`. Always pipe through `|re_sub('[^a-zA-Z0-9_-]', '_')` when constructing names from free-form data.
5. **Forgetting `{{ host|custom_macros }}` in `host.tpl`.** Custom macros set in the datasource never appear in the generated config.
6. **Loops without `needsattr` gating.** `{% for fs in application.filesystems %}` with no `needsattr="filesystems"` in the rule just produces an empty loop when filesystems is missing — but it also creates a (possibly empty) output file. Better: gate the rule so the file isn't generated at all.
7. **Wrong variable name.** Application templates use `application`, host templates use `host`, contact templates use `contact`. Mixing them up produces `UndefinedError`.
