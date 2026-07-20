---
description: "Task list for Template Rendering Error Handling"
---

# Tasks: Template Rendering Error Handling

**Input**: Design documents from `/specs/007-template-render-errors/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/interfaces.md, quickstart.md

**Tests**: INCLUDED. Constitution Principle III (Test-First) is NON-NEGOTIABLE, and plan.md sequences every task tests-first. Test tasks are therefore mandatory, not optional, and MUST fail before their implementation task is started.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Exact file paths are given in every task

## Path Conventions

Single Python package at repository root: `coshsh/` (source), `tests/` (pytest suite), `bin/` (CLI entry point). Paths below are repository-root-relative.

**Note on SC-007**: The constitutional benchmark (≥ 60,000 services in ≤ 10 s, Principle IV and Workflow §5) has **never been automated** — `specs/005-performance-optimization` optimized the pipeline on complexity analysis alone, and `tests/` contains no timing code. This feature therefore measures rather than assumes: T001a establishes a baseline on unmodified code and T047a re-measures the same benchmark afterwards. The added work is O(1) integer increments per render attempt, so no measurable change is expected — T001a/T047a are what turn that expectation into evidence.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the baseline that later "unchanged from baseline" assertions compare against

- [X] T001 Run `cd tests && python -m pytest -q` and record the exact pass/skip counts (expected 215 passed, 6 skipped) into a `## Working Notes` section in `tasks/todo.md`
- [X] T001a [P] Create `tests/test_performance.py`: a benchmark that generates a synthetic CSV datasource large enough to yield ≥ 60,000 services, runs the full `collect → assemble → render → output` pipeline once via `Generator.run()`, and asserts the wall-clock elapsed time is ≤ 10 seconds (constitution Principle IV). Build the CSV into a temp dir at setup following the `tests/recipes/test10/data/csv10.*_hosts.csv` column layout — do **not** commit a 60k-row fixture. Mark it `@pytest.mark.benchmark` and register the marker in `tests/conftest.py` so the normal suite can deselect it with `-m "not benchmark"`; it is a gate, not a per-run test. Print the elapsed time so it is readable from the run output
- [X] T001b Run the benchmark on **unmodified** code (`cd tests && python -m pytest test_performance.py -m benchmark -q -s`) and record the elapsed seconds, the service count, and the machine it ran on into `## Working Notes` in `tasks/todo.md`. This number is the baseline T047a compares against — without it, "no regression" is unfalsifiable

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The `RenderTally` value object, its ownership by `Recipe`, the recording calls in `Item`, and the shared test fixtures. Every user story below reads or writes these.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Write failing unit tests for the tally arithmetic in `tests/test_rendertally.py` covering every row of quickstart.md Scenario 1: `attempts=1_000_000, errors=1, max_pct=0` aborts; `attempts=1_000_000_000, errors=1, max_pct=0` aborts (no-rounding guard); `attempts=0` no abort and no `ZeroDivisionError`; `errors=0, max_pct=0` no abort (strict `>`); `max_pct=None` never aborts; `tolerate_missing=True, attempts=10, missing=9, errors=1` yields `error_pct == 100.0`; `tolerate_missing=True, attempts=10, missing=10` no abort and no `ZeroDivisionError`
- [X] T003 [P] Create the shared test fixture recipe in `tests/recipes/renderr/` — a `classes/` file declaring three template rules (one pointing at a good template, one at a deliberately broken template, one at a template that does not exist) plus `templates/` holding the good and broken `.tpl` files, following the layout of the existing `tests/recipes/test9/`
- [X] T004 Create `coshsh/rendertally.py` with class `RenderTally` holding `attempts`, `missing`, `errors`, `max_error_pct`, `tolerate_missing`; recording methods; and derived properties `template_errors`, `accountable_attempts`, `error_pct`, `too_many_errors` exactly as specified in data-model.md "Derived values". Add WHY comments at the two non-obvious invariants: never round before comparing (defeats `max_error_pct = 0`) and why the denominator shrinks under `tolerate_missing`. Makes T002 pass
- [X] T005 In `coshsh/recipe.py`, instantiate `self.render_tally = RenderTally(...)` in `Recipe.__init__` replacing `self.render_errors = 0` (recipe.py:345), and add `render_errors` as a read-only property delegating to `self.render_tally.template_errors`
- [X] T006 In `coshsh/recipe.py`, delete the six `self.render_errors += x.render(...)` accumulation sites (recipe.py:545-564), reducing each to a plain `x.render(...)` call
- [X] T007 In `coshsh/item.py`, give `render_cfg_template()` (item.py:185) an explicit keyword parameter `tally=None` inserted before `**kwargs`, and pass it by name from all three call sites in `Item.render()` (item.py:283, 285, 287) as `tally=recipe.render_tally`. Do **not** reach into `kwargs["recipe"]` — the recipe is in `kwargs` only because it is part of the template namespace, and coupling the counting to it would silently count nothing if a caller omitted it (plan.md Design Decision 1). Then increment `tally.attempts` once on entry before any outcome is known, and route the three existing counted paths to `tally`: `except TemplateSyntaxError` (item.py:222) → `errors`, `except Exception` on template load (item.py:229) → `errors`, `except Exception` on `template.render()` (item.py:248) → `errors`. Guard every recording call with `if tally is not None`, or give `RenderTally` no-op-safe call sites — `tally=None` means "do not count" and must never raise
- [X] T008 In `coshsh/item.py`, change the template-rule-match failure path in `Item.render()` (item.py:273) to record both `attempts` and `errors` on `recipe.render_tally` — this site is inside `Item.render()`, which receives the recipe as a declared parameter, so no `tally` argument is involved here — with a WHY comment explaining that a rule which should have produced output but did not must count as an attempt, otherwise the denominator is flattered
- [X] T009 Run `cd tests && python -m pytest test_classes.py test_recipes.py -q` and confirm `test_classes.py:100` still asserts `render_errors == 1` and `test_recipes.py:178` still asserts `render_errors == 3` — both are syntax-error-kind failures and must be numerically unchanged (research.md Finding 3)

