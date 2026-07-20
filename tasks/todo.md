# Todo: 007 Template Rendering Error Handling

Task list lives in `specs/007-template-render-errors/tasks.md`. This file carries
the working notes and the results those tasks reference.

## Working Notes

### T001 — Baseline test suite (before any source change)

```
cd tests && python -m pytest -q
215 passed, 6 skipped in 31.30s
```

Matches the count plan.md and quickstart.md predict. Every later "unchanged from
baseline" assertion compares against **215 passed / 6 skipped**.

### Machine (fixed for every timing comparison in this feature)

| | |
|---|---|
| Kernel | Linux 7.1.4-200.fc44.x86_64 |
| Arch | x86_64 |
| CPUs | 4 |
| Python | 3.14.6 |

T001b and T047a must both run here. A wall-clock comparison across machines is
not evidence.

### T001b — Constitutional benchmark baseline (unmodified code)

```
cd tests && python -m pytest test_performance.py -m benchmark -q -s
```

Fixture: 6,000 hosts x 1 Red Hat application; `os_linux_default.tpl` renders 11
services per application = **66,000 services** (constitutional floor is 60,000).

| Run | Elapsed |
|---|---|
| 1 | 1.979 s |
| 2 | 1.989 s |
| 3 | 1.964 s |
| 4 | 1.957 s |

**Baseline median: 1.979 s** against a 10 s budget. Spread across four runs is
32 ms, so anything inside roughly +/- 0.1 s at T047a is run-to-run noise.

Measured on the machine recorded above, on `master` at aa39d9b with no source
file yet modified.

## Results

### Test suite (T047)

| | Before | After |
|---|---|---|
| `pytest -q -m "not benchmark"` | 215 passed, 6 skipped | **253 passed, 6 skipped, 1 deselected** |

+38 tests, no pre-existing test newly failing. The two load-bearing regression
witnesses still hold at their original values: `test_classes.py:100`
(`render_errors == 1`) and `test_recipes.py:178` (`render_errors == 3`) — both
are syntax-error-kind failures, which were counted before and still are
(research.md Finding 3).

`test_dest.DatarecipientTest.test_create_recipe_fallback_datarecipient_write`
still passes with its `render_errors` now 1 instead of 0 — the one intended
behaviour change, confirmed in the log by the `cannot find template
os_windows_kaas` line it now counts.

### Constitutional benchmark (T047a)

Same machine as T001b, three runs, median of the run set:

| | Median | Range |
|---|---|---|
| Baseline (unmodified) | 1.979 s | 1.957 – 1.989 |
| After | **2.024 s** | 1.934 – 2.071 |

Median delta +0.045 s (+2.3%), but the ranges overlap substantially — the
fastest post-change run (1.934 s) is faster than *every* baseline run. That is
run-to-run noise on a 4-CPU shared machine, not a regression, which matches the
expectation: the added work is O(1) integer increments per render attempt, with
no new I/O and no new allocation per object. Both figures sit at roughly a fifth
of the 10 s constitutional budget for 66,000 services.

### Manual verification (T048)

Quickstart Scenario 5 walked by hand — all four exit codes confirmed:

| Command | Exit | Verified |
|---|---|---|
| `--recipe RENDERR_ABORT` | `4` | `objects_dir` never created |
| bad `max_render_error_pct` | `2` | neither recipe in the cookbook produced output |
| bad `max_delta` | `2` | same — the pre-existing silent-drop hole is closed |
| `--recipe RENDERR_MULTI_GOOD` | `0` | published normally |

The abort log line reads exactly as FR-011 requires:

```
ERROR - recipe renderr_abort aborted: 5 of 10 renderings failed
(50.0000%, maximum is 0.0%). nothing was written, the previous output is unchanged
```

Quickstart Scenario 6 was **not** walked against a live pushgateway — none is
available in this environment. It is covered instead by
`test_pushgateway.RenderErrorMetricsTest`, which stands in for
`pushadd_to_gateway` and asserts on the exact registry contents that would have
been pushed. That is a stronger assertion than scraping a gateway for the
`last_success` case in particular, because what matters there is a metric being
*absent* from the push (pushadd only replaces the metrics it carries). The
`last_success` test was verified to be load-bearing by temporarily reverting its
guard and watching it fail.

### What changed

