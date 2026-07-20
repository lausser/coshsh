# Phase 1 Data Model: Template Rendering Error Handling

## Entity: `RenderTally`

New module `coshsh/rendertally.py`. One instance per `Recipe`, created in
`Recipe.__init__`, mutated in place during `Recipe.render()`, read by
`Generator.run()`.

Pure: no I/O, no logging, no Jinja2, no filesystem. This is deliberate — it makes
the precision requirement testable without constructing a recipe.

### Fields

| Field | Type | Meaning |
|---|---|---|
| `attempts` | `int` | Every template render attempt, success or failure, counted once per matched template rule per object |
| `missing` | `int` | Attempts that failed because the template file was not found |
| `errors` | `int` | Attempts that failed for any other reason: Jinja2 syntax error, Python error while loading, exception raised while rendering, or failure evaluating a template rule's conditions |
| `max_error_pct` | `float \| None` | Configured tolerance. `None` = never abort |
| `tolerate_missing` | `bool` | When true, missing templates leave the percentage calculation |

### Derived values

```text
tolerate_missing is False:
    template_errors      = missing + errors
    accountable_attempts = attempts

tolerate_missing is True:
    template_errors      = errors
    accountable_attempts = attempts - missing

error_pct = 100.0 * template_errors / accountable_attempts
            if accountable_attempts else 0.0

too_many_errors = max_error_pct is not None and error_pct > max_error_pct
```

### Invariants

1. **Never round before comparing.** `error_pct` is compared as a raw float.
   Rounding for display (`"%.4f%%"`) is fine; rounding before the comparison
   silently defeats `max_error_pct = 0`, because `round(0.0001, 2) > 0` is
   `False`. This must be commented at the comparison site.
2. **Zero accountable attempts never aborts** and never raises
   `ZeroDivisionError`. Covers both a recipe that collected nothing and a recipe
   where every attempt was a tolerated missing template.
3. **`missing` is always counted**, regardless of `tolerate_missing`. The flag
   governs the percentage only, never the counter or the log output.
4. **`attempts` is incremented exactly once per invocation** of
   `render_cfg_template()`, before any outcome is known.
5. **Strict greater-than.** `error_pct > max_error_pct`, so `max_error_pct = 0`
   aborts on any accountable failure while a clean run at exactly `0.0` does not.

### Relationship to `Recipe`

| Before | After |
|---|---|
| `self.render_errors = 0` (recipe.py:345) | `self.render_tally = RenderTally(...)` |
| `self.render_errors += x.render(...)` ×6 (recipe.py:545-564) | `x.render(...)` ×6 — accumulation removed |
| — | `render_errors` becomes a read-only property → `tally.template_errors` |

`render_errors` retained as a property so that `test_classes.py:100`,
`test_recipes.py:178`, the summary log line (`generator.py:213`) and the existing
Prometheus gauge keep working unchanged.

## Recording points

Where each counter is incremented. All sites are in `coshsh/item.py`.

**How the tally reaches each site.** `Item.render()` receives the recipe as a
declared parameter and reads `recipe.render_tally` directly. `render_cfg_template()`
does **not** — it sees the recipe only inside `**kwargs`, where `Item.render()`
packs it for the template namespace (item.py:283-287). It therefore gains an
explicit keyword parameter:

```python
def render_cfg_template(self, jinja2, template_cache, name, output_name,
                        suffix, for_tool, _skip_pythonize=False,
                        tally=None, **kwargs):
```

passed by name from all three call sites in `Item.render()`. Rationale in plan.md
Design Decision 1. `tally=None` means "do not count" and is the safe default for
any out-of-tree caller; it never raises.

| Site | Current behaviour | New |
|---|---|---|
| `render_cfg_template()` entry | — | `attempts += 1` |
| `except TemplateSyntaxError` (line ~222) | `render_errors += 1` | `errors += 1` |
| `except TemplateNotFound` (line ~225) | logs only, **counts nothing** | `missing += 1`; log line unchanged |
| `except Exception` on load (line ~227) | `render_errors += 1` | `errors += 1` |
| `except Exception` on render (line ~243) | `render_errors += 1` | `errors += 1` |
| `Item.render()` rule-match failure (line ~271) | `render_errors += 1` | `attempts += 1`, `errors += 1` |

The rule-match failure counts an attempt because a rule that should have produced
output did not — excluding it would flatter the denominator.