**Checkpoint**: Counting infrastructure in place; `render_errors` still means what it meant before. User stories can now begin.

---

## Phase 3: User Story 1 - A missing template is counted as a failure (Priority: P1) 🎯 MVP

**Goal**: A template rule that fires against a template file which is not on the path counts as a template error, equal in weight to a broken template, with a per-recipe opt-out.

**Independent Test**: Run a recipe whose template rule references a non-existent template and observe that `recipe.render_errors` includes it; set `tolerate_missing_templates = yes` and observe it leaves both numerator and denominator while still being counted in `render_tally.missing`.

### Tests for User Story 1 ⚠️

> Write these FIRST and confirm they FAIL before T013/T014

- [X] T010 [P] [US1] Write failing test in `tests/test_render_errors.py`: a recipe using the `tests/recipes/renderr/` fixture with one missing template asserts `recipe.render_errors == 1` and `recipe.render_tally.missing == 1` (spec Acceptance Scenario US1-1)
- [X] T011 [P] [US1] Write failing test in `tests/test_render_errors.py`: the same missing template referenced by many objects yields a `missing` count and an `attempts` count reflecting every affected rendering, not one deduplicated entry (US1-3)
- [X] T012 [P] [US1] Write failing test in `tests/test_render_errors.py`: with `tolerate_missing_templates = yes`, `render_tally.missing` is still non-zero while `render_errors` excludes it and `accountable_attempts` excludes those attempts (US1-2, FR-001b, FR-001c)

### Implementation for User Story 1

- [X] T013 [US1] In `coshsh/item.py`, count the `except TemplateNotFound` branch (item.py:225) as `missing` on the `tally` parameter added in T007, leaving the existing `logger.error("cannot find template " + name)` line at its current level and wording per the spec clarification
- [X] T014 [US1] In `coshsh/recipe.py`, parse the `tolerate_missing_templates` cookbook key in `Recipe.__init__` following the existing `git_init` `yes`/`no` idiom, default `no`, and pass it into the `RenderTally` constructor
- [X] T015 [US1] Run `cd tests && python -m pytest test_dest.py -q` and confirm `test_dest.DatarecipientTest.test_create_recipe_fallback_datarecipient_write` still passes with its `render_errors` now 1 instead of 0 — the documented, intended behaviour change (research.md Finding 2)

**Checkpoint**: Missing templates are visible in the failure count for the first time. Valuable on its own — operators can alert on the existing `coshsh_recipe_render_errors` metric and finally see them.

---

