# Feature Specification: Template Rendering Error Handling

**Feature Branch**: `007-template-render-errors`

**Created**: 2026-07-20

**Status**: Draft

**Input**: User description: "handling of errors in tpl rendering (faulty and missing tpls)"

## Clarifications

### Session 2026-07-20

- Q: A template rule fires but its template file is absent from the templates path — is that always an error? → A: Error by default, with a per-recipe opt-out available for sites that depend on the current silent-skip behaviour.
- Q: How should "missing template" and "template raised during render" relate for the abort decision? → A: Counted and reported separately, but a single combined tolerance drives the abort. Additionally, a flag must be able to declare missing templates tolerated, in which case only errors arising during rendering count.
- Q: When the "missing templates are tolerated" flag is set, how do those tolerated attempts affect the percentage? → A: Excluded from both the failure count and the attempt count, so the percentage means "of the renderings held to account, what fraction failed". Still counted and reported separately for diagnostics.
- Q: Should an aborted recipe change the coshsh-cook process exit code? → A: Yes — a distinct non-zero exit code, separate from the existing startup codes.
- Q: What happens when a recipe declares a tolerance value that is not a valid percentage? → A: Refuse to start the run at all. It is a config-file syntax error, and a recipe must never be silently skipped, because every object it processes would then be absent from the final output.
- Q: The success-timestamp metric currently advances even when a run generated nothing. Fix it as part of this feature? → A: Yes, fix it here — it must advance only for runs that actually published output.
- Q: Must every render-related metric be refreshed on every run to avoid stale values? → A: No. Monitoring alarms on `(now - last_success) > threshold`, so stale values in the other metrics between successful runs are tolerable. Aborted runs must still export accurate counts.
- Q: A malformed value in the pre-existing maximum-delta setting currently causes
  that one recipe to be dropped from the run while the others proceed. Should this
  feature correct that too, so both run-safety settings react the same way to the
  same class of typo? → A: Yes. Both must refuse the run. Express the check once as
  a shared config-syntax rule rather than per-setting parsing, so that settings
  added later inherit the same behaviour by default.
- Q: How many failure categories are counted? → A: Two. A render error (template syntax error, Python error, or missing attribute) and a missing-template error count equally by default; both are "template errors". Finer distinctions stay in the log messages only. Missing templates keep their existing log output, are always counted, and are excluded from the percentage only when the tolerate flag is set.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A missing template is counted as a failure (Priority: P1)

A monitoring engineer adds a new application class whose template rule points at a
template file that does not exist (typo in the name, template pack not deployed,
file not yet written). Today the run reports this only as a log line and finishes
"successfully" — the affected services are silently absent from the generated
configuration. The engineer needs a missing template to be treated as exactly the
same class of failure as a broken template: counted, reported, and eligible to
stop the run.

**Why this priority**: This is the silent-failure case with the worst consequence.
A broken template at least produces a loud `critical` log entry; a missing template
produces a lower-severity line and is excluded from every failure count and every
downstream signal (summary line, metrics). Monitoring simply disappears for the
affected objects and nothing indicates a problem. Fixing the accounting is a
prerequisite for every other story here — no threshold policy can work while a
whole error category is invisible to it.

**Independent Test**: Run a recipe whose template rule references a non-existent
template and observe that the run's reported failure count includes it and the
severity of the report matches that of a syntactically broken template. Delivers
value on its own: operators can alert on the existing failure count and will,
for the first time, see missing templates in it.

**Acceptance Scenarios**:

1. **Given** a recipe with one template rule pointing at a template file that does
   not exist, **When** the recipe runs, **Then** the run's total failure count
   includes that missing template, and the report identifies the template by name
   and the object it was being rendered for.
2. **Given** the same recipe with missing templates declared tolerated, **When**
   the recipe runs, **Then** the missing template is reported but does not count
   as a failure, and neither the failure nor its attempt enters the proportion
   used for the abort decision.
3. **Given** a recipe where the same missing template is referenced by 500 objects,
   **When** the recipe runs, **Then** the reported failure count and the reported
   attempt count both reflect all 500 affected renderings, not a single
   deduplicated entry.
4. **Given** a recipe where all templates exist and render cleanly, **When** the
   recipe runs, **Then** the failure count is zero and behaviour is unchanged from
   today.

---

