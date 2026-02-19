---
description: "Task list for 001-ai-handover-docs"
---

# Tasks: Comprehensive Status Quo Documentation for AI Agent Handover

**Input**: Design documents from `/specs/001-ai-handover-docs/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/ ✅

**Tests**: No automated test tasks — this is a pure documentation feature. Acceptance
is verified by the 8 measurable success criteria in spec.md. A baseline pytest run and
a final accuracy audit are included as verification checkpoints.

**Organization**: Tasks are grouped by user story. US1–US3 are P1 (must deliver first);
US4–US5 are P2 (deliver second). US3 (inline comments) can overlap with US1/US2 since
each file is independent.

---

## Phase 1: Setup

**Purpose**: Create the skeleton document and directory so all story phases can work
in parallel.

- [x] T001 Create `docs/` directory at repository root
- [x] T002 Create `docs/ai_handover.md` with complete table of contents and all
  section/subsection headings (skeleton only — no body content yet); headings MUST match
  the 17 sections + 3 appendices agreed in `specs/001-ai-handover-docs/contracts/doc-structure.md`
- [x] T003 [P] Run `pytest tests/ -q` to confirm the February 2026 baseline test suite
  passes with zero failures before any file changes are made; record result in a comment
  in `specs/001-ai-handover-docs/research.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the comment-style baseline and verify the skeleton before story
work begins.

**⚠️ CRITICAL**: All story-phase inline comment work (US3) depends on T004 establishing
the agreed pattern.

- [x] T004 Add module-level docstring to `coshsh/__init__.py` following the template in
  `specs/001-ai-handover-docs/contracts/comment-style.md` — this establishes the pattern
  for all subsequent comment tasks
- [x] T005 [P] Verify `docs/ai_handover.md` skeleton: confirm all 17 section headings and
  3 appendix headings are present and the ToC anchor links resolve correctly

**Checkpoint**: Skeleton ready — all user story documentation phases can now begin.

---

## Phase 3: User Story 1 — AI Agent First Contact (Priority: P1) 🎯 MVP

**Goal**: Deliver sections 1–4 and section 14 of `docs/ai_handover.md` so an AI agent
with no prior context can understand coshsh's purpose, architecture, all 18 modules, and
the plugin system.

**Independent Test**: An AI agent given only sections 1–4 and 14 must correctly describe
the four-phase pipeline, identify the correct module to modify for a datasource change,
and explain why the delta safety mechanism exists — all without consulting source files.

### Implementation for User Story 1

- [ ] T006 [US1] Write `docs/ai_handover.md` §1 (Project Purpose and Use Cases):
  §1.1 what coshsh does, §1.2 Nagios/Icinga use case, §1.3 OMD integration use case,
  §1.4 SNMP trap / check_logfiles use case, §1.5 known deployments and scale (60k+
  services); facts from `research.md` and `doc/coshsh.md`

- [ ] T007 [US1] Write `docs/ai_handover.md` §2 (Architecture Overview): §2.1 text
  component diagram, §2.2 the four-phase pipeline with method names
  (`recipe.collect()` → `recipe.assemble()` → `recipe.render()` → `recipe.output()`),
  §2.3 phase dependency chain (WHY order is non-negotiable), §2.4 the shared `recipe.objects`
  dictionary structure; add "See also: §3.2 recipe.py" cross-reference

- [ ] T008 [P] [US1] Write `docs/ai_handover.md` §3 subsections for orchestration layer:
  §3.1 `generator.py` (responsibility, Generator class, `read_cookbook`, `run`),
  §3.2 `recipe.py` (responsibility, Recipe class, four pipeline methods, pid protection,
  safe_output, vault resolution); include preconditions/postconditions per method;
  add "See also: §2.2, §9, §10" cross-references

- [ ] T009 [P] [US1] Write `docs/ai_handover.md` §3 subsections for data layer:
  §3.3 `datasource.py` (Datasource base class, `__ds_ident__`, open/read/close interface,
  exception types), §3.4 `datarecipient.py` (Datarecipient base class, output method,
  delta tracking, git integration), §3.5 `datainterface.py` (CoshshDatainterface,
  class factory mechanism, reversed iteration); add "See also: §4" cross-references