## Phase 4: User Story 2 - Abort the run when too many renderings fail (Priority: P1)

**Goal**: A recipe exceeding its configured failure tolerance publishes nothing, leaving the previous run's output byte-for-byte intact.

**Independent Test**: Configure the fixture recipe with a broken template and `max_render_error_pct = 0`, run it, and verify no output file was written or removed and the previous output is byte-for-byte identical.

### Tests for User Story 2 ⚠️

- [X] T016 [P] [US2] Write failing test in `tests/test_render_errors.py`: run the fixture recipe once with good templates and checksum `objects_dir`; swap in the broken template and run again with `max_render_error_pct = 0`; assert the run aborts and the checksum is unchanged — nothing added, changed, or deleted (US2-1, US2-2, FR-008, SC-003)
- [X] T017 [P] [US2] Write failing test in `tests/test_render_errors.py`: a recipe with `max_render_error_pct = 5` and 2% of renderings failing publishes normally (US2-3, FR-007)
- [X] T018 [P] [US2] Write failing test in `tests/test_render_errors.py`: a recipe with no `max_render_error_pct` configured and failing renderings publishes exactly as today (US2-4, FR-007, research.md Finding 8)
- [X] T019 [P] [US2] Write failing test in `tests/test_render_errors.py`: a recipe collecting zero objects with `max_render_error_pct = 0` does not abort and raises no arithmetic error (US2-5, FR-015)
- [X] T020 [P] [US2] Write failing test in `tests/test_recipeattrs.py`: `max_render_error_pct` values `"abc"`, `""`, `"-5"`, `"250"`, and `"100.1"` each raise `RecipeInvalidConfig`, while absent yields `None`, `"0"` yields `0.0`, `"12.5"` yields `12.5`, and `"100"` yields `100.0`. Add a companion test that a recipe with `max_render_error_pct = 100` and *every* rendering failing still does not abort — 100 is the ceiling and the comparison is strict `>` (spec Edge Cases, data-model.md validation table)
- [X] T020a [P] [US2] Write failing test in `tests/test_recipeattrs.py` for the corrected `max_delta` validation (FR-016a): `"abc"`, `"10:abc"`, and `"10:20:30"` each raise `RecipeInvalidConfig`, while `"10"` still yields `(10, 10)`, `"10:20"` still yields `(10, 20)`, and an absent value still yields `()` — the accepted values must be provably unchanged, since this task tightens an existing setting rather than adding a new one. Add a companion test in `tests/test_bin.py` asserting a cookbook with `max_delta = abc` exits `2` with **no** recipe processed, where today it would silently process the other recipes and drop this one

### Implementation for User Story 2

- [X] T021 [US2] Add the `RecipeInvalidConfig` exception class to `coshsh/recipe.py` beside the existing `RecipePidAlreadyRunning` / `RecipePidNotWritable` / `RecipePidGarbage` classes (recipe.py:68-84). It carries the offending key, the raw value, and what was expected, so the message names the setting instead of surfacing a bare `invalid literal for int()`
- [X] T021a [US2] Add the shared `validated_setting(key, raw, convert, accept=None, expected="")` helper to `coshsh/recipe.py` exactly as specified in data-model.md "The shared validation rule", with a WHY comment recording that it exists so a run-safety setting added later inherits refuse-the-run behaviour by declaring a converter rather than writing its own error handling (FR-016b), and that its scope is deliberately the three run-safety settings — routing every cookbook key through it would be a speculative abstraction under constitution Principle V
- [X] T022 [US2] In `coshsh/recipe.py`, parse `max_render_error_pct` in `Recipe.__init__` alongside the existing `max_delta` parsing (recipe.py:189-195) as a single float — not the `H:S` pair form — routed through `validated_setting` with `convert=float` and `accept=0.0 <= v <= 100.0`, so non-numeric, empty, negative, and above-100 values all raise `RecipeInvalidConfig` — the valid domain is `0.0 <= value <= 100.0` inclusive, with a WHY comment noting that `100` and `250` behave identically at runtime but `250` is rejected because accepting it would mean silently accepting a value the author plainly did not mean; pass the result into the `RenderTally`. Makes T020 pass
- [X] T023 [US2] Make `Recipe.__init__` raise `RecipeInvalidConfig` for an invalid `tolerate_missing_templates` value too, routed through `validated_setting` (contracts/interfaces.md §1)
- [X] T023a [US2] In `coshsh/recipe.py`, route the existing `max_delta` parsing (recipe.py:191-195) through `validated_setting` so a malformed value raises `RecipeInvalidConfig` instead of a bare `ValueError` that `add_recipe` swallows (FR-016a). Two constraints, both with WHY comments: keep the `isinstance(self.max_delta, str)` guard exactly as it is — `self.max_delta` is also handed around as an already-parsed tuple (recipe.py:314 → `add_datarecipient`), so validation applies only where parsing applies; and validate **structure only** (one integer, or two separated by a colon), adding no range bound, so every value accepted today keeps working and the change converts a crash-and-silently-drop into a named refusal and nothing else. Makes T020a pass
- [X] T024 [US2] In `coshsh/generator.py`, insert the abort gate between `recipe.render()` and `recipe.output()` in the `Generator.run()` loop (generator.py:165-168): when `recipe.render_tally.too_many_errors` is true, skip `output()` entirely so `cleanup_target_dir()` never runs. Add a WHY comment stating that skipping `output()` is precisely what preserves the previous run's files. Makes T016 pass

