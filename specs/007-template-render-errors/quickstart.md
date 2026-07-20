# Quickstart: Validating Template Rendering Error Handling

How to prove the feature works end to end. Run everything from `tests/`.

## Prerequisites

```bash
cd /home/lausser/git/coshsh/tests
python -m pytest -q          # baseline: expect 215 passed, 6 skipped
```

Record that baseline before changing anything — several checks below are
"unchanged from baseline" assertions.

## Scenario 1 — The arithmetic (fastest signal, no I/O)

```bash
python -m pytest test_rendertally.py -q
```

Proves, with no recipe and no filesystem:

| Case | Expectation |
|---|---|
| `attempts=1_000_000, errors=1, max_pct=0` | aborts — `1e-4 > 0` |
| `attempts=1_000_000_000, errors=1, max_pct=0` | aborts — `1e-7 > 0`, guards against a rounding regression |
| `attempts=0` | no abort, no `ZeroDivisionError` |
| `errors=0, max_pct=0` | no abort — strict `>`, a clean run at exactly 0.0 passes |
| `max_pct=None` with any errors | no abort |
| `tolerate_missing=True, attempts=10, missing=9, errors=1` | pct is 100.0 (1 of 1 accountable), **not** 10.0 |
| `tolerate_missing=True, attempts=10, missing=10` | no abort, no `ZeroDivisionError` |

The last two are the ones worth reading closely: they encode that a tolerated
missing template leaves *both* numerator and denominator.

## Scenario 2 — Abort preserves the previous output

```bash
python -m pytest test_render_errors.py -q
```

The decisive check. A recipe with a deliberately broken template and
`max_render_error_pct = 0`:

1. Run once with good templates → output written, note a checksum of `objects_dir`.
2. Swap in the broken template, run again → run aborts.
3. Assert the checksum is **identical** — no file added, changed, or deleted.

This is the requirement the whole feature exists for. If only one test survives,
it should be this one.

Also covered here: pid lock released after abort (next run starts clean), other
recipes in the cookbook still processed, `tolerate_missing_templates = yes`
suppressing an abort that would otherwise happen.

## Scenario 3 — Existing behaviour is unchanged

```bash
python -m pytest test_classes.py test_recipes.py test_dest.py -q
```

| Assertion | Expected | Why it matters |
|---|---|---|
| `test_classes.py:100` — `render_errors == 1` | still `1` | Syntax-error path, was counted before, still is |
| `test_recipes.py:178` — `render_errors == 3` | still `3` | Same, ×3 mysql apps |
| `test_dest.py` fallback datarecipient test | still passes | Its `render_errors` goes 0 → 1 — verified: exactly one `TemplateNotFound` (`os_windows_kaas.tpl`). It asserts on `new_objects` and sets no tolerance, so it still writes its objects and passes. It doubles as the regression witness that publishing-with-errors remains the default (research.md Findings 2 and 8) |

## Scenario 4 — Full suite and performance

```bash
python -m pytest -q -m "not benchmark"   # must match the baseline count
python -m pytest test_performance.py -m benchmark -q -s   # the constitutional gate
```

The benchmark asserts ≥ 60,000 services in ≤ 10 seconds (constitution Principle
IV). It is excluded from the normal suite by the `benchmark` marker because it is
a gate, not a per-run test. The added work is integer increments per render
attempt, so no measurable change is expected — compare against the baseline
recorded in `tasks/todo.md` before any source file was touched, on the same
machine, and take the median of three runs. A single wall-clock sample on a
shared machine is not evidence.

Note that no benchmark existed before this feature: spec 005 optimized the
pipeline on complexity analysis alone. `tests/test_performance.py` is new here.

## Scenario 5 — Manual CLI check (exit codes)

```bash
cd /home/lausser/git/coshsh
bin/coshsh-cook --cookbook <cookbook-with-broken-template> --recipe <name>
echo "exit=$?"        # expect 4 on abort
```

```bash
# malformed tolerance value in the cookbook
bin/coshsh-cook --cookbook <cookbook-with-max_render_error_pct=abc>
echo "exit=$?"        # expect 2, and NO recipe processed
```

The second is the one to check carefully: the failure mode being guarded against
is the recipe being *silently skipped* while the run reports success (see
research.md Finding 4). Confirm nothing was generated and the message names the
offending recipe and key.

## Scenario 6 — Metrics (needs a pushgateway)

With `[pushgateway]` configured in the cookbook, run a recipe that aborts, then
query the gateway:

| Metric | Expected after an aborted run |
|---|---|
| `coshsh_recipe_aborted` | `1` |
| `coshsh_recipe_render_errors` | the error count for **this** run, not the last good one |
| `coshsh_recipe_render_attempts` | non-zero |
| `coshsh_recipe_render_error_pct` | matches the percentage in the abort log line |
| `coshsh_recipe_missing_templates` | the raw count, whether or not tolerated |
| `coshsh_recipe_tolerate_missing_templates` | `1` if the recipe sets the flag, else `0` — read together with the line above to tell a tolerated absence from a counted failure |
| `coshsh_recipe_last_success` | **unchanged** from the previous successful run — this is the fix |

The `last_success` row is the one to verify by hand. Before this change it
advanced on every run, making `(now - last_success) > threshold` unable to fire.

## Reference

- Counting rules and invariants: [data-model.md](./data-model.md)
- Config keys, metrics, exit codes: [contracts/interfaces.md](./contracts/interfaces.md)
- Verified findings about current behaviour: [research.md](./research.md)
