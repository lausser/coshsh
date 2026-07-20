> **Status: superseded design, retained analysis.** This is the document feature
> 007 started from, written before the spec existed. Its **design** is superseded
> by [plan.md](./plan.md) and [data-model.md](./data-model.md) — those were
> written after eight clarifications that this sketch predates, and they differ
> from it in substance: counters are threaded through a `RenderTally` owned by
> the recipe rather than returned up through widening tuples, missing templates
> are in scope with a `tolerate_missing_templates` opt-out, and there is an
> exit-code contract.
>
> Its **analysis of current behaviour remains valid and is not duplicated
> anywhere else** — in particular the section "Why `max_delta` doesn't solve
> this" (the `count_objects()` / `too_much_delta()` mechanics and the three
> reasons a disk-delta signal cannot serve as a render-error signal) and the
> float64 precision argument. Read it for the *why*, not for the *what*.

# Template render-error abort mechanism — implementation spec

## Problem

`coshsh-cook` currently never aborts a recipe because of a template rendering
failure, no matter how many templates fail. A render error is logged and
counted, but the recipe run proceeds to write output as if nothing happened.
The only thing that can currently stop a bad run is `max_delta`, which reacts
to *symptoms* of failure (fewer files on disk than before) — not to the
render errors themselves — and is tuned for gross data loss, not template
bugs.

Goal: add a `max_render_error_pct` recipe option that aborts the recipe
(skips writing output) when the percentage of failed template renders
exceeds a configurable threshold. Setting the threshold to `0` must abort on
a *single* failed template even if there are a million successful ones.

## Current behavior (verified against the code)

### Where a render error happens and what it does today

`coshsh/item.py`, method `Item.render_cfg_template()` (~line 187 onward):

- Loads/compiles the Jinja2 template. On `TemplateSyntaxError` or generic
  `Exception`, logs `critical` and increments a local `render_errors` int
  (lines ~222-229).
- On `TemplateNotFound`, logs `error` but does **not** increment
  `render_errors` — this is a pre-existing gap, out of scope here but worth
  knowing about.
- Renders: `self.config_files[for_tool][output_name + "." + suffix] =
  template_cache[name].render(kwargs)` (line ~239). If `.render(kwargs)`
  raises, the right-hand side never finishes evaluating, so **the dict key
  is never created**. This is why a failed render produces **no file at
  all** — not a zero-byte file. `except Exception` at line ~243 logs
  `critical` and increments `render_errors`.
- Returns `render_errors` (int) to the caller.

`Item.render()` (~line 254 onward): iterates `self.template_rules`, calls
`render_cfg_template()` once per matching rule, sums up `render_errors`
across all rule invocations for this item, returns the sum.

`coshsh/recipe.py`, method `Recipe.render()` (~lines 528-564): iterates
hosts, applications, contactgroups, contacts, hostgroups, and any custom
`Item` subtypes, calling `.render()` on each and accumulating into
`self.render_errors` (an int on the `Recipe` instance, initialized at
`recipe.py:345`). No return value; never raises; never checks the total
against anything.

`coshsh/generator.py`, the run loop (~lines 156-216): calls, in order,
`recipe.collect()` → `recipe.assemble()` → `recipe.render()` →
`recipe.output()`, all unconditionally back-to-back (~lines 165-168).
`recipe.render_errors` is read once, afterwards, only to push a Prometheus
gauge (`coshsh_recipe_render_errors`, ~line 184-187) and to log a summary
line (`recipe %s completed with %d problems`, ~line 213). **Nothing gates
`recipe.output()` on the error count.**

### Why `max_delta` doesn't solve this

`coshsh/datarecipient.py`:

- `count_objects()` (~lines 214-238) counts **on-disk state**: host
  directories under `dynamic_dir/hosts/`, and non-empty files inside them
  (excluding `host.cfg`). This is a deliberate design (see the WHY comment
  there) — it catches failures by inspecting what actually landed on disk.
- `count_before_objects()` / `count_after_objects()` snapshot this count
  before and after `Recipe.output()` runs (`recipe.py` output flow calls
  `cleanup_target_dir()` before writing, so old files are gone before new
  ones are written).