**Checkpoint**: US1 and US2 together are the minimum viable protection — the signal is complete and something acts on it.

---

## Phase 5: User Story 3 - An aborted run leaves the system ready for the next attempt (Priority: P2)

**Goal**: An abort releases the pid lock, does not report success, does not stop the other recipes in the cookbook, and surfaces as a distinct process exit code.

**Independent Test**: Trigger an abort, then run the same recipe again with the template fixed and verify it completes and publishes with no manual cleanup.

### Tests for User Story 3 ⚠️

- [X] T025 [P] [US3] Write failing test in `tests/test_render_errors.py`: after an aborted run, a second run of the same recipe with the template fixed completes and publishes with no manual cleanup, proving the pid lock was released (US3-1, FR-010, SC-004)
- [X] T026 [P] [US3] Write failing test in `tests/test_render_errors.py`: a cookbook with several recipes where one aborts still processes the others normally (US3-3, FR-014)
- [X] T027 [P] [US3] Write failing test in `tests/test_bin.py`: `bin/coshsh-cook` exits `4` when a recipe aborted on template errors, and exits `2` with no recipe processed when a cookbook declares `max_render_error_pct = abc` (FR-014a, FR-016, SC-001a, contracts/interfaces.md §2)

### Implementation for User Story 3

- [X] T028 [US3] In `coshsh/generator.py`, verify and if necessary adjust that `recipe.pid_remove()` stays outside the inner block so the lock is released on the abort path (plan.md Design Decision 4)
- [X] T029 [US3] In `coshsh/generator.py`, have `Generator.run()` return the number of recipes that aborted — safe because all nine existing call sites discard the return value (research.md Finding 7)
- [X] T030 [US3] In `coshsh/generator.py`, make `Generator.add_recipe()` catch and re-raise `RecipeInvalidConfig` ahead of its blanket `except Exception` (generator.py:94-98), so a malformed value can never result in the recipe being silently skipped. This is what closes the hole for **both** the new settings and `max_delta` (T023a) — the blanket handler is the reason a `max_delta` typo currently drops a recipe without stopping the run. Leave the blanket `except Exception` in place for every other construction failure; narrowing it further is out of scope and was explicitly rejected during clarification. Update the method's docstring, which currently states that any exception silently skips the recipe
- [X] T031 [US3] In `bin/coshsh-cook`, exit `4` when `Generator.run()` reports one or more aborted recipes, and exit `2` on `RecipeInvalidConfig` before any recipe is processed, reusing the existing bad-cookbook code path (generator.py:259). Makes T027 pass
- [X] T031a [US3] Write a failing test in `tests/test_logging.py` asserting an aborted recipe is **not** logged as completed, then in `coshsh/generator.py` stop the end-of-run summary line (generator.py:213, currently `"recipe %s completed with %d problems"`) from firing on the abort path and emit a distinct abort line instead. FR-009 forbids reporting an aborted run as a successful completion, and "completed with N problems" reads as success-with-caveats to both an operator and a log scraper. The abort line's *content* (failures, attempts, percentage, configured maximum) is T043's job under FR-011; this task is only about not claiming completion

**Checkpoint**: The abort is now a safe, recoverable, schedulable failure mode rather than a pipeline outage.