### User Story 2 - Abort the run when too many renderings fail (Priority: P1)

An operator maintains a recipe that generates tens of thousands of service
definitions. A change to a shared template breaks it. Today the run proceeds:
old output is cleared and new output is written, minus everything the broken
template would have produced — monitoring silently degrades in production. The
operator needs a way to declare "if more than X% of renderings fail, do not
publish this run at all; leave the last known-good configuration in place."

**Why this priority**: This is the requested behaviour with direct production
impact. Silent partial publication of a monitoring configuration is worse than
publishing nothing, because the gap is invisible until an incident goes
unnoticed. It ranks alongside Story 1 because the two together form the minimum
viable protection; Story 1 makes the signal complete, Story 2 acts on it.

**Independent Test**: Configure a recipe with a deliberately broken template and a
zero-tolerance threshold, run it, and verify that no output files were written or
removed and the previous run's output is byte-for-byte intact.

**Acceptance Scenarios**:

1. **Given** a recipe configured with a zero-tolerance failure threshold and one
   failing rendering out of one million attempts, **When** the recipe runs,
   **Then** the run aborts before publishing and the abort is reported with the
   failure count, the attempt count, the resulting percentage, and the configured
   threshold.
2. **Given** an aborted run and a directory containing output from a previous
   successful run, **When** the run aborts, **Then** the previous output is left
   completely untouched — nothing added, changed, or deleted.
3. **Given** a recipe with a 5% threshold and 2% of renderings failing, **When**
   the recipe runs, **Then** the run publishes normally and the failures are
   reported as problems, exactly as today.
4. **Given** a recipe with no threshold configured, **When** renderings fail,
   **Then** behaviour is identical to today: failures are reported, output is
   still published for everything that succeeded.
5. **Given** a recipe that collects no objects and therefore attempts zero
   renderings, **When** the recipe runs with a zero-tolerance threshold,
   **Then** the run does not abort and no arithmetic error occurs.

---

### User Story 3 - An aborted run leaves the system ready for the next attempt (Priority: P2)

Recipes run unattended on a schedule. When a run aborts because of template
failures, the next scheduled run must be able to start normally once the operator
has fixed the template — the abort must not leave behind a lock, a partial write,
or any other state that blocks recovery.

**Why this priority**: Without this, the safety mechanism from Story 2 turns one
bad run into an outage of the whole generation pipeline. It is P2 rather than P1
only because it is a property of the abort path rather than a separately valuable
capability — it has no standalone value if Story 2 does not exist.

**Independent Test**: Trigger an abort, then immediately run the same recipe again
with the template fixed, and verify it completes and publishes normally with no
manual cleanup.

**Acceptance Scenarios**:

1. **Given** a run that aborted due to template failures, **When** the same recipe
   is started again, **Then** it starts normally without any manual cleanup step.
2. **Given** a run that aborted, **When** the run finishes, **Then** it is not
   reported as a successful completion, and any external health signal the recipe
   emits reflects failure rather than success.
3. **Given** a cookbook containing several recipes and one of them aborting,
   **When** the run proceeds, **Then** the other recipes are processed normally
   and independently.

---

### User Story 4 - Diagnose which templates failed and why (Priority: P3)

After a run reports failures — or aborts — the engineer needs to find the cause
quickly: which template, which object, and what kind of failure (missing file,
syntax error, or an error raised while rendering).

**Why this priority**: The information needed to diagnose is largely reported
today; this story is about keeping the individual failure messages distinct even
though only two categories are counted, including the newly counted
missing-template case. It is a usability improvement on top of working detection,
not a prerequisite.

**Independent Test**: Run a recipe with one missing template, one syntactically
broken template, and one template that fails while rendering, then confirm all
three are individually identifiable in the run report even though the latter two
share a counter.

**Acceptance Scenarios**:

1. **Given** a run containing a missing template, a syntactically broken template,
   and a template that raises while rendering, **When** the run completes, **Then**
   each failure is reported individually with its own message, naming the template
   and distinguishing a missing template from a render error.
2. **Given** a rendering failure that affects a specific host or application,
   **When** the failure is reported, **Then** the report identifies which object
   was being rendered.
3. **Given** a completed run, **When** the summary is reported, **Then** it states
   both the number of failed renderings and the number attempted, so the
   proportion is apparent without reading every individual failure.

