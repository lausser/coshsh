# Implementation Plan: Template Rendering Error Handling

**Branch**: `master` (no feature branch; no `before_specify` hook registered) | **Date**: 2026-07-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/007-template-render-errors/spec.md`

## Summary

Measure template errors against template render attempts within a single recipe
run, and abort the run — publishing nothing — when the failure percentage exceeds
a configured tolerance, including a tolerance of `0` meaning "abort on any
failure". Missing templates count as template errors by default and can
optionally be excluded from the percentage while remaining counted and logged.
Export the resulting counters to Prometheus as generation-quality signals, and
correct the success timestamp so freshness alerting works.

Technical approach: replace the current return-value accumulation of
`render_errors` with a single small value object (`RenderTally`) owned by the
`Recipe` and mutated in place by `Item` — which already receives the recipe. This
removes six accumulation sites rather than adding to them, and isolates the
percentage/verdict arithmetic into a pure, dependency-free unit that can be tested
at the precision the feature demands (1 failure in 10^9 must still abort).

## Technical Context

**Language/Version**: Python 3.12+ (constitution Technology Constraints); runtime under test here is 3.14

**Primary Dependencies**: Jinja2 (templating, existing), `configparser` via `coshsh.configparser` (existing), `prometheus_client` (existing, optional at runtime)

**Storage**: Filesystem — generated config files under `objects_dir`; no database

**Testing**: pytest (constitution: pytest exclusively; existing suite is 215 passed / 6 skipped)

**Target Platform**: Linux server (unattended, cron/scheduler-driven)

**Project Type**: Single Python package (`coshsh/`) plus CLI entry point (`bin/coshsh-cook`)

**Performance Goals**: No regression against the constitutional benchmark — ≥ 60,000 services in ≤ 10 seconds. The added work is O(1) integer increments per render attempt.

**Constraints**: Deterministic output; the percentage comparison must never be rounded before evaluation; abort must leave previously published output byte-for-byte untouched

**Scale/Scope**: 5 source files touched (`item.py`, `recipe.py`, `generator.py`, `bin/coshsh-cook`, plus the new module's importers), 1 new source file (`coshsh/rendertally.py`), 3 new test modules and 1 new test fixture tree, 5 existing test modules extended, 3 doc files (`cookbook.md`, `docs/ai_handover.md`, `Changelog`); no new runtime dependency

No NEEDS CLARIFICATION items remain — 8 clarifications were resolved in the spec's
Clarifications section before planning.

## Constitution Check

*GATE: evaluated before Phase 0 and re-evaluated after Phase 1 design.*

| Principle | Assessment | Verdict |
|---|---|---|
| **I. Configuration-as-Code** | Feature strengthens it: an aborted run preserves the last generated state rather than publishing a partial one. No manual editing introduced. | PASS |
| **II. Extensibility via Class and Template Files** | No change to the class/template extension mechanism. `Item.render()`'s signature is unchanged, so existing subclass overrides (`GenericApplication`, `GenericContact`) keep working untouched — verified, neither accumulates counts itself. | PASS |
| **III. Test-First (NON-NEGOTIABLE)** | Every task below is sequenced tests-first; `RenderTally` is a pure unit under test before wiring. Includes a fixture for the render-raise path, which currently has **zero** coverage. | PASS |
| **IV. Performance and Correctness at Scale** | Added work is integer increments per render attempt; no new I/O and no new allocation per object. The constitutional benchmark is measured rather than assumed: T001a records a baseline on unmodified code and T047a re-measures after, both against a new `tests/test_performance.py`. No such benchmark existed before this feature — spec 005 optimized the pipeline on complexity analysis alone — so this feature also closes that gap. Determinism unaffected. | PASS |
| **V. Simplicity and Minimal Surface Area** | Two cookbook keys, one small class, two counters (not four — the finer split was dropped as speculative). Net effect on `recipe.py` is a **reduction**: six `+=` sites collapse to plain calls. | PASS |
| **VI. AI-First Development (NON-NEGOTIABLE)** | All new code carries WHY comments, matching the density already present in `item.py`/`recipe.py`. The non-obvious invariants (never round before comparing; why the denominator shrinks under tolerate) are commented at their site. | PASS |

**Technology Constraints**: Python 3.12+ only, no pre-3.12 shims in this change
(the legacy-compat carve-out is not invoked). Jinja2 remains the exclusive
templating engine. INI cookbook format extended with two keys — additive, no
format change, no MAJOR bump required. pytest only.

**Result: PASS — no violations, Complexity Tracking table not required.**

## Project Structure

### Documentation (this feature)

```text
specs/007-template-render-errors/
├── plan.md              # This file
├── research.md          # Phase 0 — verified findings from the existing code
├── data-model.md        # Phase 1 — RenderTally and the counting rules
├── quickstart.md        # Phase 1 — how to validate the feature end to end
├── contracts/
│   └── interfaces.md    # Phase 1 — cookbook keys, metrics, exit codes
├── checklists/
│   └── requirements.md  # Spec quality checklist (from /speckit-specify)
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
coshsh/
├── rendertally.py       # NEW — RenderTally: counters, percentage, verdict
├── item.py              # record attempts and the two error kinds
├── recipe.py            # own the tally; parse the two keys; RecipeInvalidConfig
├── generator.py         # abort gate; metrics on abort; last_success correction
└── datarecipient.py     # unchanged (max_delta path untouched)