**Known carry-over**: spec Acceptance Scenario US3-2 has two halves. "Not reported as a successful completion" lands here (T031a). "Any external health signal the recipe emits reflects failure rather than success" is the `coshsh_recipe_last_success` correction, which lands in Phase 6 (T037) — US3 is not fully closed until that ships. This is a deliberate sequencing choice: T037 belongs with the other Prometheus work and its test (T034) needs the pushgateway fixtures, so splitting it into this phase would drag the metrics stack forward for one assignment.

---

## Phase 6: User Story 5 - Track generation quality over time in observability (Priority: P2)

**Goal**: The counters become a continuous quality signal in Prometheus, and the success timestamp finally ages correctly.

**Independent Test**: Run a recipe with a mix of missing and faulty templates and confirm the exported metrics carry each raw category count, the attempt count, and the run's outcome — enough to compute the failure rate without reading a log line.

### Tests for User Story 5 ⚠️

- [X] T032 [P] [US5] Write failing test in `tests/test_pushgateway.py`: after a run with missing and faulty templates, the pushed metrics include `coshsh_recipe_missing_templates` and `coshsh_recipe_render_errors` as separate raw counts, plus `coshsh_recipe_render_attempts` and `coshsh_recipe_render_error_pct` (US5-1, US5-2, FR-017a/b)
- [X] T032a [P] [US5] Write failing test in `tests/test_pushgateway.py`: run the same fixture twice, once with `tolerate_missing_templates = no` and once with `yes`, and assert `coshsh_recipe_missing_templates` is identical in both while `coshsh_recipe_tolerate_missing_templates` is `0` then `1` — so a consumer can distinguish a tolerated absence from a counted failure, which the missing count alone cannot express (US5-3, FR-017c)
- [X] T033 [P] [US5] Write failing test in `tests/test_pushgateway.py`: an aborted run exports `coshsh_recipe_aborted = 1` and exports render counts belonging to that run, not the previous one (US5-4, FR-017d/e, SC-009)
- [X] T034 [P] [US5] Write failing test in `tests/test_pushgateway.py`: `coshsh_recipe_last_success` does not advance for a run that aborted, and does advance for a run that published (US5-7, FR-017g, SC-011)

### Implementation for User Story 5

- [X] T035 [US5] In `coshsh/generator.py`, add the five new gauges `coshsh_recipe_render_attempts`, `coshsh_recipe_missing_templates`, `coshsh_recipe_tolerate_missing_templates`, `coshsh_recipe_render_error_pct`, and `coshsh_recipe_aborted`, sourced from `recipe.render_tally`, keeping `coshsh_recipe_render_errors` at its existing name and meaning (FR-017a/b/c/d/f, SC-010). Add a WHY comment on the tolerate gauge: it exists because `missing_templates` carries the same value whether or not absences are tolerated, so without the flag a consumer cannot tell a tolerated absence from a counted failure. Makes T032 and T032a pass
- [X] T036 [US5] In `coshsh/generator.py`, export the render-related metrics on the abort path as well, since aborted runs are exactly the ones whose counts an operator needs (FR-017e)
- [X] T037 [US5] In `coshsh/generator.py`, move the `coshsh_recipe_last_success` assignment (generator.py:188-192) inside the branch that runs only when the recipe actually published output, with a WHY comment recording that it previously advanced on every run that acquired the pid lock, which made `(now - last_success) > threshold` alerting unable to fire. Makes T034 pass

**Checkpoint**: The feature is useful on the days nothing aborts, and the liveness alarm works.

---

## Phase 7: User Story 4 - Diagnose which templates failed and why (Priority: P3)

**Goal**: Each individual failure remains separately identifiable in the run report even though only two categories are counted.

**Independent Test**: Run a recipe with one missing template, one syntactically broken template, and one template that fails while rendering, and confirm all three are individually identifiable in the log.

### Tests for User Story 4 ⚠️

- [X] T038 [P] [US4] Write failing test in `tests/test_logging.py`: a run containing a missing template, a broken template, and a template that raises while rendering produces three individually distinguishable log messages, each naming the template and the object (US4-1, US4-2, FR-012)
- [X] T039 [P] [US4] Write failing test in `tests/test_logging.py`: the end-of-run summary line reports both the number of failed renderings and the number attempted (US4-3, FR-013)
- [X] T040 [P] [US4] Write failing test in `tests/test_logging.py`: an abort log line reports the failure count, the attempt count, the resulting percentage, and the configured maximum (US2-1, FR-011)