---

---

### User Story 5 - Track generation quality over time in observability (Priority: P2)

An operator running coshsh on a schedule wants the health of generation itself to
be visible in the observability stack alongside everything else they monitor: how
many templates are missing, how many failed to render, how many renderings were
attempted, and whether the last run published or aborted. Raw counts — not just a
pass/fail — let them see quality trends, spot a template pack degrading over
weeks, and alert before a threshold is ever crossed.

**Why this priority**: The counters exist to make the abort decision; exporting
them costs little and turns a binary safety mechanism into a continuous quality
signal. It is P2 rather than P1 because the abort protection works without it,
but it is what makes the feature useful on the days nothing aborts.

**Independent Test**: Run a recipe with a mix of missing and faulty templates and
confirm the exported metrics report each category's raw count, the attempt count,
and the run's outcome — sufficient to compute the failure rate externally without
re-deriving it from logs.

**Acceptance Scenarios**:

1. **Given** a run with missing and faulty templates, **When** the run finishes,
   **Then** the exported metrics carry the raw missing-template count and the raw
   render-error count, not only a combined total.
2. **Given** a run, **When** metrics are exported, **Then** the number of
   rendering attempts is exported alongside the failure counts, so the failure
   rate is computable externally.
3. **Given** a recipe with missing templates declared tolerated, **When** the run
   finishes, **Then** the tolerated missing templates are still exported as their
   own count, distinct from the failures that count toward the tolerance.
4. **Given** a run that aborted, **When** metrics are exported, **Then** the abort
   is exported as its own signal and the run is not reported as a success.
5. **Given** a run that failed before rendering began and therefore left stale
   render-related values in place, **When** an operator alarms on the age of the
   success signal, **Then** the failure is detected regardless of what those
   stale values show.
6. **Given** an existing dashboard or alert built on the metric that reports total
   render errors today, **When** this feature ships, **Then** that metric keeps
   its current name and meaning and the dashboard continues to work.
7. **Given** a recipe that has been failing to generate for several runs, **When**
   an operator alerts on how long ago the recipe last succeeded, **Then** the
   alert fires — the success signal has not advanced since the last run that
   actually published output.

---

### Edge Cases

- **Zero renderings attempted**: a recipe that collects no objects, or whose
  objects match no template rules, must not abort and must not produce a
  division error.
- **One failure among an enormous number of successes**: with a zero-tolerance
  threshold, a single failure out of a million or a billion attempts must abort.
  The proportion must be evaluated at full precision; any rounding applied for
  display must not influence the decision.
- **A single template missing but referenced by every object**: the failure
  proportion approaches 100% and must abort under any threshold below that.
- **All templates missing**: the recipe must abort (when a threshold is set) or
  publish an empty-but-consistent result (when none is set) — never a partial
  wipe followed by a partial write.
- **A template that renders successfully for most objects and fails for a few**
  (e.g. an object missing an attribute the template dereferences): counted
  per rendering attempt, not per template.
- **Threshold set to exactly 100**: never aborts, however many renderings fail —
  100% is the highest proportion reachable, and the comparison is a strict
  "greater than". A threshold *above* 100 is not a permissive setting but a
  config-file syntax error, handled like any other malformed threshold below.
- **Malformed threshold value in configuration**: the whole run must refuse to
  start, reporting the misconfiguration rather than silently treating it as "no
  threshold" or quietly dropping the offending recipe.
- **Malformed value in any other run-safety setting**: same outcome. A recipe
  whose maximum-delta setting cannot be interpreted must stop the run rather than
  being dropped from it, which is what happens today.
- **Every rendering tolerated as missing**: when the tolerate flag is set and no
  rendering remains to be held to account, the attempt count is zero and the run
  must not abort — the same zero-attempts rule applies.
- **Tolerate flag set but failures are faulty templates, not missing ones**: the
  flag must not suppress those; they still count and can still trigger an abort.
- **A failure raised while evaluating whether a template rule applies** (before
  any template is loaded): already counted today as a failure; must remain
  counted and must be included in the proportion.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST, by default, count a rendering that could not be
  produced because its template file was not found as a rendering failure, equal
  in weight to a rendering that failed because the template was faulty.