- [ ] T010 [P] [US1] Write `docs/ai_handover.md` §3 subsections for object layer:
  §3.6 `item.py` (Item base class, config_files structure keyed by tool, monitoring detail
  resolution, render method), §3.7 `host.py`, §3.8 `application.py` (class factory,
  GenericApplication), §3.9 `contact.py`, §3.10 `contactgroup.py`, §3.11 `hostgroup.py`;
  include fingerprint() return values for each

- [ ] T011 [P] [US1] Write `docs/ai_handover.md` §3 subsections for support layer:
  §3.12 `monitoringdetail.py`, §3.13 `templaterule.py` (all constructor parameters),
  §3.14 `vault.py`, §3.15 `configparser.py` (isa inheritance), §3.16 `jinja2_extensions.py`,
  §3.17 `dependency.py`, §3.18 `util.py` (compare_attr, substenv, sanitize_filename,
  odict); add cross-references to §4, §5, §6, §7 as appropriate

- [ ] T012 [US1] Write `docs/ai_handover.md` §4 (Plugin / Extension System):
  §4.1 class factory mechanism (`CoshshDatainterface.init_class_factory` and `get_class`),
  §4.2 class path search order and catchall mechanism (catchall appended to END = lowest
  priority), §4.3.1–§4.3.4 all four ident function conventions with signatures and
  examples, §4.4 class file naming prefixes (`datasource_*`, `app_*`, `os_*`, `detail_*`,
  `vault*`), §4.5 reversed iteration order (WHY: user classes beat defaults), §4.6 catchall
  directories; add "See also: §3.5, §12" cross-references

- [ ] T013 [US1] Write `docs/ai_handover.md` §14 (Edge Cases and Gotchas): all 8 edge
  cases from spec.md §Edge Cases — fingerprint collision, ident priority, catchall
  ordering, DatasourceNotAvailable handling, Jinja2 UndefinedError + render_errors,
  circular isa (unsupported), vault backend unreachable, max_delta with zero-baseline;
  each entry MUST include observed behaviour AND reason AND gotcha for callers

**Checkpoint**: US1 complete — sections 1, 2, 3, 4, 14 written. AI agent first-contact
scenario is independently testable.

---

## Phase 4: User Story 2 — AI Agent Plugin Authoring (Priority: P1)

**Goal**: Deliver sections 5, 6, 7, and 12 of `docs/ai_handover.md` so an AI agent
can author any plugin type from scratch using only the documentation.

**Independent Test**: An AI agent given only sections 4–7 and 12 must produce a correct,
runnable datasource plugin and application class plugin with zero corrections.

**Dependencies**: T012 (§4 Plugin System) must be complete before T017 (§12 Authoring
Guide) because §12 cross-references §4.

### Implementation for User Story 2

- [ ] T014 [P] [US2] Write `docs/ai_handover.md` §5 (MonitoringDetail Type Reference):
  all 19 types — for each: `monitoring_type` string value, `monitoring_0`…`monitoring_N`
  parameter mapping, resulting object attribute name and type (str/list/dict), and one
  example of how it is used in a Jinja2 template; source of truth is
  `recipes/default/classes/detail_*.py`

- [ ] T015 [P] [US2] Write `docs/ai_handover.md` §6 (INI Configuration File Reference):
  all 7 section types as Markdown tables with columns: Key | Type | Default | Effect;
  §6.8 three substitution patterns (%ENV_VAR%, @VAULT[key], @MAPPING_NAME[key]) with
  examples; §6.9 isa recipe inheritance with example; add "See also: §10" cross-reference

- [ ] T016 [P] [US2] Write `docs/ai_handover.md` §7 (Jinja2 Template System):
  §7.1 template discovery (FileSystemLoader + templates_path search order), §7.2 template
  caching mechanism, §7.3 all 8 built-in filters with signatures and examples, §7.4 built-in
  `re_match` test, §7.5 `environ` global, §7.6 custom extensions via `my_jinja2_extensions`
  key, §7.7 how `service` filter generates Nagios service definitions with NAGIOSCONF
  integration, §7.8 `.tpl` extension convention; add "See also: §5, §12.2" cross-references