bin/
└── coshsh-cook          # exit codes for abort and for config-syntax errors

tests/
├── test_rendertally.py   # NEW — pure unit tests for the arithmetic
├── test_render_errors.py # NEW — integration: abort, tolerate, preservation
├── test_performance.py   # NEW — the 60k/10s constitutional benchmark
├── recipes/renderr/      # NEW — fixture: good, broken, missing, raising templates
├── test_recipeattrs.py   # cookbook key validation
├── test_bin.py           # CLI exit codes 2 and 4
├── test_pushgateway.py   # the new gauges and the last_success correction
├── test_logging.py       # per-failure messages, summary and abort lines
├── test_dest.py          # documented behaviour change (render_errors 0 → 1)
├── test_classes.py       # existing assertion on render_errors (must stay 1)
└── test_recipes.py       # existing assertion on render_errors (must stay 3)

.claude/skills/coshsh-classes/references/cookbook.md   # document both keys
docs/ai_handover.md                                    # metrics, exit codes, run() contract
Changelog                                              # one-liner, added at completion
```

**Structure Decision**: Single Python package, no new subpackage. `rendertally.py`
is a new top-level module in `coshsh/`, matching the project's existing
one-concept-per-module convention (`templaterule.py`, `datasource.py`).

## Design Decisions

### 1. In-place tally instead of return-value threading

`Item.render(template_cache, jinja2, recipe)` already receives the recipe, so at
that level the counters need no plumbing. The earlier sketch
(`TEMPLATE-ERRORS.md`) proposed returning `(errors, attempts)` tuples through two
signatures and six call sites; adding a third value would have made it a
four-tuple. Rejected.

One level down the recipe is *not* a declared parameter:
`Item.render_cfg_template(jinja2, template_cache, name, output_name, suffix,
for_tool, _skip_pythonize=False, **kwargs)` (item.py:185) receives the recipe only
inside `**kwargs`, because `Item.render()` packs it there for the template
namespace (item.py:283-287). Four of the six recording sites live in
`render_cfg_template`, so it gains **one explicit keyword parameter**,
`tally: RenderTally | None = None`, passed by name from its three call sites.

Explicit over `kwargs["recipe"].render_tally`: the tally is a parameter of the
function's own contract, not part of the caller-supplied template namespace that
`**kwargs` exists to carry. Digging it out of `kwargs` would couple the counting
to an unrelated dict whose keys are set by template-rule configuration
(`rule.self_name`), and would silently count nothing if a caller ever omitted
`recipe`. The default of `None` keeps the parameter optional for any out-of-tree
caller, and its absence means "do not count" rather than raising.

`Recipe.render_errors` becomes a read-only property delegating to the tally, so
the two existing test assertions, the summary log line, and the Prometheus gauge
keep working with no call-site changes.

### 2. Two counted kinds, not four

`missing` (template file not found) and `errors` (Jinja2 syntax error, Python
error, missing attribute, template-rule evaluation failure). The finer
distinctions remain visible in the existing distinct log messages but are not
counted apart — nothing in the policy needs them separated.

### 3. Config-syntax errors must not be swallowed

`Generator.add_recipe()` (generator.py:94-98) currently catches **every**
exception from `Recipe.__init__` and logs-and-continues, silently dropping the
recipe. That is exactly the outcome FR-016 forbids. A malformed tolerance must
therefore raise a **dedicated** exception type that `add_recipe` re-raises rather
than swallows — following the existing `RecipePid*` exception convention in
`recipe.py`. See research.md for the full trace.

### 4. Abort placement

Between `recipe.render()` and `recipe.output()` in the `Generator.run()` loop.
`output()` is what calls `cleanup_target_dir()` and then writes; skipping it
entirely is what makes the previous run's output survive. `recipe.pid_remove()`
stays where it is, outside the inner block, so the lock is released on abort.

## Constitution Re-Check (post-design)

Re-evaluated after Phase 1 artifacts were written. No gate changed verdict.

Two points the design surfaced that were worth re-testing against the
constitution:

- **Principle V (minimal surface)** — Phase 1 added a second exception class
  (`RecipeInvalidConfig`) and four Prometheus metrics beyond the original single
  counter. Re-checked: the exception is required by FR-016 and follows an
  existing convention (three `RecipePid*` classes already exist), and each metric
  maps to a specific requirement (FR-017a/b/d) rather than being speculative.
  `render_error_pct` was the only debatable one — kept because with
  `tolerate_missing_templates` on, it cannot be derived externally without
  reimplementing the policy. Still PASS.
- **Principle II (no core changes for app behaviour)** — `add_recipe` gains a
  re-raise clause, which is core. Re-checked: this is framework error-handling,
  not application-specific behaviour, and it corrects a case where core silently
  discarded a recipe. Still PASS.

**Result: PASS. Complexity Tracking not required.**

## Complexity Tracking

> Not required — Constitution Check passed with no violations, before and after design.