- **FR-001a**: The system MUST provide a per-recipe setting that declares missing
  templates tolerated. When set, a rendering skipped because its template was not
  found MUST NOT be treated as a failure, and only failures arising from faulty
  templates and from errors raised during rendering count toward the tolerance.
- **FR-001b**: A rendering tolerated under FR-001a MUST be excluded from both the
  failure count and the attempt count used to compute the proportion, so that the
  proportion expresses the fraction of failures among the renderings actually held
  to account.
- **FR-001c**: A rendering tolerated under FR-001a MUST still be counted and
  reported separately, so operators retain visibility into how many templates are
  missing even when their absence is tolerated.
- **FR-002**: The system MUST count the total number of rendering attempts made
  during a run, incrementing once per attempt regardless of the attempt's outcome,
  except for attempts excluded under FR-001b.
- **FR-002a**: The system MUST recognise exactly two counted categories: a
  **missing-template error** (the template file was not found) and a **render
  error** (a syntax error in the template, a Python error, or a missing attribute
  encountered while rendering). Together they form the **template errors** that
  drive the abort decision. Finer distinctions within render errors remain visible
  in the log messages but are not counted separately.
- **FR-003**: The system MUST compute the proportion of failed renderings relative
  to the renderings attempted in the same run, and MUST NOT use any measure
  derived from a previous run's results for this purpose.
- **FR-004**: The system MUST support an optional per-recipe configuration setting
  that expresses the maximum tolerated percentage of failed renderings. A valid
  value is a number from 0 to 100 inclusive; anything outside that range is not a
  percentage and MUST be rejected under FR-016.
- **FR-005**: The system MUST abort a recipe run — publishing nothing — when the
  proportion of failed renderings exceeds the configured maximum.
- **FR-006**: The system MUST treat a configured maximum of zero as "abort if any
  rendering fails", regardless of how many renderings succeeded, and MUST evaluate
  the comparison without rounding that could mask a very small non-zero proportion.
- **FR-007**: The system MUST preserve current behaviour when no maximum is
  configured: failures are reported and the run publishes output for everything
  that rendered successfully.
- **FR-008**: The system MUST leave any previously published output completely
  unmodified when a run aborts — no deletion, no partial write, no reordering.
- **FR-009**: The system MUST NOT report an aborted run as a successful completion.
- **FR-010**: The system MUST release any run-exclusivity lock it acquired when a
  run aborts, so that the next scheduled run of the same recipe can start.
- **FR-011**: The system MUST report an abort with enough detail to act on it: the
  number of failures, the number of attempts, the resulting proportion, and the
  configured maximum.
- **FR-012**: The system MUST report each individual rendering failure with the
  template's name, the object being rendered where one applies, and an indication
  of whether the template was missing or faulty.
- **FR-013**: The system MUST report, at the end of every run, both the number of
  failed renderings and the number attempted.
- **FR-014**: The system MUST continue processing the remaining recipes in a
  cookbook when one recipe aborts. This is safe because an aborted recipe leaves
  its previously published output in place, so no object disappears from the
  final result.
- **FR-014a**: The system MUST terminate with a distinct non-zero exit code,
  separate from the codes already used for startup failures, when any recipe
  aborted during the run, so that unattended schedulers detect the condition
  without depending on log parsing or metrics.
- **FR-015**: The system MUST tolerate a run in which zero renderings were
  attempted, treating the failure proportion as zero and not aborting.
- **FR-016**: The system MUST refuse to start the run at all when any recipe
  declares a maximum-failure setting that cannot be interpreted as a valid
  percentage, reporting the misconfiguration before any recipe is processed. It
  MUST NOT skip only the offending recipe and proceed with the others, because a
  skipped recipe leaves every object it would have processed absent from the
  final output.
- **FR-016a**: The refusal in FR-016 MUST apply to every run-safety setting a
  recipe declares, not only the new maximum-failure one. This corrects existing
  behaviour: a malformed value in the pre-existing maximum-delta setting currently
  causes that single recipe to be dropped from the run while the others proceed —
  exactly the silent, whole-recipe loss of output that FR-016 exists to prevent.
- **FR-016b**: The rule that decides whether a run-safety setting's value is
  acceptable MUST be expressed once and applied uniformly to those settings,
  rather than as separate ad-hoc parsing per setting, so that a setting added
  later inherits the refuse-the-run behaviour by default instead of having to
  re-implement it.
