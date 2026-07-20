# Phase 0 Research: Template Rendering Error Handling

All findings below were verified against the working tree (coverage runs, log
inspection, docstring inspection), not inferred. Line numbers are from the state
of the code at planning time.

## Finding 1 — Nothing from the earlier design sketch is implemented

**Decision**: Treat `TEMPLATE-ERRORS.md` (repo root) as an idea collection, not as
partially-landed work.

**Verification**: Repo-wide search for every identifier it proposes —
`render_attempts`, `max_render_error_pct`, `too_many_render_errors`,
`render_error_pct` — returns hits only inside `specs/`. `recipe.py:189-195`
parses `max_delta`/`max_delta_action` and nothing else; `generator.py:165-168`
runs `collect() → assemble() → render() → output()` back to back with no gate.

**Its description of *current* behaviour is accurate** and was reused. Its
*design* predates this feature's clarifications (single knob, no tolerate flag,
no exit-code contract, missing templates declared out of scope) and is superseded.

## Finding 2 — The missing-template branch is reached today, silently

**Decision**: Counting missing templates is a live behaviour change, not a
theoretical one. This is why the tolerate flag exists.

**Verification**: Coverage run over the full suite with per-test dynamic contexts
shows `item.py:225-226` (`except TemplateNotFound`) **executed**, attributed to
`tests.test_dest.DatarecipientTest.test_create_recipe_fallback_datarecipient_write`.

Root cause traced: `[recipe_TEST9a]` (`tests/etc/coshsh.cfg:142`) declares no
`templates_dir`, so its templates path is only the repo-root
`recipes/default/templates`. `tests/recipes/test9/classes/os_windows.py:14-16`
declares two **unconditional** rules (`needsattr=None`): `os_windows_default`
(present in the defaults) and `os_windows_kaas` (absent). The fixture's own
`tests/recipes/test9/templates/os_windows_kaas.tpl` exists but is never on the
path.

**Consequence for implementation**: this test's `render_errors` goes from 0 to 1.
Verified by instrumenting `jinja2.Environment.get_template` during the test: 4
template loads, exactly one `TemplateNotFound` (`os_windows_kaas.tpl`) — one
Windows application × one unconditional rule. The test asserts on `new_objects`,
and `TEST9a` sets no tolerance (`max_error_pct is None` → never abort), so it
still passes.

**This test is also the proof that publishing with errors is normal, not
exceptional.** It reaches `output()` with a template error and writes its objects,
which is what every recipe without a configured tolerance will keep doing. See
Finding 8.

**Alternative considered**: fixing the fixture by adding `templates_dir` to
`TEST9a`. Rejected as the primary approach — it would hide the very behaviour
change under test. The fixture is left as-is precisely because it is now a
regression witness for the missing-template path.

## Finding 3 — The render-raise path has zero test coverage

**Decision**: A new fixture is required; this is the only one of the three failure
paths with no existing exemplar.

**Verification**: Coverage annotation of `item.py` marks lines 243-248 (the
`except Exception` around `template.render(kwargs)`) as never executed across all
215 tests. Lines 227-229 (generic exception on template *load*) are likewise never
executed.

The two counted paths that *are* covered are both `TemplateSyntaxError`:

| Test | Assertion | Cause |
|---|---|---|
| `test_classes.py:100` | `render_errors == 1` | `os_windows_kaas.tpl:24` — `No filter named 'neighbor_applications_as_tuple'` |
| `test_recipes.py:178` | `render_errors == 3` | `templates_err/app_db_mysql_default.tpl:4` — deliberate `{% if {#` syntax error, hit once per each of 3 mysql apps |

**Consequence**: both existing assertions are `faulty`-kind errors, which are
counted today and stay counted. Neither number changes. This was the main
compatibility risk and it is cleared.

## Finding 4 — `add_recipe` silently swallows every construction error

**Decision**: A malformed tolerance value must raise a **dedicated** exception
type, which `add_recipe` re-raises instead of catching.

**Verification**: `generator.py:94-98`:

```python
try:
    recipe = coshsh.recipe.Recipe(**kwargs)
    self.recipes[kwargs["name"]] = recipe
except Exception as e:
    logger.error("exception creating a recipe: %s" % e)
```

