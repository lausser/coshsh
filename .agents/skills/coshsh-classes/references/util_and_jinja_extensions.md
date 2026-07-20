# coshsh.util and Custom Jinja2 Extensions

## `coshsh.util` — module-level helper functions

The `coshsh.util` module collects the small, dependency-free helpers that coshsh uses throughout. Import what you need; these are stable and safe to use in user code.

### `compare_attr(attr_name, params, value, ignorecase=False)`

The workhorse for identifier functions and any "does this thing match" check. Compares `params[attr_name]` to `value` with regex, equality, or negation semantics depending on the `value` string's prefix.

```python
from coshsh.util import compare_attr

# regex match (most common form)
compare_attr("type", params, ".*windows.*")            # True if params["type"] matches /.*windows.*/

# case-insensitive regex
compare_attr("type", params, "linux", ignorecase=True)

# negation: with leading "!"
compare_attr("type", params, "!boring_type")           # True if params["type"] != "boring_type"

# negative regex: with leading "!~"
compare_attr("name", params, "!~temp_.*")              # True if name doesn't start with temp_
```

Returns `True` or `False`. Returns `False` (not an error) if `attr_name` is missing from `params`.

Use this in every `__ds_ident__` and `__mi_ident__` instead of raw string equality unless you specifically want exact case-sensitive matching with no regex.

### `is_attr(attr_name, params, value, ignorecase=False)`

Like `compare_attr` but simpler — only exact equality, no regex. Effectively `params.get(attr_name) == value` with optional case-insensitive comparison. Mostly historical; `compare_attr` is preferred for new code.

### `substenv(text)`

Expands `%(VAR)%` and `%VAR%` placeholders in a string from the OS environment.

```python
from coshsh.util import substenv
path = substenv("%(OMD_ROOT)%/etc/coshsh")
# → "/omd/sites/prod/etc/coshsh" if OMD_ROOT is set
```

Called automatically by the cookbook parser on every value. You rarely need to call it explicitly, but it's handy when constructing paths in custom datasource code.

### `str2bool(value)`

Parses common boolean string representations.

```python
from coshsh.util import str2bool

str2bool("yes")    # True
str2bool("no")     # False
str2bool("true")   # True
str2bool("0")      # False
str2bool(True)     # True (pass-through)
```

Accepts `yes`/`no`, `true`/`false`, `on`/`off`, `1`/`0`, in any case. Use it in datasource `__init__` to convert cookbook string values like `tls_verify = no` into proper bools.

### `setup_logging(...)`, `switch_logging(...)`, `restore_logging()`

Internal — called by `Generator` and `Recipe`. You don't call these from extension code. Just `logger = logging.getLogger('coshsh')` at the top of your module and use it.

### `odict()`

Historical ordered-dict class. Since Python 3.7, the built-in `dict` is ordered. Don't use `odict` in new code.

### Internal module-loading helpers

`load_python_module`, the `CoshshDatainterface` parent class, and the re-blessing mechanism are framework internals. You interact with them only indirectly via `__ds_ident__` / `__mi_ident__` / `__dr_ident__`. Don't import them in user code.

## Writing Custom Jinja2 Extensions

When the built-in filters/tests/globals aren't enough, write your own.

### How registration works

In your recipe, list extensions:

```ini
[recipe_my_recipe]
my_jinja2_extensions = my_module.filter_uppercase_first, my_module.is_recent, my_module.global_now
```

Coshsh:

1. Imports `my_module` (must be importable from `classes_dir` or Python's `sys.path`).
2. Looks up each function by name.
3. Registers based on the name prefix:
   - `filter_<name>` → Jinja2 filter usable as `{{ x | name }}`
   - `is_<name>` → Jinja2 test usable as `{% if x is name %}`
   - `global_<name>` → Jinja2 global usable as `{{ name() }}` or `{{ name }}`

The naming convention is what makes it work — without the prefix, the framework doesn't know how to register.

### Custom filter

```python
# my_module.py
def filter_uppercase_first(value):
    return str(value).capitalize()

def filter_kvfmt(d, sep=" "):
    return sep.join(f"{k}={v}" for k, v in d.items())

def filter_sanitize_nagios_name(value):
    import re
    return re.sub(r'[^a-zA-Z0-9_-]', '_', str(value))
```

Template usage:

```jinja
host_name {{ application.name | uppercase_first }}
labels    {{ application.labels | kvfmt(", ") }}
service_description {{ application | service("fs_" + (fs.path | sanitize_nagios_name)) }}
```

### Custom test

```python
def is_recent(value, days=7):
    """test whether a date string is within `days` days of now"""
    import datetime
    if not value:
        return False
    try:
        dt = datetime.datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return (datetime.datetime.now() - dt).days < days

def is_prod(host):
    return host.host_name.startswith("prod-")
```

Template usage:

```jinja
{% if application.last_seen is recent(30) %}
  use generic-service
{% else %}
  use stale-service
{% endif %}

{% if host is prod %}
  contact_groups oncall_24x7
{% endif %}
```

### Custom global

Globals are functions you can call (or sometimes values) from any template, without a "this" object.

```python
def global_run_id():
    """uniquely identify this coshsh run"""
    import os, time
    return f"{os.getpid()}-{int(time.time())}"

def global_safe_check(name):
    """return a sanitized check command name"""
    import re
    return re.sub(r'[^a-z0-9_]', '_', name.lower())
```

Template usage:

```jinja
# generated by coshsh run {{ run_id() }}
check_command {{ safe_check(application.type) }}
```

### Tips for writing extensions

- Keep filters pure (no side effects, deterministic). Templates may re-render or be cached.
- Handle `None` and missing values defensively. `application.foo` may not exist on every instance.
- Use Python type hints for clarity — they don't constrain Jinja2 but help maintainers.
- Place extension modules in `classes_dir` so they're discovered automatically.
- One module can export many extensions — they're individually registered by the prefix-naming.

### Built-in extensions to study

`coshsh/jinja2_extensions.py` in coshsh's source defines the built-in filters (`service`, `host`, `contact`, `custom_macros`, `re_sub`, `re_escape`, `rfc3986`, `neighbor_applications`) and globals (`environ`). Read it as a reference for idiomatic style — the source is short and well-organized.

## Pitfalls

1. **Wrong prefix.** `def my_filter(x)` is not registered as a filter. Must be `filter_my_filter`.
2. **Module not in `sys.path`.** Coshsh adds `classes_dir` entries to `sys.path` automatically, so placing your module there works. Placing it elsewhere requires manually adding the directory.
3. **Side effects in filters.** Filters get called during render. Side effects (DB writes, API calls) make rendering non-idempotent. Don't.
4. **Exceptions in extensions.** A raised exception aborts the template render for that item. Catch and return a safe default value when possible.
5. **Trying to use Jinja2 environment-level features.** Coshsh's Jinja2 environment is shared across all templates; you can't add `extensions=[...]` (Jinja2's lib-level extensions like `do`, `loopcontrols`) from user code. Filter/test/global registration is the supported extension point.