- **FR-017**: The system MUST continue to expose the failure count through the
  existing operational metrics channel, including on runs that abort, so external
  alerting keeps working.
- **FR-017a**: The system MUST export the raw count of missing templates and the
  raw count of render errors as quality signals in their own right, independent of
  whether any tolerance is configured and independent of whether missing templates
  are tolerated.
- **FR-017b**: The system MUST export the number of rendering attempts, so that
  the failure rate can be computed by the observability system without re-deriving
  it from logs.
- **FR-017c**: The system MUST export the count of missing templates that were
  tolerated under FR-001a as a distinct signal, separate from the failures that
  count toward the tolerance.
- **FR-017d**: The system MUST export whether the run aborted, as a signal
  distinct from the failure counts.
- **FR-017e**: The system MUST export the render-related metrics on runs that
  aborted, since those are precisely the runs whose counts an operator needs. For
  runs that failed before rendering began, the render-related metrics MAY be
  omitted, leaving the previous run's values in place. Staleness is acceptable
  there because the success-freshness signal (FR-017g) is the authoritative
  liveness alarm and will age regardless of what the other metrics show.
- **FR-017f**: The system MUST preserve the name and meaning of the metric that
  reports the total number of render errors today, so existing dashboards and
  alerts continue to function. New breakdowns MUST be additive.
- **FR-017g**: The system MUST NOT report a run as successful in the metrics when
  that run aborted or did not publish output. Operators alarm on the age of this
  signal, which makes it the authoritative indication that generation has stopped
  working — every other metric is diagnostic detail read after that alarm fires.
  This corrects existing behaviour:
  the success-timestamp signal is currently updated on every run that acquires the
  run lock, including runs that generated nothing, which makes freshness alerting
  on it impossible. After this change the signal MUST advance only for runs that
  actually published output.
- **FR-018**: The new configuration setting MUST be documented alongside the
  existing recipe settings that govern run-safety thresholds.

### Key Entities

- **Rendering attempt**: one application of one template to one object during one
  run. It is the unit of both counting and failure. An attempt is made whenever a
  template rule is determined to apply to an object.
- **Template error**: a rendering attempt that did not produce output. Exactly two
  counted kinds, weighted equally by default:
  - **Missing-template error** — the template file was not found.
  - **Render error** — a syntax error in the template, a Python error, or a
    missing attribute encountered while rendering against a specific object.

  Only the missing-template kind can be optionally excluded from the percentage.
- **Failure tolerance**: an optional per-recipe percentage stating the highest
  proportion of failed rendering attempts that may still be published. Absent
  means unlimited. Zero means none. A single tolerance covers all failure
  categories combined.
- **Missing-template tolerance flag**: an optional per-recipe switch declaring
  that templates absent from the path are acceptable. When set, those renderings
  leave the tolerance calculation entirely — neither failure nor attempt — while
  remaining separately reported.
- **Run outcome**: whether a recipe published its output, and whether it is
  reported as successful. An aborted run publishes nothing and is not successful.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of rendering failures caused by a missing template appear in
  the run's reported failure count (today: 0%), unless the recipe declares missing
  templates tolerated, in which case 100% of them appear in the separate
  missing-template report and 0% in the failure count.
- **SC-001a**: An aborted run is detectable by a scheduler from the process exit
  code alone, with no log parsing and no metrics backend.
- **SC-002**: A recipe configured for zero tolerance with exactly one failed
  rendering among one million successful ones aborts every time, across repeated
  runs.
- **SC-003**: After an aborted run, the previously published configuration is
  byte-for-byte identical to what it was before the run started.
- **SC-004**: After an aborted run, the next run of the same recipe starts without
  any manual intervention, in 100% of cases.
- **SC-005**: Recipes with no failure tolerance configured produce byte-for-byte
  identical output to the current version, for the full existing test corpus.
- **SC-006**: An operator can identify the specific template and object behind any
  reported failure from the run report alone, without re-running with additional
  diagnostics enabled.
- **SC-007**: Generation throughput is unchanged within measurement noise — the
  existing 60,000-services-in-10-seconds benchmark still passes.
- **SC-008**: An operator can compute the template error rate for any recipe, and
  see how much of it is missing templates versus render errors, entirely from
  exported metrics — without reading a single log line.