### Implementation for User Story 4

- [X] T041 [US4] Add a test fixture template to `tests/recipes/renderr/templates/` that raises during `template.render()` (not at load time), closing the coverage gap at `coshsh/item.py:243-248` which research.md Finding 3 confirmed is executed by zero of the existing 215 tests
- [X] T042 [US4] In `coshsh/item.py`, ensure each of the three failure paths logs a message that names the template, names the object being rendered where one applies, and distinguishes missing from faulty. Makes T038 pass
- [X] T043 [US4] In `coshsh/generator.py`, extend the end-of-run summary line (generator.py:213) to report attempts alongside errors, and add the abort log line carrying failures, attempts, percentage, and configured maximum. Makes T039 and T040 pass

**Checkpoint**: All five stories independently functional.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T044 [P] Document `max_render_error_pct` and `tolerate_missing_templates` in `.claude/skills/coshsh-classes/references/cookbook.md` alongside the existing `max_delta` / `max_delta_action` run-safety settings (FR-018), and add a note to the `max_delta` entry that a malformed value now refuses the run instead of dropping the recipe — its accepted values are unchanged (FR-016a)
- [X] T044a [P] Update `docs/ai_handover.md` for the behaviour this feature changes: the Prometheus metrics section (~line 3500) gains the five new gauges and the corrected `coshsh_recipe_last_success` semantics; the note at ~line 3520 that "if a recipe fails, partial metrics may still be pushed" needs restating against the new freshness contract (contracts/interfaces.md §3); the `Generator.run()` pipeline description (~lines 338, 637) gains the abort gate between `render()` and `output()`; and the CLI section gains exit code `4`. **Re-locate every section by content, not by the line numbers above** — `docs/ai_handover.md` is being edited concurrently for unrelated reasons, so treat those anchors as stale on arrival and re-read the file first
- [X] T046 Move `TEMPLATE-ERRORS.md` from the repository root to `specs/007-template-render-errors/origin-sketch.md` as the document this feature started from, prefixing it with a short header stating that its *design* is superseded by plan.md and data-model.md while its analysis of current behaviour and of why `max_delta` cannot serve as a render-error signal remains valid. Do not delete it: its "Why `max_delta` doesn't solve this" section (`count_objects()` / `too_much_delta()` mechanics and the three reasons a disk-delta signal is unsuitable) and its float64 precision argument have no counterpart in any other spec artifact
- [X] T047 Run `cd tests && python -m pytest -q -m "not benchmark"` and confirm the count matches the T001 baseline plus the new tests, with no pre-existing test newly failing (SC-005)
- [X] T047a Re-run the benchmark from T001a (`cd tests && python -m pytest test_performance.py -m benchmark -q -s`) on the **same machine** as T001b and compare against the recorded baseline. Confirm the ≤ 10 s constitutional bound still holds and that the delta against baseline is within run-to-run noise — take the median of three runs, since a single wall-clock sample on a shared machine is not evidence. Record both numbers in the `## Results` section of `tasks/todo.md`. If the delta exceeds noise, **stop** and investigate before proceeding: the added work is meant to be O(1) integer increments per attempt, so a real regression means something other than counting was changed (SC-007, constitution Principle IV and Workflow §5)
- [X] T048 Walk quickstart.md Scenarios 5 and 6 manually — the CLI exit codes and, with a pushgateway configured, the metric values after an aborted run, verifying `coshsh_recipe_last_success` by hand
- [X] T049 Review every new code path for the WHY-comment density required by constitution Principle VI, matching the level already present in `coshsh/item.py` and `coshsh/recipe.py`
- [X] T050 Record results and any lessons in `tasks/todo.md` (Results section) and `tasks/lessons.md`
- [X] T045 **Last task of the feature.** Add a one-line entry to `Changelog` (repository root, no file extension, capital C) in the existing `* YYYY-MM-DD VERSION` + indented-summary format, newest first at the top of the file. Per project convention the `Changelog` line is written only once the spec is completely finished, which is why this task is numbered out of order here — everything above it must be done first. Keep it to a one-liner in the house style; the three detailed compatibility notes in contracts/interfaces.md are reference material for the release notes and the commit message, not for `Changelog` itself

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately. T001b MUST run before any source file is touched; once `coshsh/` changes, the baseline it captures is no longer a baseline
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Foundational
- **US2 (Phase 4)**: Depends on Foundational. Independently testable, but its abort tests are far more meaningful once US1 lands, because missing templates are otherwise invisible to the percentage
- **US3 (Phase 5)**: Depends on US2 — the abort path must exist before its recoverability can be tested. Acceptance Scenario US3-2 is only half-closed here (T031a); its other half is T037 in Phase 6
- **US5 (Phase 6)**: Depends on Foundational for the counters and on US2 for `coshsh_recipe_aborted`. The `last_success` correction (T037) depends on nothing but must ship in the same release as T036 — spec.md Assumptions treats them as one unit
- **US4 (Phase 7)**: Depends on Foundational only. Sequenced last by priority (P3), not by dependency
- **Polish (Phase 8)**: Depends on all desired stories. T047a additionally depends on T001b (nothing to compare against otherwise), and T045 runs last of all by project convention — the `Changelog` line is written only once the spec is finished