- [ ] T017 [US2] Write `docs/ai_handover.md` §12 (Plugin Authoring Guide):
  **§12.1 Complete datasource example** — ident function, class with `open`/`read`/`close`,
  Host and Application creation, `self.add()`, corresponding recipe INI snippet;
  **§12.2 Complete application class example** — ident function with regex match, class
  with multiple TemplateRules including one conditional on a list-type MonitoringDetail,
  Jinja2 template snippet showing the `{% for %}` loop, recipe INI snippet;
  **§12.3 MonitoringDetail plugin** — scalar type example (LOGIN) and list type example
  (FILESYSTEM) showing property_type, property_attr, monitoring_N mapping;
  **§12.4 Vault plugin** — ident function, class with `open`/`read`; **§12.5 Custom
  Jinja2 extension** — filter and test registration; **§12.6 Full recipe INI with vault**
  — complete multi-datasource recipe with vault, mapping, and environment variable
  substitution; all code examples MUST be runnable against the Feb 2026 baseline

**Checkpoint**: US2 complete — sections 5, 6, 7, 12 written. Plugin authoring scenario
is independently testable.

---

## Phase 5: User Story 3 — AI Agent Code Comprehension via Inline Comments (Priority: P1)

**Goal**: Add module-level docstrings and `# WHY:` / `# NOTE:` inline comments to all 18
`coshsh/*.py` files following `specs/001-ai-handover-docs/contracts/comment-style.md`.

**Independent Test**: An AI agent reads any single commented source file and correctly
answers: (a) module responsibility, (b) why at least two non-obvious decisions were made,
(c) preconditions for each public method — without consulting any other document.

**Dependencies**: T004 must be complete (establishes the comment pattern).

**Note**: All T018–T035 are fully parallel — each touches a different file.

### Implementation for User Story 3

- [ ] T018 [P] [US3] Add module docstring + `# WHY:` comments to `coshsh/recipe.py`:
  must explain pid_protect purpose, safe_output guard, why assemble is separate from
  collect, vault resolution order, and the recipe.objects dict structure

- [ ] T019 [P] [US3] Add module docstring + `# WHY:` comments to `coshsh/generator.py`:
  must explain cookbook parsing, recipe ordering (odict), and why Generator delegates
  to Recipe rather than running the pipeline itself

- [ ] T020 [P] [US3] Add module docstring + `# WHY:` comments to `coshsh/datainterface.py`:
  MUST explain reversed class_factory iteration (WHY: user classes override defaults),
  dynamic importlib loading (WHY: plugin files are discovered at runtime), and what
  happens when two ident functions both match

- [ ] T021 [P] [US3] Add module docstring + `# WHY:` comments to `coshsh/datasource.py`:
  must explain DatasourceNotAvailable vs DatasourceNotCurrent vs DatasourceNotReady
  exception semantics, the hostname_transform_ops chain, and the objects dict structure

- [ ] T022 [P] [US3] Add module docstring + `# WHY:` comments to `coshsh/datarecipient.py`:
  must explain count_before/count_after delta tracking, positive vs negative max_delta
  semantics, safe_output git reset behaviour, and the for_tool routing mechanism

- [ ] T023 [P] [US3] Add module docstring + `# WHY:` comments to `coshsh/item.py`:
  must explain why config_files is keyed by tool name, what monitoring detail resolution
  does to object attributes, when unique_config naming applies, and the render_errors
  counter

- [ ] T024 [P] [US3] Add module docstring + `# WHY:` comments to `coshsh/application.py`:
  must explain the class factory redirect in __init__, GenericApplication fallback logic,
  and the fingerprint() composition (host_name + name + type)

