# Troubleshooting coshsh

When something goes wrong, the failure usually falls into one of seven categories. Match the symptom, follow the cause, apply the fix.

## Symptom-to-cause table (cheat sheet)

| Symptom                                                                      | Likely cause                                                                                                                                                                                                  | First thing to check                                                                                  |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| "datasource X is unknown"                                                    | `type =` in cookbook doesn't match any `__ds_ident__`, OR the `datasource_*.py` file isn't in `classes_dir`, OR it has a syntax error preventing import                                                       | Search for the `type` string across all `datasource_*.py`; try `python -c "import datasource_x"`      |
| Recipe runs to completion but `objects_dir/dynamic/` is empty                | Datasource's `read()` didn't actually populate `recipe.objects` — `self.objects = objects` line is missing, or `self.add(...)` was never called                                                              | Log immediately after each `self.add()`; verify `len(recipe.objects['hosts'])` at end of `read()`     |
| Hosts appear but no services for some/all applications                       | No `app_*.py` / `os_*.py` matched the application's `type` (falls back to `GenericApplication` with empty `template_rules`), so no `.tpl` is rendered                                                          | grep the log for the actual `type` values being processed; ensure `__mi_ident__` matches them lowercased |
| Services exist but a specific `.cfg` file is missing                         | Either the template wasn't found (`cannot find template` in log), or the `TemplateRule` condition (`needsattr`, `valueofattr`) didn't match                                                                       | Confirm `.tpl` file is in `templates_dir`; print the item's relevant attributes                       |
| `jinja2.exceptions.UndefinedError: 'foo' is undefined`                       | Template references an attribute that doesn't exist on the item. Datasource didn't set it, monitoring detail didn't resolve, or `__init__` didn't compute it                                                  | Add `{{ application | pprint }}` to the template top to dump all attributes                           |
| Monitoring detail rows are read but produce no effect (no `application.X`)   | `host_name + name + type` triple on the detail doesn't match any application's fingerprint, OR there's no `detail_*.py` for the `monitoring_type`                                                              | Log the application's triple and the detail's triple side-by-side; check `recipes/default/classes/detail_*` for the type |
| "Recipe already running" / cannot acquire PID lock                           | Previous run crashed leaving a stale PID file                                                                                                                                                                  | Check `pid_dir` for `<recipe>.pid`, verify no process is alive, remove the file                       |
| `Too many open files`                                                        | OS file descriptor limit exhausted, typically when generating tens of thousands of items                                                                                                                       | `ulimit -n 65536` before running, or fix the limit in the systemd unit / OMD config                   |
| Datasource raised a plain `Exception` — ugly stack trace, recipe aborted     | Datasource didn't translate its lower-level error to `DatasourceNotAvailable`/`DatasourceCorrupt`                                                                                                              | Wrap the failing op in try/except and raise the right coshsh exception                                |
| Output files have literal "None" in them                                     | Datasource passed `None` values into item constructor                                                                                                                                                          | Strip None from params dicts; or use `| default(...)` in templates                                    |
| Generated configs change between runs even though source data didn't         | Some attribute is non-deterministic (e.g. dict ordering, set iteration, timestamp)                                                                                                                              | Use sorted iteration; avoid datetime.now() in templates                                                |
| `max_delta` keeps tripping                                                   | Threshold too tight, or genuine large change in inventory                                                                                                                                                      | Review and either widen the threshold (`max_delta = 30:50`) or accept the change with `--force` once |
| `coshsh-cook` exits `4`, nothing was written, previous output still in place | The recipe exceeded `max_render_error_pct`, so it published nothing on purpose. This is the safety mechanism working, not a crash                                                                              | Read the `aborted:` line — it names the failure count, the attempts, the percentage and the configured maximum; fix the templates it lists above that line |
| `coshsh-cook` exits `2` and no recipe ran at all                            | A run-safety value cannot be interpreted (`max_delta`, `max_render_error_pct` or `tolerate_missing_templates`). The run refuses to start rather than silently dropping the offending recipe                    | The message names the recipe and the key; fix the value in the cookbook |
| Render error count jumped after an upgrade, templates unchanged             | Templates that cannot be found now count as render errors; they were previously logged but counted nowhere                                                                                                     | Check `coshsh_recipe_missing_templates` or the `[N missing, M faulty]` breakdown in the summary line; if the absences are deliberate set `tolerate_missing_templates = yes` |

## Step 1: enable debug logging

Always do this first.

```bash
coshsh-cook --cookbook X.cfg --recipe Y --debug
```

Or in the cookbook for persistence:

```ini
[recipe_Y]
log_level = DEBUG
log_file  = %(OMD_ROOT)%/var/log/coshsh/Y_debug.log
```

DEBUG output shows every class match decision, every template selection, every detail resolution. It's verbose — pipe to `less` or grep for specific item names.