- `too_much_delta()` (~lines 276-334) computes `delta_hosts` /
  `delta_services` as **percentages of the old count**, with
  divide-by-zero guards (`old_objects[i] == 0` → delta treated as `0`,
  because a recipe growing from 0 objects shouldn't be flagged). Compares
  against `self.max_delta` (a `(host_pct, service_pct)` tuple parsed in
  `recipe.py:189-195` from the `max_delta` cookbook key, format `H:S`, see
  `.claude/skills/coshsh-classes/references/cookbook.md` line ~70).

This is unsuitable as a render-error signal because:

1. It's indirect — it infers failure from a missing file, not from the
   actual error count.
2. It's percentage-of-*previous-run-size*, not percentage-of-*this-run's-
   render-attempts*. A single failed template among a million successful
   ones is very unlikely to move `delta_services` past any sane threshold.
3. `max_delta`'s divide-by-zero guard exists because its denominator
   (`old_objects`) is a *baseline from a different run* and can legitimately
   be zero or drift. This does not apply to the new metric (see below),
   whose denominator comes from *this same render pass*.

## Design

### New metric: percentage of failed template renders, this run

Two counts, both from the *same* render pass, so no cross-run baseline
issues:

- **`render_attempts`** — total number of template-render attempts, success
  or failure. **Does not exist today and must be added.** Increment it once
  per call to `render_cfg_template()` (i.e. once per matched `TemplateRule`
  per item), unconditionally — right at the top of the method, or anywhere
  guaranteed to run exactly once per invocation regardless of outcome.
- **`render_errors`** — already exists, counts only failures.

Percentage:

```python
pct_failed = 100.0 * render_errors / render_attempts if render_attempts else 0.0
```

Threshold check, strict greater-than, against the raw (unrounded) float:

```python
if max_render_error_pct is not None and pct_failed > max_render_error_pct:
    # abort
```

### Why this correctly triggers on "1 failure in a million" when the threshold is 0

`pct_failed = 100 * 1 / 1_000_000 = 0.0001`. `0.0001 > 0` is `True` in
Python float arithmetic — no precision issue at any realistic scale (float64
has ~15-17 significant decimal digits; this only breaks down past ~10^15
attempts, not a real concern).

**Critical implementation rule: never round before comparing.** Rounding
before the comparison would silently defeat the strict-zero case, e.g.
`round(0.0001, 2) > 0` evaluates to `0.0 > 0` → `False`. Rounding is fine
for **log/display output only** (e.g. `"%.4f%%"`), never for the abort
decision itself.

Zero `render_attempts` (recipe with no templates matched at all — e.g. no
hosts/apps collected) must not raise `ZeroDivisionError` and must not
trigger an abort: treat as `pct_failed = 0.0`.

### Config option: `max_render_error_pct`

New optional key in `[recipe_<name>]` sections, parsed the same place
`max_delta` is parsed (`recipe.py:189-195`). Unlike `max_delta`, this is a
**single float**, not a colon-separated pair (there's only one metric here,
not a host/service split):

```ini
[recipe_prod_linux]
...
max_delta            = 10:20
max_render_error_pct = 0
```

- Absent / unset → current behavior preserved (never abort on render
  errors, same as `max_delta` being unset today).
- `0` (or `0.0`) → strictest policy: abort if *any* template render fails,
  regardless of how many succeeded.
- `5` → abort only if more than 5% of template-render attempts failed.

Parsing should accept both `int` and `float` string values (`"0"`, `"0.0"`,
`"5"`, `"12.5"`) and store as `float` internally. Follow the existing
pattern at `recipe.py:189-195` for reading from `kwargs`/cookbook and
coercing types — don't need the `:`-split logic `max_delta` uses since this
is a single number, not a pair.

Naming note: deliberately **not** reusing/extending `max_delta` or naming
this `max_render_errors` (a bare count) — we settled on a percentage after
discussion, because it stays meaningful across recipes of wildly different
sizes and reuses the mental model `max_delta` users already have, while the
"even one failure" case is fully expressible via `0`.

### Where to hook the abort check

In `coshsh/generator.py`, in the run loop, between the existing calls to
`recipe.render()` and `recipe.output()` (currently back-to-back at
~lines 167-168):

```python
if recipe.collect():
    recipe.assemble()
    recipe.render()
    if recipe.too_many_render_errors():
        logger.critical(
            "recipe %s aborted: %.4f%% of %d template renders failed "
            "(%d errors), exceeds max_render_error_pct=%s",
            recipe.name, recipe.render_error_pct, recipe.render_attempts,
            recipe.render_errors, recipe.max_render_error_pct)
    else:
        recipe.output()
        recipe_completed = True
        ... # existing prometheus gauge block, unchanged
```

Suggested new `Recipe` method (`recipe.py`, near `too_much_delta`-style
helpers or right after `render()`):

```python
def too_many_render_errors(self) -> bool:
    """True if the percentage of failed template renders exceeds
    max_render_error_pct. Mirrors too_much_delta()'s role but operates
    on this run's render_attempts/render_errors, not on disk-count deltas.
    """
    self.render_error_pct = (
        100.0 * self.render_errors / self.render_attempts
        if self.render_attempts else 0.0
    )
    if self.max_render_error_pct is None:
        return False
    return self.render_error_pct > self.max_render_error_pct
```

### What "abort" must mean

Skip `recipe.output()` entirely for this run. This is important: `output()`
is what calls `cleanup_target_dir()` (wipes old files) and then writes new
ones. Skipping it means **whatever was on disk from the previous successful
run stays untouched** — the safe failure mode. Do not partially write.

Other run-loop bookkeeping to preserve on abort:

- `recipe_completed` stays `False` (mirrors what happens today when
  `recipe.collect()` returns `False`) — this already suppresses the
  "completed with N problems" log line and the per-run Prometheus success
  gauges, which is correct: an aborted run is not a success.
- `recipe.pid_remove()` (~generator.py line 202) is called unconditionally
  after the `if recipe.collect(): ...` block, at the same indentation level
  as `if recipe.collect():` itself (i.e. inside `if recipe.pid_protect():`
  but outside the inner `if`). **Do not change this** — the pid lock must
  still be released on an aborted run, same as today.
- Consider whether the Prometheus `coshsh_recipe_render_errors` gauge push
  (~generator.py lines 184-187) should still fire on abort — probably yes,
  it's useful operational signal, and it's currently inside the
  `if recipe.collect():` block gated on nothing render-related. Keep that
  push regardless of abort so operators can alert on it externally too.

### Files to touch

1. `coshsh/item.py` — add `render_attempts` counting in
   `render_cfg_template()` (or wherever attempts are most naturally
   counted once per call) and thread it through `Item.render()`'s return
   value the same way `render_errors` is threaded today. `Item.render()`
   currently returns a single int (`render_errors`); decide whether to
   return a tuple `(render_errors, render_attempts)` or add a second
   accumulator attribute — check how the two existing call sites in
   `recipe.py:545-564` consume the return value before choosing, since
   both need to stay in sync (`self.render_errors +=` pattern repeated 6x).
2. `coshsh/recipe.py` — add `self.render_attempts = 0` next to
   `self.render_errors = 0` (`recipe.py:345`); accumulate it in `render()`
   alongside `render_errors` at all 6 call sites (~lines 545-564); parse
   `max_render_error_pct` from cookbook config near `max_delta` parsing
   (~lines 189-195); add `too_many_render_errors()` method and
   `render_error_pct` attribute as sketched above.
3. `coshsh/generator.py` — insert the abort check between `recipe.render()`
   and `recipe.output()` in the run loop (~lines 165-168), as sketched
   above.
4. `.claude/skills/coshsh-classes/references/cookbook.md` — document the
   new `max_render_error_pct` key next to the existing `max_delta`
   documentation (~line 70), following the same doc style.

### Test / acceptance criteria

- Unit test on `Recipe.too_many_render_errors()`: feed it
  `render_errors=1, render_attempts=1_000_000, max_render_error_pct=0` →
  must return `True`. Feed `render_errors=0` with any `render_attempts` →
  `False`. Feed `render_attempts=0` (nothing rendered) → `False`, no
  exception.
- Unit test confirming the comparison is not rounded: e.g.
  `render_errors=1, render_attempts=1_000_000_000, max_render_error_pct=0`
  still returns `True` (pct = 1e-7, well below any rounding threshold that
  might accidentally be introduced).
- Integration test: a recipe with one intentionally broken template (e.g.
  references an undefined Jinja2 variable that raises, or bad syntax) and
  `max_render_error_pct = 0` in the cookbook → after running the recipe,
  assert `recipe.output()` was never invoked / no files were
  written/changed in `objects_dir`, and the previous run's files (if any)
  are untouched.
- Integration test: same broken template but `max_render_error_pct` unset →
  current behavior preserved, output still gets written for everything that
  didn't fail (regression guard against breaking existing behavior).
- Confirm `pid_remove()` still runs and the pid lock is released after an
  aborted run (no stale lock blocking the next scheduled run).

### Explicitly out of scope for this change

- Per-host or per-application partial abort (skip only the broken item's
  output, keep everything else). Not requested; would require restructuring
  how `output()` writes per-item, since today it's all-or-nothing per
  datarecipient call.
- Fixing the `TemplateNotFound` branch in `item.py` (~line 225-226) not
  incrementing `render_errors`. Noted as a pre-existing gap, separate
  concern.
- `max_delta_action`-style multiple actions (`abort`,
  `git_reset_hard_and_clean`, ...) for the new option. MVP is abort-only;
  extending to other actions can be layered on later without changing the
  detection logic above.