A blanket `except Exception` that logs and continues. The caller
(`generator.py:322-325`) then does `if recipe not in self.recipes: continue`.
So any exception raised in `Recipe.__init__` results in the recipe being
**silently skipped** — the exact outcome FR-016 forbids, and the outcome the
operator explicitly ruled out ("we never can skip a recipe because all the
objects it processes would be missing in the final output").

**Approach**: add `RecipeInvalidConfig` alongside the existing
`RecipePidAlreadyRunning` / `RecipePidNotWritable` / `RecipePidGarbage` classes
(`recipe.py:68-84`), and in `add_recipe` catch-and-re-raise it ahead of the
generic handler. `bin/coshsh-cook` converts it to a process exit, matching the
existing bad-cookbook exit at `generator.py:259`.

**Alternative considered**: validating the new keys in `read_cookbook` before
`add_recipe` is called. Rejected — it splits parsing of one recipe's config
across two places, and `Recipe.__init__` is where every other key is parsed.

## Finding 5 — Prometheus export semantics and the two defects

**Decision**: Accept metric staleness for runs that never rendered; fix the
success timestamp; export the render metrics on aborted runs.

**Verification**:

- `pushadd_to_gateway` docstring: *"This replaces metrics with the same name, job
  and grouping_key. This uses the POST HTTP method."* Metrics **absent** from a
  push therefore retain their previous value in the pushgateway indefinitely.
  (`push_to_gateway`, by contrast, is PUT and "overwrites all metrics" — not used
  here.)
- `generator.py:184-187` sets `coshsh_recipe_render_errors` **inside**
  `if recipe.collect():`, so a collect failure omits it and the previous value
  persists.
- `generator.py:188-192` sets `coshsh_recipe_last_success` **outside** that block
  — it advances on every run that acquires the pid lock, including runs that
  generated nothing. Its help text ("The timestamp when the recipe successfully
  ran last time") is therefore false, and any `time() - last_success > threshold`
  alert is unable to fire.

**Resolution** (per clarifications): staleness of the render metrics is tolerable
*because* the operator's alarm is `(now - last_success) > threshold` — but that is
only true once `last_success` is corrected. The two changes are coupled and must
ship together; the spec records this dependency in Assumptions.

**Alternative considered**: exporting explicit zeros for every metric on every
run to defeat staleness. Rejected by the operator — unnecessary once the liveness
alarm works, and it would report a misleading "0 errors" for runs that never
rendered.

## Finding 6 — `Item.render()` overrides do not accumulate

**Decision**: Moving from return-value accumulation to in-place tally mutation is
safe.

**Verification**: The only two overrides are
`GenericApplication.render()` (`application.py:153`) and
`GenericContact.render()` (`contact.py:168`). Both delegate to `super()` and
return its value unchanged; `GenericApplication` additionally returns `0` early
when the application has no actionable details — correctly recording no attempts.
Neither performs its own counting, so neither needs modification.

`Item.render()`'s signature stays `(self, template_cache, jinja2, recipe)`, so
user-supplied `Item` subclasses in class files are unaffected (constitution
Principle II).

## Finding 7 — `Generator.run()` return value is unused

**Decision**: `run()` may return an abort count without breaking any caller.

**Verification**: `run()` is declared `-> None`. Its callers are
`bin/coshsh-cook:82` and eight test call sites (`test_git.py:42`,
`test_order.py:30`, `test_recipes.py:74`, `test_datainterface.py:11`,
`test_suffix.py:13`, `test_pid.py:21,76,90,94`), all of which discard the return
value. Returning an `int` is therefore backward compatible.

## Finding 8 — Reaching `output()` with errors is the normal case, not an edge case

**Decision**: The abort is strictly opt-in. No safety floor is introduced.

**Verification**: `generator.py:165-168` calls
`collect() → assemble() → render() → output()` back to back with nothing gating
the write on `render_errors`. Today, therefore, **every** recipe with a broken or
missing template publishes partial output. That is the defect being fixed.

After this change, whether `output()` is reached with errors is purely a matter of
configuration:

| `max_render_error_pct` | `output()` reached with template errors? |
|---|---|
| absent (**default**) | Yes — FR-007 preserves today's behaviour exactly |
| `5`, with 2% failed | Yes — deliberately within tolerance |
| `0` | No |

**Implication worth stating plainly**: a site that never sets
`max_render_error_pct` gains no abort protection from this feature — only better
counters and metrics. Protection is opt-in per recipe. This follows directly from
FR-007 and the backward-compatibility assumption; it is recorded here because it
is easy to misread the feature as protecting every recipe by default.

**Alternative considered**: defaulting to `0`, or introducing a safety floor that
aborts when *all* renderings fail regardless of configuration. Rejected —
silently converting previously-succeeding unattended runs into aborts is exactly
the breaking change the backward-compatibility assumption forbids, and a floor is
speculative (Principle V) with no demonstrated demand.

## Summary of decisions

| Question | Decision |
|---|---|
| Reuse the earlier sketch's design? | No — current-behaviour analysis only; design superseded |
| How to thread counters? | In place via the already-passed `recipe`; no signature changes |
| How many counted kinds? | Two: `missing` and `errors` |
| Malformed tolerance value? | Dedicated exception, re-raised past `add_recipe`, process exits |
| Metric staleness? | Tolerated, contingent on the `last_success` correction shipping with it |
| Existing `render_errors` assertions? | Unchanged (both are `faulty`-kind); re-run to confirm |
| Abort by default? | No — opt-in per recipe; unconfigured recipes keep publishing with errors |