| File | Change |
|---|---|
| `coshsh/rendertally.py` | **new** — counters, percentage, abort verdict; pure, no I/O |
| `coshsh/item.py` | records attempts and the two failure kinds; missing templates now counted |
| `coshsh/recipe.py` | owns the tally; `render_errors` became a read-only property; `RecipeInvalidConfig`; `validated_setting` and the three run-safety settings |
| `coshsh/generator.py` | abort gate between `render()` and `output()`; re-raises `RecipeInvalidConfig`; five new gauges; `last_success` corrected; `run()` returns the abort count |
| `bin/coshsh-cook` | exit `4` on abort, exit `2` on invalid config |
| `tests/` | 3 new modules, 1 new fixture tree, 5 cookbooks, 4 existing modules extended |
| docs | `cookbook.md`, `docs/ai_handover.md`, `Changelog`, `origin-sketch.md` |

Net effect on `recipe.py`'s render path is a **reduction**: six `+=`
accumulation sites collapsed to plain calls.

## Simplification pass (post-implementation review)

Reviewing the finished diff surfaced three things worse than they needed to be,
one of them introduced by this feature rather than inherited. All behaviour is
unchanged; the counts pinned by `test_recipes.py:178` (`== 3`) and
`test_classes.py:100` (`== 1`) are untouched.

| Change | Effect |
|---|---|
| `Item.render()`: compute `output_name`, then one call | Three ~240-char duplicate calls become one; `functools.reduce(lambda x, y: x and y, ...)` becomes `all(...)`; `import functools` retired |
| `RenderTally.record(outcome)` replaces `record_attempt` / `record_missing` / `record_error` | Four `if tally is not None:` guards become one; the parallel local `render_errors` counter inside `render_cfg_template` is gone; an attempt and its outcome can no longer be recorded separately |
| `Generator.export_recipe_metrics()` extracted, gauges data-driven | `run()` 193 → 124 lines, nesting 8 → 6 levels; two consecutive `recipe_completed and has_prometheus` blocks merged |
| `item._TemplateFailure` remembered in `template_cache` | A broken/absent template is parsed and reported **once per run** instead of once per affected object |

The second one is the one worth remembering. The rule-match failure path had
needed an eight-line comment explaining why it called `record_attempt()` *and*
`record_error()` when every other site called only `record_error()`. That comment
existed because the API permitted the mistake — and the mistake is silent, since
a missed attempt only shrinks the denominator and flatters the percentage the
abort decision is made on. With one `record(outcome)` call the pitfall is
unreachable and the comment is one line.

### Log volume (the `_TemplateFailure` change)

Measured end to end, one recipe with 5 hosts sharing one broken template:

| | Before | After |
|---|---|---|
| Syntax-error lines in the log | 5 | **1** |
| Tracebacks | 5 | **1** |
| `render_errors` | 5 | **5** (unchanged) |

At the benchmark's scale one broken template meant 60,000 file reads, 60,000
parses and 60,000 tracebacks. Guarded by
`test_logging.RenderErrorLoggingTest.test_a_broken_template_is_reported_once_not_once_per_object`,
verified load-bearing (fails `5 != 1` with the caching reverted).

Subsequent hits log at DEBUG naming the object. Note this reaches the **console**
under `--debug` and never the log file, because the file handler is pinned at
INFO (`coshsh/util.py:305`). That is the right trade: a template that fails to
*load* is broken for every object equally, whereas a failure while *rendering* is
genuinely object-specific and still logs per object at CRITICAL.

### Failure breakdown in the log

Because a template that fails to load is now reported once per run rather than
once per object, counting log lines no longer reconstructs *which kind* of
failure occurred. `RenderTally.breakdown` puts that split back, in the one line
that already carried the count:

```
INFO  - recipe renderr_all_kinds completed with 3 problems out of 4 rendering attempts [1 missing, 2 faulty]
INFO  - recipe renderr_tolerate completed with 0 problems out of 7 rendering attempts [5 missing (tolerated)]
ERROR - recipe renderr_all_kinds_abort aborted: 3 of 4 renderings failed [1 missing, 2 faulty] (75.0000%, maximum is 0.0%). nothing was written, the previous output is unchanged
```

Empty on a clean run, so no zero-count noise. This keeps the log self-sufficient
for debugging: whoever reads it at 3am may not have Prometheus in front of them,
even though `coshsh_recipe_missing_templates` and `coshsh_recipe_render_errors`
carry the same split.

### Verification after the pass

- `pytest -q -m "not benchmark"` → **258 passed, 6 skipped, 1 deselected**
  (253 before the pass; +1 net tally test, +1 log-volume test, +3 breakdown tests)
- Metrics tests re-validate the extracted helper gauge-for-gauge, including which
  gauges are absent on the abort path
- Benchmark median **2.041 s** (baseline 1.979 s, pre-pass 2.024 s) — same noise band
- Exit codes re-walked by hand: 4 / 2 / 2 / 0
