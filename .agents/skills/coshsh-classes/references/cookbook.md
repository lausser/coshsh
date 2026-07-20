# Cookbook and Recipe Configuration (.cfg)

A cookbook is an INI-style file that tells `coshsh-cook` what to do. It lives at e.g. `/etc/coshsh/conf.d/myrecipe.cfg` (in OMD) or anywhere else you point `--cookbook` at. Multiple cookbooks can be combined in one invocation; their sections are merged.

## Section types

| Section header                       | Purpose                                                                |
| ------------------------------------ | ---------------------------------------------------------------------- |
| `[defaults]`                         | Global defaults (paths, log level, recipe list)                        |
| `[recipe_<name>]`                    | A single generation task: data sources → classes → templates → output  |
| `[datasource_<name>]`                | A data source (referenced from a recipe's `datasources =`)             |
| `[datarecipient_<name>]`             | A custom output handler (referenced from a recipe's `datarecipients =`) |
| `[mapping_<name>]`                   | Simple key→value lookup tables usable in other section values          |
| `[prometheus_pushgateway]`           | Optional integration for pushing metrics about the coshsh run           |

Section names use underscores: `[recipe_prod_linux]`, not `[recipe prod linux]` or `[recipe-prod-linux]`. The token after the first `_` is the user-visible name referenced elsewhere.

## Variable substitution

Two layers:

- **Environment variables**: `%(VARNAME)%` or `%VARNAME%`. Resolved at parse time. `%(OMD_ROOT)%` is the typical one. Done by `coshsh.util.substenv`.
- **Mapping references**: `@{MAPPING_NAME[key]}` looks up `key` in `[mapping_name]`. Useful for short shared strings.

```ini
[mapping_regions]
de = europe-west1
us = us-east1

[recipe_eu]
description = Region @{MAPPING_REGIONS[de]}
classes_dir = %(OMD_ROOT)%/local/etc/coshsh/classes
```

## `[recipe_<name>]`

The central section. Each recipe is one generation task with its own datasources, classes, templates, and output destination.

```ini
[recipe_prod_linux]
datasources    = cmdb, csv_overrides
classes_dir    = %(OMD_ROOT)%/local/etc/coshsh/recipes/prod/classes
templates_dir  = %(OMD_ROOT)%/local/etc/coshsh/recipes/prod/templates
objects_dir    = %(OMD_ROOT)%/etc/naemon/conf.d/generated/prod_linux
filter         = cmdb(env=production,os=~linux.*)
git_init       = yes
max_delta      = 10:20
log_file       = %(OMD_ROOT)%/var/log/coshsh/prod_linux.log
log_level      = INFO
```

### Required-or-near-required keys

`datasources` — comma-separated list of `<name>`s referencing `[datasource_<name>]` sections. The order matters: each datasource's `read()` is called in this order and they share `recipe.objects`.

`classes_dir` — directories searched for `datasource_*.py`, `app_*.py`, `os_*.py`, `detail_*.py`, `datarecipient_*.py`. Comma-separated. Coshsh always also searches its built-in `recipes/default/classes`, so you don't need to list that.

`templates_dir` — directories searched for `*.tpl` files. Comma-separated. Built-in `recipes/default/templates` is always also searched.

`objects_dir` — base directory where the default datarecipient writes config files (under a `dynamic/` subdir). Required unless you exclusively use custom datarecipients with their own output destinations.

### Optional keys

`datarecipients` — comma-separated list of `[datarecipient_<name>]` sections to use for output. Use `>>>` to include the default file-writer in the list. If omitted, the default file-writer is used implicitly. Example: `datarecipients = >>>, prometheus_writer, audit_db`.

`filter` — a string passed to each datasource's `read(filter=...)`. The datasource decides how to interpret it. The convention (when datasources implement it) is `dsname(key=value, key=~regex), other_ds(...)` to scope filters to specific datasources.

`git_init` — `yes`/`no` (default `yes`). When true, the default datarecipient initializes the output's `dynamic/` directory as a git repo on first use. Lets you `git diff` between coshsh runs to see what changed.

`max_delta` — change protection. `H:S` where `H` is the percent host-count change and `S` is the percent application/service-count change that triggers `max_delta_action`. Positive numbers protect against shrinkage (e.g. 10:20 means: if hosts shrink by >10% OR services shrink by >20%, take action). Negative numbers protect against growth. Single number applies to both: `15`. The companion key `max_delta_action` specifies what to do (`abort`, `git_reset_hard_and_clean`, ...). A value coshsh cannot parse (`max_delta = abc`) refuses the whole run with exit code `2`, naming the recipe and the setting — a run-safety control whose value is uninterpretable stops the run rather than being guessed at.

`max_render_error_pct` — render-failure tolerance, as a percentage from `0` to `100`. When more than this share of a recipe's template renderings fail, the recipe publishes **nothing**: the previous run's output is left byte-for-byte intact and `coshsh-cook` exits `4`. Omitted (the default) means no abort — protection is opt-in per recipe, so a recipe that does not set it publishes whatever it managed to render, however much failed. `0` means abort on any failure at all, however many succeeded. `100` never aborts (the comparison is strict `>`). Unlike `max_delta` this is a single number, not an `H:S` pair. A percentage rather than a count so that the same value stays meaningful for a 50-object recipe and a 50,000-object one.

`tolerate_missing_templates` — `yes`/`no` (default `no`). A template rule pointing at a `.tpl` file that is not on `templates_path` counts as a render failure by default. Set this to `yes` when a partial template pack is deliberate: the absences are still counted and still logged at ERROR, but they leave the `max_render_error_pct` calculation entirely — both the failure count and the attempt count — so they can neither cause nor mask an abort.

All three run-safety settings — `max_delta`, `max_render_error_pct`, `tolerate_missing_templates` — are validated when the recipe is built. A value that cannot be interpreted (`abc`, empty, negative, above `100`, or anything other than `yes`/`no`) refuses the run with exit code `2` **before any recipe is processed**, naming the offending recipe and key. The alternative — skipping the one bad recipe — would produce a run that reports success while its output silently lacks every object that recipe owns.

`log_file` — recipe-specific log file path. Overrides defaults. Useful in OMD: `log_file = %(OMD_ROOT)%/var/log/coshsh/myrecipe.log`.

`log_level` — `DEBUG`, `INFO`, `WARNING`, `ERROR`. Default `INFO`. Set to `DEBUG` for verbose output (essential when troubleshooting).

`pid_dir` — directory for the recipe's PID lock file. Default is sensible in OMD; override only if you have file-system constraints.

`force` — `yes`/`no`. Recipe-level equivalent of `--force` on the command line. Forces datasource reads even when `DatasourceNotCurrent` would otherwise skip them.

`safe_output` — `yes`/`no`. Enables additional safety checks when writing output (e.g. atomic file swaps).

`ENV_<NAME>` — sets the environment variable `<NAME>` for the duration of this recipe's execution. Example: `ENV_HTTPS_PROXY = http://proxy.internal:3128`.

`my_jinja2_extensions` — comma-separated list of `module.function_name` entries for custom Jinja2 extensions. Modules must be importable from `classes_dir`. The naming convention determines registration: `filter_*`, `is_*`, `global_*`. See `templates.md` for details.

### Exit codes

| Code | Meaning |
|---|---|
| `0` | All recipes processed, none aborted |
| `2` | Bad or missing cookbook file, or an uninterpretable run-safety value (no recipe was processed) |
| `3` | Could not import the `coshsh` package |
| `4` | One or more recipes aborted on template errors; their previous output is untouched |

`4` is distinct from `2` so a scheduler can tell "templates broke, the previous config is still in place" from "coshsh could not start". A run that aborts one recipe still processes the others and still exits `4`.

For log-based monitoring, a clean recipe matches `recipe \S+ completed with 0 problems`; the full line also carries the attempt count and, when anything failed, a breakdown: `completed with 3 problems out of 4213 rendering attempts [1 missing, 2 faulty]`. An aborted recipe emits no completion line at all, only an `aborted:` line at ERROR.

## `[datasource_<name>]`

```ini
[datasource_cmdb]
type     = mycmdb
url      = https://cmdb.example.com/api
token    = %(CMDB_TOKEN)%
timeout  = 60
tls_verify = yes
```

`type` is the only required key (every other key depends on the datasource implementation). The `type` value is matched against `__ds_ident__` functions in `datasource_*.py` modules — whichever module's identifier returns a class wins. All other key/value pairs are passed as `**kwargs` to that class's `__init__`.

For the built-in CSV datasource (`type = csv`), the supported keys are documented in `datasource_csvfile.py`. The main ones:

```ini
[datasource_inv]
type = csv
dir  = /path/to/csv/files
csv_hosts_file = inventory_hosts.csv
csv_applications_file = inventory_apps.csv
csv_applicationdetails_file = inventory_details.csv
csv_delimiter = ,
name_for_files = inventory
```

The CSV datasource also auto-discovers files by prefix: if `dir = /data` and the section is `[datasource_inv]`, it looks for `inv_hosts.csv`, `inv_applications.csv`, etc. unless you override with explicit `csv_*_file` keys.

## `[datarecipient_<name>]`

```ini
[datarecipient_prometheus]
type        = snmp_exporter
output_path = %(OMD_ROOT)%/etc/prometheus/snmp_targets
```

`type` matches a `__dr_ident__` function in a `datarecipient_*.py`. Other keys are kwargs.

The reserved name `>>>` in a recipe's `datarecipients =` line refers to the default file-writing recipient — you usually don't define it as a section.

## `[defaults]`

```ini
[defaults]
recipes      = prod_linux, prod_windows, network_devices
classes_dir  = %(OMD_ROOT)%/local/etc/coshsh/common_classes
templates_dir = %(OMD_ROOT)%/local/etc/coshsh/common_templates
log_dir      = %(OMD_ROOT)%/var/log/coshsh
pid_dir      = %(OMD_ROOT)%/tmp/run/coshsh
log_level    = INFO
backup_count = 5
```

`recipes` lists the default set of recipes to run when `coshsh-cook` is invoked without `--recipe`. Useful for cron jobs that should run "all of them".

The path keys in `[defaults]` act as fallbacks. Per-recipe paths are *prepended* to defaults (recipe-specific entries are searched first).

## `[mapping_<name>]`

```ini
[mapping_environments]
prod = production
dev  = development
stg  = staging
```

Lookups via `@{MAPPING_ENVIRONMENTS[prod]}` resolve to `production` in any other section. Useful for short codes from your data that need expansion.

## Worked example: complete cookbook

```ini
[defaults]
recipes       = prod_servers, prod_network
log_dir       = %(OMD_ROOT)%/var/log/coshsh
pid_dir       = %(OMD_ROOT)%/tmp/run/coshsh
log_level     = INFO
classes_dir   = %(OMD_ROOT)%/local/etc/coshsh/common/classes
templates_dir = %(OMD_ROOT)%/local/etc/coshsh/common/templates

[mapping_team]
sysops  = sysops@example.com
netops  = netops@example.com
dbops   = dbops@example.com

[datasource_cmdb_api]
type       = mycmdb
url        = https://cmdb.example.com/api/v2
token      = %(CMDB_TOKEN)%
tls_verify = yes
timeout    = 120

[datasource_overrides]
type = csv
dir  = %(OMD_ROOT)%/local/etc/coshsh/data
csv_hosts_file = overrides_hosts.csv
csv_applicationdetails_file = overrides_details.csv

[datarecipient_prom]
type        = snmp_exporter
output_path = %(OMD_ROOT)%/etc/prometheus/snmp_targets

[recipe_prod_servers]
datasources    = cmdb_api, overrides
classes_dir    = %(OMD_ROOT)%/local/etc/coshsh/recipes/prod_servers/classes
templates_dir  = %(OMD_ROOT)%/local/etc/coshsh/recipes/prod_servers/templates
objects_dir    = %(OMD_ROOT)%/etc/naemon/conf.d/generated/prod_servers
filter         = cmdb_api(env=production, type=~server.*)
git_init       = yes
max_delta      = 10:20
log_file       = %(OMD_ROOT)%/var/log/coshsh/prod_servers.log

[recipe_prod_network]
datasources    = cmdb_api
classes_dir    = %(OMD_ROOT)%/local/etc/coshsh/recipes/prod_network/classes
templates_dir  = %(OMD_ROOT)%/local/etc/coshsh/recipes/prod_network/templates
objects_dir    = %(OMD_ROOT)%/etc/naemon/conf.d/generated/prod_network
datarecipients = >>>, prom
filter         = cmdb_api(env=production, type=~(switch|router|firewall))
git_init       = yes
log_file       = %(OMD_ROOT)%/var/log/coshsh/prod_network.log
```

Cron entry:

```cron
# every 10 minutes, regenerate prod configs
*/10 * * * * coshsh-cook --cookbook /omd/sites/prod/etc/coshsh/conf.d/main.cfg
```

## Running

```bash
# generate all recipes listed in [defaults].recipes
coshsh-cook --cookbook /etc/coshsh/conf.d/main.cfg

# only one recipe
coshsh-cook --cookbook /etc/coshsh/conf.d/main.cfg --recipe prod_servers

# verbose
coshsh-cook --cookbook /etc/coshsh/conf.d/main.cfg --recipe prod_servers --debug

# force regeneration even if DatasourceNotCurrent
coshsh-cook --cookbook /etc/coshsh/conf.d/main.cfg --recipe prod_servers --force
```

After a successful run, the new configuration is in `objects_dir/dynamic/`. Reload Naemon/Nagios/Icinga to pick it up (typically via OMD's `omd reload <site>` or `naemon -v` followed by a service restart).

## Multiple datasources: ordering matters

```ini
[recipe_x]
datasources = cmdb_api, csv_overrides, csv_extra_apps
```

Processing order:

1. `cmdb_api.read()` runs first, populating `recipe.objects` with hosts and applications from the API.
2. `csv_overrides.read()` runs next. It can:
   - Add new hosts/apps the API didn't have.
   - Look up existing hosts/apps via `self.get('hosts', 'web01')` and mutate them (override alias, add hostgroups, add details).
   - Add monitoring details to apps the API created.
3. `csv_extra_apps.read()` runs last. Same capabilities.

When two datasources add items with the same fingerprint, the later one wins — but it's an attribute-level merge: attributes set by the later datasource overwrite, others are preserved.

## Multiple datarecipients

```ini
[recipe_x]
datarecipients = >>>, prom, audit_db

[datarecipient_prom]
type = snmp_exporter
output_path = /etc/prometheus/snmp_targets

[datarecipient_audit_db]
type = audit_logger
dsn  = postgresql://...
```

All three run during the output phase, receiving the same fully-populated `recipe.objects`. Each one decides which items it cares about — typically by inspecting `item.config_files` keys, `item.template_rules[].for_tool`, or `item.__class__`.

## Pitfalls

1. **Forgetting the `_` in section names.** `[recipe prod]` is invalid; must be `[recipe_prod]`.
2. **Spaces around `=`.** Mostly fine but be consistent. Use `key = value` (spaces around `=`).
3. **Listing datasources in the wrong order.** When one datasource depends on another's data, the dependent must come later.
4. **Relative paths.** `classes_dir = ../classes` works but is fragile. Use absolute paths or `%(OMD_ROOT)%`-anchored paths.
5. **`%(NONEXISTENT_ENV)%`.** Behavior depends on coshsh version — may leave the placeholder literally or substitute empty. Always make sure the env var is set, or `export` it in your cron job.
6. **Filter syntax expectations.** Filters are entirely datasource-defined. There's no built-in filter parser; if a datasource doesn't implement `_parse_filter`, the filter string is ignored. Check the datasource's source code.
7. **`objects_dir` write permissions.** Coshsh writes as the user who runs `coshsh-cook`. In OMD, that's the site user. Make sure the path is writable.
8. **`git_init = yes` in a non-git environment.** Requires git to be installed. If you don't want git tracking, set `git_init = no`.