- [ ] T025 [P] [US3] Add module docstring + `# WHY:` comments to `coshsh/host.py`:
  must explain attribute normalisation (lowercasing type/os/hardware etc.), the ports
  list default of [22], and the is_correct() validation

- [ ] T026 [P] [US3] Add module docstring + `# WHY:` comments to `coshsh/contact.py`:
  must explain the clean_name() umlaut stripping and the fingerprint composition
  (name + type + address + userid)

- [ ] T027 [P] [US3] Add module docstring + `# WHY:` comments to
  `coshsh/contactgroup.py`: must explain its relationship to Contact and when it
  is created during assemble

- [ ] T028 [P] [US3] Add module docstring + `# WHY:` comments to `coshsh/hostgroup.py`:
  must explain its relationship to Host and when it is created during assemble

- [ ] T029 [P] [US3] Add module docstring + `# WHY:` comments to
  `coshsh/monitoringdetail.py`: must explain the class factory pattern for detail types,
  property_type semantics (str/list/dict), property_attr flattening, unique_attribute
  deduplication, and WHY monitoring_0…N are used instead of named params

- [ ] T030 [P] [US3] Add module docstring + `# WHY:` comments to `coshsh/templaterule.py`:
  must explain every constructor parameter (needsattr, isattr, template, unique_attr,
  unique_config, suffix, self_name, for_tool) and the matching logic precedence

- [ ] T031 [P] [US3] Add module docstring + `# WHY:` comments to `coshsh/vault.py`:
  must explain vault plugin discovery, the @VAULT[key] substitution contract, and why
  vault resolution happens before datasource instantiation

- [ ] T032 [P] [US3] Add module docstring + `# WHY:` comments to `coshsh/configparser.py`:
  must explain the isa inheritance mechanism (one-level deep, no cycle detection), how
  %ENV_VAR% and @VAULT[key] tokens are handled at parse time vs resolve time

- [ ] T033 [P] [US3] Add module docstring + `# WHY:` comments to
  `coshsh/jinja2_extensions.py`: must explain the `service` filter Nagios output
  generation, the rfc3986 filter purpose, and how custom extensions are registered
  via my_jinja2_extensions

- [ ] T034 [P] [US3] Add module docstring + `# WHY:` comments to `coshsh/dependency.py`:
  must explain what this module models and when dependency objects are created

- [ ] T035 [P] [US3] Add module docstring + `# WHY:` comments to `coshsh/util.py`:
  must explain compare_attr regex semantics, substenv substitution pattern, the odict
  ordered dict and WHY it is needed (preserve recipe order), and sanitize_filename
  MD5-suffix logic

**Checkpoint**: US3 complete — all 18 source files have inline comments. AI code
comprehension scenario is independently testable.

---

## Phase 6: User Story 4 — New Human Maintainer Orientation (Priority: P2)

**Goal**: Deliver sections 8–11 and 15–17 and all appendices of `docs/ai_handover.md`
so a new human maintainer can understand the full system from a single document.

**Independent Test**: A human reading only the status quo document answers the five
standard architecture questions without opening any source file.

**Dependencies**: T007 (§2 architecture), T012 (§4 plugin system) must be complete.

### Implementation for User Story 4

- [ ] T036 [P] [US4] Write `docs/ai_handover.md` §8 (Output Directory Structure):
  `dynamic/` vs `static/` purpose, full directory tree with example paths
  (`dynamic/hosts/server-nr1/host.cfg`, `dynamic/hosts/server-nr1/os_windows_default.cfg`,
  `dynamic/hostgroups/hostgroup_customer_*.cfg`), file naming conventions and
  `sanitize_filename` MD5 suffix for special characters; add "See also: §9" cross-reference

- [ ] T037 [P] [US4] Write `docs/ai_handover.md` §9 (Delta / Cache Safety Mechanism):
  count_before/count_after flow, positive vs negative max_delta semantics with examples
  (e.g., max_delta = 10:20 vs max_delta = -10:-20), max_delta_action options (warn/error),
  safe_output git reset --hard + git clean -f -d, when to use safe_output in production;
  add "See also: §6.2" cross-reference