### Within Each User Story

- Tests are written first and MUST fail before the implementation tasks in the same phase
- `RenderTally` (model) before `Recipe` wiring (service) before `Generator` gate (endpoint)
- Story complete before moving to the next priority

### Parallel Opportunities

- T001 and T001a in Setup (a pytest run and a new test module)
- T002 and T003 in Foundational (different files: a test module and a fixture tree)
- All test tasks within a story: T010–T012, T016–T020 (plus T020a), T025–T027, T032–T034 (plus T032a), T038–T040
- Once Foundational completes, US1, US2, and US4 can be worked in parallel by different developers; US3 and US5 must wait on US2
- T044 and T044a in Polish (a skill reference and `docs/ai_handover.md`)

**Not parallel**: T005–T008 all touch `coshsh/recipe.py` or `coshsh/item.py` and must be sequential. T021–T023a likewise all touch `coshsh/recipe.py`, and T021a must land before T022/T023/T023a since all three call the helper it adds. T024, T028–T031a, T035–T037, and T043 all touch `coshsh/generator.py`. T045 is not parallel with anything — it is the last task of the feature.

---

## Parallel Example: User Story 2

```bash
# Launch all US2 tests together — they are independent assertions in two files:
Task: "Abort preserves previous output byte-for-byte in tests/test_render_errors.py"
Task: "5% tolerance with 2% failures publishes normally in tests/test_render_errors.py"
Task: "No tolerance configured behaves exactly as today in tests/test_render_errors.py"
Task: "Zero attempts does not abort and does not divide by zero in tests/test_render_errors.py"
Task: "Malformed tolerance values raise RecipeInvalidConfig in tests/test_recipeattrs.py"
```

---

## Implementation Strategy

### MVP (User Stories 1 + 2)

1. Phase 1: Setup — capture the baseline
2. Phase 2: Foundational — `RenderTally`, `Recipe` ownership, `Item` recording
3. Phase 3: US1 — missing templates counted
4. Phase 4: US2 — abort on exceeding tolerance
5. **STOP and VALIDATE**: quickstart.md Scenarios 1, 2, and 3

US1 and US2 are jointly the MVP rather than US1 alone. US1 completes the signal but acts on nothing; US2 acts on it but, without US1, an entire failure category stays invisible to the percentage it is deciding on. Shipping either alone delivers a partial safety mechanism that an operator could reasonably mistake for a complete one.

### Incremental Delivery

1. Setup + Foundational → counting infrastructure, `render_errors` semantics unchanged
2. US1 + US2 → MVP, abort protection working (opt-in per recipe)
3. US3 → aborts are recoverable and detectable by a scheduler
4. US5 → quality trends in the observability stack, liveness alarm fixed
5. US4 → diagnosis polish

### Notes

- Protection is **opt-in**: a site that never sets `max_render_error_pct` gains better counters and metrics but no abort (research.md Finding 8). This is deliberate — see spec.md Assumptions on backward compatibility
- Commit after each task or logical group; do not commit without asking
- Two existing assertions are load-bearing regression witnesses: `test_classes.py:100` (`== 1`) and `test_recipes.py:178` (`== 3`) must not change value