## Step 2: isolate

Cut the surface area until the problem is reproducible in a small setup.

- **One recipe only**: `--recipe Y` (don't run the whole `recipes =` list from `[defaults]`).
- **Simplify datasources**: swap your custom datasource for `type = simplesample` or a tiny CSV (10 hosts) to test downstream logic.
- **Simplify templates**: replace the suspected template with a one-liner that just outputs `{{ application.host_name }}` to confirm the item reaches render.
- **Reduce data**: when debugging a CSV datasource, point it at a 3-row file.

## Step 3: validate

When the problem is suspected upstream:

- **Cookbook**: try a known-good minimal cookbook in a separate `--cookbook` invocation to rule out parse errors.
- **CSV**: `head -3` and `wc -l`; check the header row; verify the delimiter matches `csv_delimiter`.
- **API**: hit the endpoint with `curl` using the same credentials/headers; verify a sample response payload.
- **DB**: connect with `psql`/`mysql` and run the exact query.
- **Filesystem permissions**: `coshsh-cook` runs as the OMD site user (typically) — make sure `objects_dir` is writable by that user.

## The classic failures, in detail

### "datasource X is unknown"

The cookbook says `type = mycmdb`, coshsh walked every `datasource_*.py` in every `classes_dir`, no `__ds_ident__` returned a class for `params = {'type': 'mycmdb', ...}`.

Causes, in order of likelihood:

1. `__ds_ident__` matches the wrong string (typo, case mismatch). `compare_attr("type", params, "MyCmdb")` is case-sensitive by default — pass `ignorecase=True` or normalize.
2. The Python file fails to import (missing dependency, syntax error). Coshsh logs the import error but it's easy to miss. Try `python -c "import sys; sys.path.insert(0, '<classes_dir>'); import datasource_mycmdb"`.
3. The file is misnamed — must start with `datasource_`. Files named `mycmdb_datasource.py` are not loaded.
4. The file isn't in any `classes_dir`. Re-check the recipe's `classes_dir =`.
5. `__ds_ident__` returned `MyClass()` (an instance) instead of `MyClass`. The framework expects the class.

### Applications fall back to `GenericApplication`

Log line: `item ... uses GenericApplication`. The `type` on the application didn't match any `__mi_ident__`.

Causes:

1. **Case sensitivity**. The framework lowercases application `type` before calling identifiers. Your `__mi_ident__` does `params["type"] == "Linux"` — never matches because the value has been lowercased to `linux`.
2. **Typo in `type`**. Datasource emits `type = "windowws"` (typo). Add a `logger.debug(f"adding app type={row['type']}")` to see.
3. **Wrong file prefix**. Class is in `mywindows.py`, not `os_mywindows.py` or `app_mywindows.py`. Not loaded.
4. **Module import failure**. Same as datasource case — `python -c "import os_mywindows"` to surface the error.

### `UndefinedError: 'foo' is undefined`

Jinja2 hit `{{ application.foo }}` and `foo` doesn't exist on the application.

Causes:

1. The datasource never set it. Add `logger.debug` after construction to confirm.
2. A monitoring detail was supposed to populate it (`application.filesystems` from `FILESYSTEM` details) but no details were created or the triple didn't match.
3. Typo in the template — `applicaiton.foo`, `application.fooo`.
4. Spelling drift between Python and templates — `application.is_clustered` in Python but `{{ application.isClustered }}` in template.

Debug technique: at the top of the template, add `{{ application | pprint }}` (with the `pprint` filter — needs to be a custom global, or use `{{ application.__dict__ | tojson }}`) to dump the full state of the item the template is rendering against.

Or guard with `| default()`:

```jinja
{{ application.foo | default("") }}
{{ application.bar | default(0) }}
```

This silences `UndefinedError` but should be a deliberate choice — sometimes the right fix is to set the attribute in `__init__`.

### Monitoring details silently do nothing

Details are added (`self.add('details', md)` runs without error), but `application.filesystems` is empty in templates.

Causes:

1. **Triple mismatch.** The detail's `host_name + name + type` doesn't equal any application's. Most common when:
   - The application's `name='os'` but the detail has `name=''` or no `name`.
   - The application's `type='linux'` but the detail has `type='Linux'` (case).
   - The detail uses `host` instead of `host_name`.
   - The application's `type` is one thing in the data but is rewritten in `__init__` (e.g. lowercased) — the detail still has the original.

   Diagnosis: after `read()`, log every application's fingerprint and every detail's intended-parent triple. They must match exactly.

2. **No `detail_*.py` for the `monitoring_type`.** You wrote `monitoring_type = "MY_CUSTOM"` but didn't create `detail_my_custom.py`. The framework stores the detail but has no logic to extract it into a structured attribute.

3. **The application class doesn't have a `template_rules` entry that uses the resolved attribute.** Details might be properly attached as `application.filesystems`, but if no `TemplateRule(needsattr="filesystems", ...)` exists, no per-filesystem template renders.

### Template not found

Log line: `ERROR - cannot find template foo`.

The `TemplateRule(template="foo")` references `foo.tpl`, which isn't in any `templates_dir` (recipe-specific or default).

Causes:

1. File misspelled, wrong extension (`foo.tpl.txt` doesn't load).
2. File is in a sibling directory the recipe doesn't list.
3. File exists but is unreadable by the current user.

`find . -name 'foo.tpl'` from anywhere in the project usually finds it.

This **counts as a render error**, once per object that referenced the template, so it shows up in `recipe.render_errors`, in `coshsh_recipe_missing_templates`, and in the `max_render_error_pct` abort decision. If a recipe deliberately references templates it does not ship, set `tolerate_missing_templates = yes` rather than letting it consume the recipe's failure budget.

The line appears **once per run**, not once per affected object — the failure is remembered for the rest of the render pass. Use the end-of-run summary for the totals: `completed with 3 problems out of 4213 rendering attempts [1 missing, 2 faulty]`.

### Recipe aborted on template errors

Log line: `ERROR - recipe X aborted: 3 of 4 renderings failed [1 missing, 2 faulty] (75.0000%, maximum is 0.0%). nothing was written, the previous output is unchanged`.

Not a crash — the recipe exceeded its `max_render_error_pct` and deliberately published nothing, so whatever the last good run produced is still in place, byte for byte. `coshsh-cook` exits `4`.

What to do:

1. The failures themselves are logged above the abort line, one per distinct broken template plus one per object for render-time errors. Fix those.
2. If the percentage looks wrong, check `tolerate_missing_templates`: when it is `yes`, absent templates leave *both* sides of the fraction, so 9 tolerated absences and 1 real failure reads as 100%, not 10%.
3. If the recipe legitimately runs with a partial template pack, `tolerate_missing_templates = yes` is the fix, not raising the tolerance — raising it also hides genuinely broken templates.

The lock is released on the abort path, so the next scheduled run starts normally once the templates are fixed. No manual cleanup is needed.

### `TemplateSyntaxError`

Jinja2 syntax error in a `.tpl`. The error message gives line and column.

Common causes:

1. Mismatched `{% %}` and `{{ }}`.
2. Missing `{% endfor %}` or `{% endif %}`.
3. Reserved-word collision: `{% set type = ... %}` may conflict — `type` is a Python builtin and Jinja2 treats it carefully.
4. Old `{% %}` syntax in places that need `{{ }}` or vice versa.

### PID file issues

Coshsh creates `<pid_dir>/<recipe>.pid` containing the PID of the running coshsh process. If a previous run crashed (kill -9, system reboot), the file persists. On the next run, coshsh sees the file and refuses to start.

Fix:

```bash
ps -p $(cat /omd/sites/prod/tmp/run/coshsh/prod_linux.pid) 2>/dev/null \
  || rm /omd/sites/prod/tmp/run/coshsh/prod_linux.pid
```

(Only remove if the PID is genuinely dead.)

### Generated configs differ between runs

If `git diff` in `<objects_dir>/dynamic/` shows changes between runs of unchanged input data, something's non-deterministic. Common culprits:

1. **Dict iteration order** — fixed since Python 3.7 but watch out for sets or older code.
2. **`hostgroups` order** — when built incrementally from multiple sources, the order may differ. Sort before assigning.
3. **Timestamps in templates** — `{{ now() }}` or `{{ datetime.now() }}` changes every run. Remove or stabilize.
4. **Filtering randomness** — `random.sample()`, `random.shuffle()` somewhere in the datasource.

Use `git diff` to identify what changed; usually the diff itself reveals which attribute is non-deterministic.

### Performance

If a recipe takes minutes instead of seconds for a moderate inventory:

- **Datasource is slow.** Time each phase in the log: `read` start to end, `assemble` start to end, `render` start to end, `output` start to end. Almost always `read` dominates if anything's slow.
- **Per-record API calls.** Replace with bulk fetches.
- **N+1 database queries.** Pre-fetch related rows in batches.
- **Synchronous SNMP/HTTP probes inside `read()`.** Move out — your datasource is supposed to read inventory, not perform live checks.

Coshsh itself processes 60000 services in roughly 10 seconds, so the framework is rarely the bottleneck.

## When asking for help

A useful bug report includes:

- The coshsh version (`coshsh-cook --version`).
- The full `--debug` output from a single failing run.
- The exact section of the cookbook involved.
- A minimal sample of input data that reproduces the issue.
- What you expected vs what you got.

The maintainer's response will be much faster if you've already isolated to the smallest failing case.