- [ ] T038 [P] [US4] Write `docs/ai_handover.md` §10 (Vault and Secrets Management)
  and §11 (Hostname Transformations): §10 covers all four substitution mechanisms with
  examples, built-in vault types (vault_pass, vault_naemon), recipe.substsecret; §11
  covers all 5 transform operations, configuration via hostname_transform key, execution
  order (left to right); add "See also: §6" cross-references

- [ ] T039 [P] [US4] Write `docs/ai_handover.md` §15 (Prometheus Pushgateway
  Integration), §16 (OMD Integration), §17 (SNMP Trap / check_logfiles): §15 metrics
  emitted + config; §16 OMD paths (%OMD_ROOT%), default recipe layout in OMD site,
  coshsh-cook invocation; §17 use case, datarecipient_prometheus_snmp pattern reference,
  testsnmptt test recipe as runnable reference; add cross-references to §6 and §8

- [ ] T040 [US4] Write `docs/ai_handover.md` Appendix A (All Config Keys quick-reference
  table), Appendix B (All MonitoringDetail Types quick-reference table with monitoring_type
  values and result attributes), Appendix C (Class Factory Decision Tree — text diagram
  showing ident function lookup flow); update ToC anchor links to appendices

**Checkpoint**: US4 complete — all 17 sections and 3 appendices written. Human maintainer
orientation scenario is independently testable.

---

## Phase 7: User Story 5 — AI Agent Test Authoring (Priority: P2)

**Goal**: Deliver §13 (Test Infrastructure Guide) so an AI agent can write a passing
pytest test without guidance.

**Independent Test**: An AI agent reading only §13 writes a pytest test for a new
datasource that correctly sets up a recipe, invokes the full pipeline, and asserts on
output files — and the test passes on first run.

**Dependencies**: T008 (§3.2 recipe.py) and T009 (§3.3 datasource.py) should be complete
for accurate cross-references.

### Implementation for User Story 5

- [ ] T041 [US5] Write `docs/ai_handover.md` §13 (Test Infrastructure Guide): §13.1
  CommonCoshshTest base class (what setUp/tearDown do, class factory reset between
  tests — WHY: prevents cross-test contamination), §13.2 test recipe fixture layout
  under `tests/recipes/<testNN>/` (cfg file, classes/, templates/), §13.3 setup and
  cleanup patterns (setUpConfig, setUpObjectsDir, tearDown), §13.4 asserting on generated
  files (os.path.exists, reading .cfg content), §13.5 testing a datasource plugin,
  §13.6 testing an application class plugin, §13.7 running the suite (`pytest tests/ -q`);
  §13.6 MUST include a complete, runnable test example that an AI agent can copy and
  adapt with zero changes to the pattern

**Checkpoint**: US5 complete — §13 written. AI test authoring scenario independently
testable.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Accuracy audit, cross-reference verification, and final consistency check.

- [ ] T042 [P] Factual accuracy audit of `docs/ai_handover.md`: for every class name,
  method signature, config key, and file path mentioned in the document, verify it
  matches the Feb 2026 baseline by grepping the actual source files; document any
  discrepancies found and fix them (satisfies SC-008)

- [ ] T043 [P] Documentation coverage count: for each of the 18 `coshsh/*.py` files,
  verify a module-level docstring exists (`grep -c '"""' coshsh/*.py`) and that at least
  one `# WHY:` comment is present; record count in a comment appended to
  `specs/001-ai-handover-docs/research.md` (satisfies SC-003/SC-004)

- [ ] T044 Run `pytest tests/ -q` after all inline comment additions to confirm no
  executable code was accidentally modified; all tests MUST pass (zero regressions)