The `TemplateNotFound` log line stays at its current level and wording
(`logger.error("cannot find template " + name)`), per clarification.

## Entity: `RecipeInvalidConfig`

New exception in `coshsh/recipe.py`, beside the existing `RecipePidAlreadyRunning`
/ `RecipePidNotWritable` / `RecipePidGarbage`.

Raised by `Recipe.__init__` when a cookbook value cannot be interpreted. Must be
re-raised by `Generator.add_recipe()` rather than swallowed by its blanket
`except Exception` — see research.md Finding 4.

Carries the offending key, the raw value, and what was expected, so the message
can name the setting rather than surfacing a bare `invalid literal for int()`.

## The shared validation rule (FR-016b)

One module-level helper in `coshsh/recipe.py` — not a new module, and not a class.
Every run-safety setting is validated through it, so a setting added later
inherits refuse-the-run behaviour by declaring a converter instead of writing its
own error handling:

```python
def validated_setting(key, raw, convert, accept=None, expected=""):
    """Parse one run-safety cookbook value or raise RecipeInvalidConfig."""
    try:
        value = convert(raw)
    except (TypeError, ValueError):
        raise RecipeInvalidConfig(key, raw, expected)
    if accept is not None and not accept(value):
        raise RecipeInvalidConfig(key, raw, expected)
    return value
```

| Setting | `convert` | `accept` | `expected` |
|---|---|---|---|
| `max_render_error_pct` | `float` | `0.0 <= v <= 100.0` | a percentage from 0 to 100 |
| `tolerate_missing_templates` | `yes`/`no` → bool | — | `yes` or `no` |
| `max_delta` | the existing `H:S`-or-single parse | all parts are integers | one integer, or two separated by a colon |

Scope is deliberately the three run-safety settings. Routing every cookbook key
through it would be a speculative abstraction (constitution Principle V); these
three share the property that a bad value must stop the run rather than degrade
it.

### `max_delta` — correcting existing behaviour (FR-016a)

Today `max_delta` is parsed at recipe.py:191-195 with a bare
`tuple(map(int, ...))`. On a malformed value that raises `ValueError` inside
`Recipe.__init__`, which `Generator.add_recipe()` swallows (generator.py:96-97) —
so the recipe is dropped from `self.recipes` and the run proceeds without it,
silently omitting every object that recipe would have produced.

Two constraints on the fix:

1. **Only the `str` branch is validated.** `self.max_delta` is also passed around
   as an already-parsed tuple (recipe.py:314 hands it to
   `add_datarecipient`), so the `isinstance(self.max_delta, str)` guard stays
   exactly as it is. Validation applies where parsing applies.
2. **Structure only, not range.** Accept what parses as one or two integers;
   do **not** add a 0–100 bound. Every value accepted today keeps working — the
   change converts a crash-and-silently-drop into a named refusal, and nothing
   else. Tightening the range too would widen the blast radius beyond the
   silent-data-loss bug this is here to close.

Validation rules for `max_render_error_pct`:

| Input | Result |
|---|---|
| absent | `None` — never abort (current behaviour preserved) |
| `"0"`, `"0.0"` | `0.0` — abort on any accountable failure |
| `"5"`, `"12.5"`, `"100"` | the float. `100` never aborts: `error_pct` cannot exceed 100 and the comparison is strict `>` |
| `"abc"`, `""` | `RecipeInvalidConfig` |
| `"-5"` | `RecipeInvalidConfig` — a negative tolerance is meaningless |
| `"250"` | `RecipeInvalidConfig` — a percentage's domain is 0–100; above 100 is a typo, not a permissive policy (spec FR-004) |

The valid domain is therefore `0.0 <= value <= 100.0` inclusive. Note that `100`
and `250` behave identically at runtime (neither can ever abort); they are
distinguished deliberately, because accepting `250` would mean silently accepting
a value the author plainly did not mean.

`tolerate_missing_templates` follows the existing `git_init` idiom: `yes`/`no`,
default `no`. Any other value raises `RecipeInvalidConfig`.

## State transitions — run outcome

```text
collect() fails            → no render, no output, not completed
                             (render metrics may be stale; last_success does not advance)

render() → too_many_errors → ABORT: output() skipped, previous output preserved,
                             pid released, render metrics exported fresh,
                             last_success does NOT advance, exit code set

render() → within tolerance→ output() runs, completed, all metrics fresh,
                             last_success advances
```