- **SC-009**: An aborted run's exported failure counts reflect that run, not the
  previous one.
- **SC-010**: Every dashboard or alert built on the render-error metric that works
  today still works after this feature ships, with no query changes.
- **SC-011**: A recipe that has not published output for N runs is detectable by
  an age check on the success signal alone — a check that cannot fire at all
  today.

## Assumptions

- **Backward compatibility is the default.** Recipes that do not configure a
  failure tolerance behave exactly as they do today. This is deliberate: coshsh
  runs unattended in production at many sites, and silently turning previously
  succeeding runs into aborts would be a breaking change.
- **Counting missing templates as failures is a behaviour change and is intended.**
  It affects the reported failure count and the operational metric derived from it
  for recipes that already have missing templates. This is confirmed to occur in
  the existing test corpus: `test_dest.DatarecipientTest.test_create_recipe_fallback_datarecipient_write`
  reaches the missing-template path today and counts nothing, because its recipe
  declares no templates directory while an unconditional template rule fires. The
  per-recipe tolerate flag (FR-001a) exists precisely so sites relying on the
  current silent skip can keep it.
- **Absence of a template file is not a supported way to express "optional".**
  Template rules already carry conditions for that purpose; a rule that fires with
  no template on the path is a misconfiguration by default. The tolerate flag is a
  compatibility escape hatch, not an endorsement of the pattern.
- **Tightening validation of the existing maximum-delta setting is a deliberate
  in-scope behaviour change.** A site whose cookbook already carries a malformed
  value there is silently losing that recipe's entire output on every run today
  and has no signal telling it so. After this change the run refuses to start and
  names the setting. This will look like a new failure at such sites; it is an old
  one becoming visible. It is included here rather than deferred because shipping
  FR-016 without it would leave two neighbouring settings in the same cookbook
  section reacting oppositely to the same typo.
- **A config-syntax error and a render abort are deliberately handled
  differently.** A malformed threshold stops the whole run before anything is
  processed, because a silently skipped recipe would leave all of its objects
  absent from the final output. A render abort is per-recipe and safe by contrast,
  because that recipe's previously published output stays on disk.
- **Abort granularity is the whole recipe.** Publishing partial output while
  skipping only the objects whose renderings failed is out of scope; the safe
  failure mode is to publish nothing and preserve the last good state.
- **A percentage is the right measure**, not an absolute failure count. It stays
  meaningful across recipes of very different sizes, and the "even one failure"
  policy remains fully expressible by setting the tolerance to zero.
- **Abort is the only response.** Other reactions to exceeding the tolerance
  (reverting a version-controlled output directory, notifying an external system)
  are out of scope and can be layered on later without changing how failures are
  detected or counted.
- **Existing failure reporting is adequate in form**; this feature makes it
  complete and consistent rather than redesigning it.
- **The error counters are a quality signal, not only an abort input.** They are
  exported regardless of whether any tolerance is configured, because their value
  to an observability system is in the trend, not only in the moment a threshold
  trips.
- **The existing metrics export replaces only the metrics present in a given
  push**; metrics absent from a push keep their previous value indefinitely. This
  is verified behaviour of the export mechanism in use. It is accepted rather than
  worked around: operators alarm on the age of the success signal, so a run that
  never rendered is caught by that alarm even while the render metrics still show
  the last good run's values.
- **The liveness alarm and the success-signal fix are one unit.** Tolerating stale
  render metrics (FR-017e) is only safe because the success signal ages correctly
  (FR-017g). If the success-signal correction were dropped or deferred, stale
  metrics would become genuinely dangerous — nothing would be aging, and a broken
  recipe could look healthy indefinitely. These two must ship together.
- **Metric names are a public interface**, subject to the same backward
  compatibility expectations as generated output format. Breakdowns are added
  as new signals rather than by changing an existing one.
- **Correcting the success signal is a deliberate in-scope behaviour change.**
  It currently advances on every run that acquires the run lock, so it reports
  success for runs that generated nothing. Sites that (incorrectly) see it as
  always-fresh today may start seeing it age — which is the point. It is included
  here rather than deferred because this feature adds an abort path that would
  otherwise make the signal wrong more often.
- The change is confined to the coshsh core generation flow; no datasource,
  data-recipient, template pack, or user-supplied class file needs modification.
