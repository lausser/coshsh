# Specification Quality Checklist: Template Rendering Error Handling

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-07-20
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

Re-validated 2026-07-20 after the clarification session that resolved the
maximum-delta consistency question. Still 16/16, no regressions.

This closes the second of the two "areas the planning phase should confirm against
the code" recorded at the bottom of this file. The check was made: a malformed
maximum-delta value raises during recipe construction, and that exception is
swallowed by the generic handler that registers recipes, so the recipe is dropped
and the run continues without it. The two settings would therefore have behaved
oppositely on the same class of typo. FR-016a and FR-016b were added to make the
refusal uniform and to require the rule be expressed once rather than per setting.

Checklist items re-examined for this change:

- **"No implementation details"** held — FR-016a/b describe *which settings* are
  covered and that the rule is stated once, without naming the exception type, the
  parsing call, or the module. The Assumptions entry describes the observable
  change at affected sites, not the code path.
- **"Requirements are testable"** held — FR-016a is directly testable (malformed
  maximum-delta value → run refuses to start, no recipe processed), and FR-016b is
  observable as behaviour: a newly added run-safety setting refuses the run on a
  bad value without its own validation code.
- **"Scope is clearly bounded"** re-checked and still passing, though scope did
  grow: this feature now also corrects an existing setting it did not previously
  touch. The growth is bounded to validation of run-safety settings and is
  recorded in Assumptions as a deliberate in-scope behaviour change.

---

Re-validated 2026-07-20 after the clarification session (5 questions answered).
All 16 items still pass — 16/16 before, 16/16 after, no regressions.

Clarification-driven changes re-checked:

- **Testability held** — the five answers each landed as concrete requirements
  (FR-001a/b/c, FR-002a, FR-014a, FR-016) rather than prose, and each has a
  matching acceptance scenario or edge case.
- **One deliberate, bounded exception to "no implementation details"**: the
  Assumptions section names the existing test
  `test_dest.DatarecipientTest.test_create_recipe_fallback_datarecipient_write`
  as evidence that the missing-template path is already reachable today. This is
  cited as verified evidence for a behaviour-change assumption, not as a design
  instruction. Judged worth keeping; remove it if the spec is circulated to
  non-technical stakeholders.
- **Acceptance-scenario numbering repaired** — an interim `1a.` item would not
  have rendered as a list entry; User Story 1's scenarios are now 1-4.

---

Re-validated 2026-07-20 after relaxing the staleness requirement. Still 16/16.
FR-017e was weakened from "always export explicit zeros" to "export on aborted
runs; staleness tolerated otherwise", on the operator's stated alerting model
(age of the success signal is the liveness alarm). SC-009 narrowed to match. The
resulting coupling — FR-017e is only safe while FR-017g holds — is recorded in
Assumptions so it cannot be split across releases unnoticed.

---

Re-validated 2026-07-20 after adding User Story 5 (observability). Still 16/16.
The new requirements (FR-017a…g, SC-008…010) are stated as exported signals and
their meanings, not as metric names or client-library calls, keeping the
"no implementation details" item intact.

---

Initial validation performed 2026-07-20, single iteration, all items pass.

Issues found and corrected during validation:

1. **Implementation leakage** — the source notes this spec draws on
   (`TEMPLATE-ERRORS.md` in the repo root) name concrete identifiers
   (`max_render_error_pct`, `render_attempts`, `too_many_render_errors()`,
   `Item.render_cfg_template`, Jinja2, file paths and line numbers). All were
   kept out of the spec; requirements refer to "an optional per-recipe
   configuration setting" and "the proportion of failed renderings" instead.
   `TEMPLATE-ERRORS.md` remains a useful design input for `/speckit-plan`.

2. **Precision requirement stated behaviourally** — FR-006 expresses the
   no-rounding rule as an observable outcome ("MUST evaluate the comparison
   without rounding that could mask a very small non-zero proportion") rather
   than as float-arithmetic guidance; SC-002 makes it measurable.

3. **Scope boundary made explicit** — the original design notes declared the
   missing-template accounting gap out of scope. The feature request explicitly
   names missing templates, so it is in scope here and is promoted to User
   Story 1 (P1), with the resulting behaviour change called out in Assumptions.

Areas the planning phase should confirm against the code (not spec defects,
but verification points):

- FR-017 (metric still emitted on abort) interacts with existing run-loop
  structure; confirm the metric push is not gated on successful completion.
- FR-016 (reject malformed tolerance values) has no existing precedent — the
  comparable `max_delta` setting's parsing behaviour on bad input should be
  checked so the two settings behave consistently.