- [ ] T045 [P] Verify all Markdown anchor links in `docs/ai_handover.md` ToC resolve
  correctly; verify all "See also:" cross-references point to sections that exist;
  fix any broken links

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001, T002) — BLOCKS US3 comment work
- **US1 (Phase 3)**: Depends on Foundational — all US1 tasks can then run in parallel
- **US2 (Phase 4)**: Depends on T012 (§4) for §12 cross-references; T014–T016 are parallel
- **US3 (Phase 5)**: Depends on T004 (comment pattern baseline); T018–T035 all parallel
- **US4 (Phase 6)**: Depends on T007 + T012 for cross-references; T036–T039 parallel
- **US5 (Phase 7)**: Depends on T008 + T009 for cross-references
- **Polish (Phase 8)**: Depends on ALL story phases being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational — no inter-story dependencies
- **US2 (P1)**: Can start after US1's T012 (§4) is complete (T017 needs §4 cross-refs)
- **US3 (P1)**: Can start after T004 — fully independent of US1/US2 document sections
- **US4 (P2)**: Can start after US1's T007 + T012 complete — otherwise independent
- **US5 (P2)**: Can start after US1's T008 + T009 complete — otherwise independent

### Within Each User Story

- Document sections: write in order (earlier sections define terms used in later ones)
- Inline comments (US3): fully parallel (T018–T035)
- Polish tasks: fully parallel once all stories complete

---

## Parallel Example: US3 (Inline Comments)

All 18 inline comment tasks can run simultaneously:

```text
T018: coshsh/recipe.py
T019: coshsh/generator.py
T020: coshsh/datainterface.py
T021: coshsh/datasource.py
T022: coshsh/datarecipient.py
T023: coshsh/item.py
T024: coshsh/application.py
T025: coshsh/host.py
T026: coshsh/contact.py
T027: coshsh/contactgroup.py
T028: coshsh/hostgroup.py
T029: coshsh/monitoringdetail.py
T030: coshsh/templaterule.py
T031: coshsh/vault.py
T032: coshsh/configparser.py
T033: coshsh/jinja2_extensions.py
T034: coshsh/dependency.py
T035: coshsh/util.py
```

## Parallel Example: US1 Document Sections

T008, T009, T010, T011 (module reference groups) can run in parallel after T007 (§2):

```text
T008: §3.1–§3.2 (orchestration layer: generator + recipe)
T009: §3.3–§3.5 (data layer: datasource, datarecipient, datainterface)
T010: §3.6–§3.11 (object layer: item, host, application, contact, groups)
T011: §3.12–§3.18 (support layer: detail, templaterule, vault, config, jinja2, dep, util)
```

---

## Implementation Strategy

### MVP First (US1 + US3)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T005)
3. Complete Phase 3: US1 (T006–T013) — architecture + module reference
4. Complete Phase 5: US3 (T018–T035) in parallel — inline comments
5. **STOP and VALIDATE**: AI agent first-contact + code comprehension scenarios testable

### Incremental Delivery

1. Setup + Foundational → skeleton ready
2. Add US1 (sections 1–4, 14) → AI architecture comprehension delivered (MVP!)
3. Add US2 (sections 5–7, 12) → plugin authoring delivered
4. Add US3 (inline comments) → code comprehension delivered (can overlap with US1+US2)
5. Add US4 (sections 8–11, 15–17, appendices) → human maintainer orientation delivered
6. Add US5 (section 13) → test authoring delivered
7. Polish → final accuracy audit

### Parallel Team Strategy

With multiple agents:

- **Agent A**: US1 sections (T006–T013)
- **Agent B**: US3 inline comments, batch 1 (T018–T026)
- **Agent C**: US3 inline comments, batch 2 (T027–T035)
- After Agent A completes T012+T015+T016: **Agent D** starts US2 (T014–T017)
- After US1 complete: **Agent E** starts US4 (T036–T040)

---

## Notes

- [P] tasks touch different files — safe to run simultaneously
- [USN] label maps each task to its user story for traceability
- All document section tasks reference the contracts in `specs/001-ai-handover-docs/contracts/`
- Inline comment tasks MUST NOT change any executable code — comments and docstrings only
- Every code example in §12 must be verified as runnable against the Feb 2026 baseline
- Cross-references (See also:) must use anchor link syntax: `[§X.Y](#xy-section-title)`
- Do NOT use omd.consol.de/docs/coshsh as a source (see research.md Decision 3)
