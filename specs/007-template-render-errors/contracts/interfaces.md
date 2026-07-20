# Phase 1 Contracts: Template Rendering Error Handling

coshsh is a CLI tool and library. Its externally-visible contracts are the
cookbook config keys, the exported metrics, the process exit codes, and the
Python attributes that user class files may read.

## 1. Cookbook configuration keys

Both keys are optional and belong in a `[recipe_<name>]` section, alongside the
existing `max_delta` / `max_delta_action`.

### `max_render_error_pct`

```ini
[recipe_prod_linux]
objects_dir          = /omd/sites/prod/var/coshsh/objects
max_delta            = 10:20
max_render_error_pct = 0
```

| Aspect | Contract |
|---|---|
| Type | Single float (**not** the `H:S` pair form used by `max_delta`) |
| Domain | `0` to `100` inclusive |
| Absent | No abort on template errors — current behaviour, unchanged |
| `0` | Abort if **any** accountable template error occurs, however many succeeded |
| `5` | Abort only if more than 5% of accountable attempts failed |
| `100` | Never aborts — 100% is the ceiling and the comparison is strict `>` |
| Comparison | Strict `>`, evaluated unrounded |
| Invalid | Non-numeric, empty, negative, or **above 100** — run refuses to start (see exit codes) |

Deliberately not named `max_render_errors` (a bare count): a percentage stays
meaningful across recipes of wildly different sizes, and the "even one failure"
policy is fully expressible as `0`.

### `tolerate_missing_templates`

```ini
[recipe_partial_templatepack]
max_render_error_pct      = 0
tolerate_missing_templates = yes
```

| Aspect | Contract |
|---|---|
| Type | `yes` / `no`, following the existing `git_init` idiom |
| Default | `no` — a missing template is a template error |
| `yes` | Missing templates are still counted and still logged, but leave the percentage calculation entirely (both numerator and denominator) |
| Invalid | Run refuses to start |

### `max_delta` — existing key, stricter validation

Not a new key and its accepted values are unchanged: `10`, `10:20`, or absent, as
today. What changes is the reaction to a value that is **not** accepted.

| Aspect | Before | After |
|---|---|---|
| `max_delta = abc` | `ValueError` inside recipe construction, swallowed by the generic handler — the recipe is dropped and the run continues without it, silently omitting all of its objects | Run refuses to start, naming the setting and the recipe |
| `max_delta = 10:20` | accepted | accepted, unchanged |
| `max_delta` absent | no delta check | no delta check, unchanged |

Validated for structure only (one integer, or two separated by a colon) — no range
bound is added, so every value that works today keeps working (FR-016a).

## 2. Exit codes (`coshsh-cook`)

| Code | Meaning | Status |
|---|---|---|
| `0` | All recipes processed; none aborted | existing |
| `2` | Bad or missing cookbook file | existing (`generator.py:259`) |
| `3` | Could not import the `coshsh` package | existing (`bin/coshsh-cook:41`) |
| `2` | Invalid recipe config value (`RecipeInvalidConfig`) | **new** — reuses the config-error code, since it is the same class of failure |
| `4` | One or more recipes aborted on template errors | **new** |

`4` is distinct so a scheduler can tell "templates broke, previous config
preserved" from "coshsh could not start". A run that aborts one recipe still
processes the others and still exits `4`.

## 3. Prometheus metrics

Pushed via `pushadd_to_gateway` with the existing grouping keys (`hostname`,
`username`, `cookbook`, `recipe`).

### Existing, unchanged names

| Metric | Change |
|---|---|
| `coshsh_recipe_last_generated` | none |
| `coshsh_recipe_number_of_objects{type}` | none |
| `coshsh_recipe_last_duration` | none |
| `coshsh_recipe_render_errors` | **value semantics change**: now includes missing templates by default (see Compatibility) |
| `coshsh_recipe_last_success` | **corrected**: advances only for runs that actually published output |

### New

| Metric | Type | Meaning |
|---|---|---|
| `coshsh_recipe_render_attempts` | Gauge | Template render attempts this run |
| `coshsh_recipe_missing_templates` | Gauge | Templates not found this run, counted whether or not tolerated |
| `coshsh_recipe_tolerate_missing_templates` | Gauge | `1` if this recipe declares missing templates tolerated, else `0` |
| `coshsh_recipe_render_error_pct` | Gauge | The percentage the abort decision was made on |
| `coshsh_recipe_aborted` | Gauge | `1` if this run aborted on template errors, else `0` |

`tolerate_missing_templates` is exported because FR-017c requires the *tolerated*
missing-template count to be a distinct signal. `coshsh_recipe_missing_templates`
alone cannot satisfy that: it carries the same value whether or not the flag is
set, so a consumer cannot tell a tolerated absence from a counted failure. With
the flag exported alongside it, both readings are available —
`missing_templates and tolerate_missing_templates` is the tolerated count, and
`missing_templates unless tolerate_missing_templates` is the part folded into
`render_errors`. Exporting the flag rather than a second pre-computed count keeps
the metric set additive and avoids a gauge whose meaning changes with config.

`render_error_pct` is exported rather than left to be derived, because with
`tolerate_missing_templates = yes` the denominator is *accountable* attempts —
deriving it externally would mean reimplementing the policy in PromQL.

### Freshness contract

- Aborted runs **do** export the render metrics (they are the runs whose numbers
  matter most) and `coshsh_recipe_aborted = 1`.
- Runs that fail before rendering **may** leave the render metrics stale. This is
  acceptable only because `coshsh_recipe_last_success` now ages correctly and is
  the authoritative liveness alarm: `(now - last_success) > threshold`.

## 4. Python attributes visible to class files

| Attribute | Contract |
|---|---|
| `recipe.render_errors` | **Preserved** as a read-only int property. Value now includes missing templates by default |
| `recipe.render_tally` | New. `RenderTally` instance; `attempts`, `missing`, `errors`, `template_errors`, `error_pct`, `too_many_errors` |
| `Item.render(template_cache, jinja2, recipe)` | **Signature unchanged.** Return value retained but no longer used for accumulation |
| `Item.render_cfg_template(...)` | Gains a keyword argument for the tally; existing positional parameters unchanged |

Assigning to `recipe.render_errors` now raises `AttributeError` (it became a
property). No code in the repository does so after this change; the six former
`+=` sites are removed.

## Compatibility notes for CHANGELOG

1. **`coshsh_recipe_render_errors` may rise** at sites that have missing
   templates, because those now count. This is the intended fix — the number was
   previously under-reporting. Set `tolerate_missing_templates = yes` to keep the
   old value.
2. **`coshsh_recipe_last_success` may start aging.** It previously advanced on
   every run that acquired the pid lock, so age-based alerts could never fire.
   After this change they can — a previously-silent alert becoming active will
   look like a new alarm, but it is an old one finally working.
3. **New exit code `4`.** Wrappers treating any non-zero exit as fatal will now
   see aborts. That is correct: an aborted run needs attention.
4. **A malformed `max_delta` now stops the run** (exit `2`) instead of silently
   dropping that one recipe. This is the loudest compatibility change in the
   feature: a site whose cookbook carries such a typo is losing that recipe's
   entire output on every run today with no signal, and will now get a hard
   startup failure naming the setting. Accepted values are unchanged — only the
   reaction to an unacceptable one. Fix the value to restore the run; there is no
   opt-out, by design (FR-016a).
