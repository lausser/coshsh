---
description: "Task list for Legacy Python (<3.8) Compatibility Layer"
---

# Tasks: Legacy Python (<3.8) Compatibility Layer

**Input**: Design documents from `/specs/006-legacy-python-compat/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/compat-activation.md ✅, quickstart.md ✅

**Tests**: The `tests/` suite stays **Python-version-agnostic** — it runs on whatever single interpreter the distro/CI provides (GitHub Actions exercises the matrix, one Python per run). Exactly **one new test file** is added, `tests/test_pycompat.py`, and it is `skipif`-gated to run **only on Python <3.8**: on modern interpreters it is skipped (the layer is inert there anyway), and on the legacy-Python CI job it actively exercises the compat module (addresses analysis finding C2). Beyond that, verification tasks run the existing suite in each story phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, US3 (maps to spec.md user stories)
- Exact file paths are included in every task

## Path Conventions

Single-project layout (unchanged). Repository root holds `coshsh/` (protected package), `bin/` (entry points), `tests/`. The compat module lives at the **repository root** (sibling to `coshsh/`) because it MUST run before `coshsh/__init__.py` is compiled.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the red baseline and confirm the protected-source constraint before writing any compat code.

- [X] T001 Capture the red baseline on the Python 3.6 target: from the package root run `TMPDIR=/tmp pytest-3 -p no:cacheprovider -q` and record the result (expected: 47 collection errors, 0 tests run, all rooted in `SyntaxError: future feature annotations` at `coshsh/__init__.py:40`) into `specs/006-legacy-python-compat/research.md` if not already present.
- [X] T002 Record the pre-feature baselines used by the SC checks: `git stash list`/clean tree, `git diff --stat coshsh/` (empty), and the current contents of `bin/coshsh-cook` and `bin/coshsh-create-template-tree` line 9 (the `from __future__ import annotations` to be replaced), so US2/US3 acceptance can diff against them.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the single compatibility module `coshsh_pycompat.py`. Every user story depends on it (bin scripts and conftest all `import coshsh_pycompat`).

**⚠️ CRITICAL**: No user story work can begin until `coshsh_pycompat.py` exists and imports cleanly on both Python 3.6 and ≥3.8.

> All Phase-2 tasks edit the **same file** (`coshsh_pycompat.py`), so they are sequential (no `[P]`), except T003 which creates it.

- [X] T003 Create `coshsh_pycompat.py` at the repository root with the module docstring and `WHY` header comments (compile-time-`SyntaxError` constraint, FR-006/FR-012) and the version gate `if sys.version_info < (3, 8): _install()` (FR-003 / contract C1). Above the gate the module must be a no-op on ≥3.8.
- [X] T004 In `coshsh_pycompat.py`, implement the AST annotation-stripper (`ast.NodeTransformer`): remove `from __future__ import annotations`; null `arg.annotation` and `FunctionDef.returns`; convert annotated assignments-with-value to plain assignments; drop annotation-only statements; repair emptied blocks with `pass` (FR-006, FR-007).
- [X] T005 In `coshsh_pycompat.py`, implement the strip loader as an `importlib.machinery.SourceFileLoader` subclass overriding `source_to_code()` to parse → transform (T004) → `compile()`; additionally **disable bytecode caching** for transformed modules (e.g. override `set_data()` to a no-op / `get_code()` to skip `.pyc` read+write) so no transformed `.pyc` is ever produced or a stale unshimmed `.pyc` loaded on <3.8 (FR-006 / contract C2 / byte-compiled-artefacts edge case).
- [X] T006 In `coshsh_pycompat.py`, implement the `coshsh`-scoped `importlib.abc.MetaPathFinder`: delegate to the default `PathFinder` for a spec and swap in the strip loader **only** when `fullname == "coshsh"` or `fullname.startswith("coshsh.")`; return `None` otherwise (FR-013 / contract C3).
- [X] T007 In `coshsh_pycompat.py`, implement the `typing.Protocol` / `typing.runtime_checkable` no-op shim, injected only if absent, so `class IdentFunction(Protocol)` in `coshsh/datainterface.py` loads on 3.6/3.7 (FR-008 / contract C4).
- [X] T008 In `coshsh_pycompat.py`, implement the `subprocess.run(capture_output=...)` → `stdout=PIPE, stderr=PIPE` translation shim for Python <3.7 (used by `tests/test_delta.py`) (FR-008 / contract C4).
- [X] T009 In `coshsh_pycompat.py`, wire `_install()` to add the finder to `sys.meta_path` and apply the shims **idempotently** (finder added at most once; shims guarded by `hasattr`/sentinel), scoped so nothing is installed on ≥3.8 (FR-010, FR-013 / contract C1).

**Checkpoint**: `python3 -c "import coshsh_pycompat"` succeeds on Python 3.6 (installs hooks) and on ≥3.8 (inert, no `sys.meta_path` change). Foundation ready.

---

## Phase 3: User Story 1 - Test suite passes on legacy Python (Priority: P1) 🎯 MVP

**Goal**: With the compat module present, running the project test runner from the package root on Python 3.6 completes with exit code 0, no version-incompatibility import/collection errors.

**Independent Test**: On the Python 3.6 CentOS 7 environment with `python36-pytest`/`python36-jinja2` installed, run `TMPDIR=/tmp pytest-3 -p no:cacheprovider -q` from the package root → exits 0 (only environment-specific skips permitted).

### Implementation for User Story 1

- [X] T010 [P] [US1] Create `tests/conftest.py` (NEW file): under `sys.version_info < (3, 8)`, insert the package root onto `sys.path` and `import coshsh_pycompat`, so the finder is active before pytest collects any coshsh-importing test module (FR-005, FR-010 / contract C1, C5).
- [X] T011 [P] [US1] Edit `bin/coshsh-cook`: replace its own line-9 `from __future__ import annotations` with a `sys.version_info < (3, 8)`-gated block that inserts the source root onto `sys.path` and imports `coshsh_pycompat`, placed above the first `import coshsh` (FR-005, FR-006 / contract C5).
- [X] T012 [P] [US1] Edit `bin/coshsh-create-template-tree`: apply the identical gated bootstrap replacement as T011 (FR-005 / contract C5).
- [X] T013 [P] [US1] Create `tests/test_pycompat.py` (NEW file): a **legacy-only** regression test for the compat module, gated with `pytestmark = pytest.mark.skipif(sys.version_info >= (3, 8), reason="compat layer is inert on Python >= 3.8")` so it is **skipped** on modern interpreters and only runs on the <3.8 CI matrix job. On a legacy interpreter it asserts: (a) `import coshsh` and a representative `coshsh.<submodule>` (e.g. `coshsh.datainterface`) import succeed despite the future-import + PEP 585/604 syntax; (b) `typing.Protocol` / `typing.runtime_checkable` are usable; (c) `subprocess.run(capture_output=True)` returns captured `stdout`/`stderr`; (d) the finder is **scoped** — a non-`coshsh` module is not intercepted/transformed (contract C3); (e) re-importing `coshsh_pycompat` is idempotent (finder present at most once). Keeps `tests/` single-version-agnostic (addresses analysis C2 / FR-002, FR-008, FR-009, FR-013 / contracts C1–C4).
- [X] T014 [US1] Run the full suite on Python 3.6 from the package root (`TMPDIR=/tmp pytest-3 -p no:cacheprovider -q`) and confirm exit 0 — this run now also executes `tests/test_pycompat.py` (T013); triage any residual failure against the research.md taxonomy to confirm it is an environment prerequisite (writable `/tmp` & `/var/tmp`, non-root user, optional deps, running pushgateway) and NOT a coshsh-source version incompatibility (FR-001, FR-002, FR-009 / SC-001).

**Checkpoint**: MVP reached — the headline goal (SC-001) is met and independently verifiable on the Python 3.6 target; the compat module has an automated regression guard on the legacy interpreter.

---

## Phase 4: User Story 2 - Modern Python behaviour and sources are unchanged (Priority: P1)

**Goal**: On Python ≥3.8 the feature is completely inert; `coshsh/` is byte-for-byte unchanged; suite results are identical with and without the layer.

**Independent Test**: On Python 3.12, run the suite with the feature present and confirm identical passed/failed/skipped counts vs. upstream (`tests/test_pycompat.py` shows as **skipped**, not failed); confirm the gate short-circuits; confirm `git diff coshsh/` is empty.

### Implementation / Verification for User Story 2

- [X] T015 [P] [US2] Verify inertness on modern Python: on a Python ≥3.8 interpreter run `python -c "import coshsh_pycompat, sys; assert sys.version_info >= (3,8); assert not any('coshsh_pycompat' in type(f).__module__ for f in sys.meta_path)"` (gate False → no finder installed, no `typing`/`subprocess` attributes added) (FR-003, FR-013 / SC-005 / contract C1).
- [X] T016 [P] [US2] Verify source immutability: run `git diff --stat coshsh/` and confirm zero changed files under `coshsh/` (byte-for-byte identical to pre-feature) (FR-004 / SC-003 / contract C6).
- [X] T017 [US2] Run the full existing suite on Python ≥3.8 (`pytest -q`) with the feature present and confirm passed/failed/skipped counts are identical to the pre-feature baseline captured in T002, with `tests/test_pycompat.py` counted as **1 skipped** (FR-009 / SC-002).

**Checkpoint**: Modern-Python behavior provably unchanged; US1 and US2 both hold simultaneously.

---

## Phase 5: User Story 3 - Additive, review-ready, upstreamable change (Priority: P2)

**Goal**: The change set is small, self-documenting, and confined to new files plus exactly the two permitted entry-point edits, ready to submit as a PR.

**Independent Test**: A reviewer reading the added files and the two bin diffs can, in one pass, enumerate the incompatibilities addressed and confirm the interpreter-version gate.

### Implementation for User Story 3

- [X] T018 [P] [US3] Audit `coshsh_pycompat.py` for self-documentation (FR-012 / SC-006): confirm each shim (future-import strip, PEP 585/604 annotation strip, `typing.Protocol`, `subprocess.run`) carries a `WHY` comment naming the incompatibility and the Python version it targets, and that the `< (3, 8)` gate is explicit at the top.
- [X] T019 [P] [US3] Confirm the edited pre-existing file set is EXACTLY `{bin/coshsh-cook, bin/coshsh-create-template-tree}` and everything else is NEW (`coshsh_pycompat.py`, `tests/conftest.py`, `tests/test_pycompat.py`): run `git status --porcelain` / `git diff --name-only` and check no other tracked file is modified (FR-005, FR-011 / SC-004 / contract C6).
- [X] T020 [US3] Confirm the change set is self-contained for a PR (FR-011): verify `coshsh_pycompat.py`, `tests/conftest.py`, and `tests/test_pycompat.py` reference nothing outside the tracked source tree, and that `setup.py` is untouched (still `python_requires='>=3.8'`).

**Checkpoint**: All three user stories independently satisfied; change is review-ready.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation.

- [X] T021 Run the full `specs/006-legacy-python-compat/quickstart.md` validation end-to-end on the Python 3.6 container (baseline → compat → provisioned env) and confirm the expected-outcomes table (47 errors → suite passes; empty `git diff coshsh/`; two edited files).
- [X] T022 [P] Update `README.python3` (or add a short note) documenting the legacy-Python source-tree run path (`pytest-3` / OMD packaging) and that `pip install` on <3.8 remains intentionally blocked by `python_requires='>=3.8'`.
- [X] T023 [P] Record any lessons/discovered pitfalls (e.g. `.pyc` staleness, import ordering) in `tasks/lessons.md`.
- [ ] T024 [P] Verify the broadened CI matrix in `.github/workflows/python-app.yml` (added 2026-07-03): the `build` job runs 3.8–3.13 via `actions/setup-python` (compat inert, `test_pycompat.py` skipped), and the `legacy` job runs 3.6/3.7 inside `python:<ver>-slim-bullseye` containers (compat active, `test_pycompat.py` executes). Decision: `setup-python` cannot install 3.6/3.7 on modern runners (GLIBC mismatch, both EOL) and `centos:7` breaks `actions/checkout@v4` (node20 needs GLIBC 2.28+; CentOS 7 has 2.17), so the Debian-based `python:3.6/3.7` images are the maintainable way to exercise the layer in CI. On the first real run, confirm the legacy job is green; tune provisioning (non-root user, writable `/var/tmp`, optional-dep/pushgateway skips) if any environment-sensitive test fails.
- [X] T025 Propagate to a reviewable diff (decided 2026-07-03): implementation + validation happen in the CentOS 7 podman playground `/packages/coshsh/coshsh-12.2.1.1`; environment failures there are fixed in the container directly (create missing dirs, `chmod` to writable, add a non-root run user, install optional deps / start pushgateway as needed — the container is disposable). Once `pytest-3` is green, create a local **feature branch** (`006-legacy-python-compat`) and copy the modified/new files from the container playground back to `/src/coshsh` (the mounted repo) so the maintainer can review a clean `git diff`. Version numbering is deferred — success is judged solely by the CentOS 7 suite passing; a `12.3` bump happens later, out of scope here.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup. **BLOCKS all user stories** — nothing imports without `coshsh_pycompat.py`.
- **User Stories (Phase 3–5)**: All depend on Foundational (Phase 2) completion.
  - US1 (P1) and US2 (P1) are independent of each other and can run in parallel once Phase 2 is done.
  - US3 (P2) verifies the artifacts produced by US1; its audit tasks are strongest after US1's files exist, but the review criteria are independent.
- **Polish (Phase 6)**: Depends on the desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Needs Phase 2. Produces `tests/conftest.py`, `tests/test_pycompat.py` + the two bin edits. Independently testable via the 3.6 suite run.
- **US2 (P1)**: Needs Phase 2. Pure verification of inertness/immutability on ≥3.8. Independent of US1.
- **US3 (P2)**: Needs Phase 2 (+ US1 files for the file-set audit). Review-readiness verification.

### Within Each Phase

- Phase 2 (T003→T009) is sequential — all edit the single file `coshsh_pycompat.py`.
- US1: T010/T011/T012/T013 are `[P]` (four different files — conftest, two bins, the compat test), then T014 runs the suite (depends on all four).
- US2: T015/T016 are `[P]`; T017 runs the suite.
- US3: T018/T019 are `[P]`; T020 depends on the file set being final.

### Parallel Opportunities

- Phase 2 must be serial (same file).
- Once Phase 2 completes: **US1 and US2 can proceed in parallel** (different concerns, different files).
- Within US1: `tests/conftest.py`, `bin/coshsh-cook`, `bin/coshsh-create-template-tree`, `tests/test_pycompat.py` (T010–T013) are all different files and run together.
- Within US2/US3: the `[P]`-marked verification tasks run together.

---

## Parallel Example: User Story 1

```bash
# After Phase 2 (coshsh_pycompat.py) is complete, create/edit all four activation & test files together:
Task: "Create tests/conftest.py with gated import coshsh_pycompat (T010)"
Task: "Edit bin/coshsh-cook: replace future-import with gated bootstrap (T011)"
Task: "Edit bin/coshsh-create-template-tree: same gated bootstrap (T012)"
Task: "Create tests/test_pycompat.py: skipif(>=3.8) legacy-compat regression test (T013)"
# Then run the suite once (T014) — it collects test_pycompat.py automatically.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup (capture red baseline).
2. Phase 2: Foundational — build `coshsh_pycompat.py` (CRITICAL, blocks everything).
3. Phase 3: US1 — conftest + two bin edits + compat test → run 3.6 suite.
4. **STOP and VALIDATE**: `pytest-3` exits 0 on Python 3.6 (SC-001). This is the headline deliverable.

### Incremental Delivery

1. Setup + Foundational → module importable on 3.6 and ≥3.8.
2. US1 → 3.6 suite green incl. `test_pycompat.py` (MVP / SC-001).
3. US2 → prove ≥3.8 inertness + source immutability (SC-002/003/005).
4. US3 → prove review-readiness + file-set constraint (SC-004/006).
5. Polish → quickstart end-to-end + docs.

---

## Notes

- `[P]` = different files, no dependencies.
- The `coshsh/` package is **protected** — no task may modify any file under it (SC-003). Any task that would require editing `coshsh/*.py` is a design error; solve it in `coshsh_pycompat.py` instead.
- Only `bin/coshsh-cook` and `bin/coshsh-create-template-tree` may be edited among pre-existing files (SC-004). `tests/test_pycompat.py` is a **new** file, so it does not count against that constraint.
- `tests/test_pycompat.py` MUST be `skipif`-gated on `sys.version_info >= (3, 8)` — the `tests/` suite stays single-version-agnostic; the compat test only runs where the layer is active (the legacy CI matrix job).
- The compat module MUST stay inert on ≥3.8 — verify the gate, never weaken it.
- Commit after each logical group; keep the diff small and PR-ready (US3).

---

## Implementation Status & Verification Story (2026-07-03)

**Delivered files** (validated in the CentOS 7 / Python 3.6.8 podman playground
`/packages/coshsh/coshsh-12.2.1.1`, then copied to `/src/coshsh` for review):

- `coshsh_pycompat.py` (new) — meta-path finder + AST strip-loader (no `.pyc` cache) +
  `typing.Protocol` / `subprocess.run` shims, all behind the `< (3, 8)` gate. WHY-commented.
- `tests/conftest.py` (new) — gated `import coshsh_pycompat` (package root onto `sys.path`).
- `tests/test_pycompat.py` (new) — `skipif(>=3.8)` legacy-only regression guard.
- `bin/coshsh-cook`, `bin/coshsh-create-template-tree` (edited) — future-import replaced by
  the gated compat bootstrap. **These two are the only pre-existing tracked files modified.**

**Results:**

- **SC-001 (Python 3.6):** baseline 47 collection errors → **213 passed, 8 failed** (full
  suite, `TMPDIR=/tmp pytest-3 -p no:cacheprovider -q`, `LANG=en_US.UTF-8`). Every failure is
  in an **unmodified** upstream test file and is environmental, NOT a coshsh-source version
  incompatibility (T014 triage):
  - `test_pid_perms` — root bypasses permission bits (needs a non-root run user; CI legacy job
    runs as `tester`).
  - `test_pushgateway` ×2 — no Prometheus pushgateway on `127.0.0.1:9091`.
  - `test_configparser` (isa) ×5, `test_coshsh_cook`, `test_extra_dir` — cascade victims of a
    **pre-existing** suite quirk: `datarecipient_simplesample` defaults `objects_dir="/tmp"`
    and its cleanup `rmtree`s `/tmp` mid-run, so later `tempfile`/`/tmp` tests fail depending on
    ordering. **All of these PASS in isolation.** (Matches research's "206 passed, 9 failed,
    2 error" residual baseline; run-to-run variance confirms it is ordering, not code.)
  - `tests/test_pycompat.py` → **6 passed** on Python 3.6 (layer active).
- **SC-002 / SC-005 (Python ≥3.8):** verified inert on the host Python 3.14 — `import
  coshsh_pycompat` installs no `sys.meta_path` finder and no `subprocess` shim (gate False);
  `tests/test_pycompat.py` → **6 skipped**. Full ≥3.8 suite parity is covered by the CI `build`
  matrix (3.8–3.13); it was intentionally NOT run on the host because the unmodified suite's
  `/tmp`-deleting datarecipient cleanup could delete the host `/tmp`.
- **SC-003:** `git diff --stat coshsh/` is empty (0 files) — core sources byte-for-byte pure.
- **SC-004:** only `bin/coshsh-cook` + `bin/coshsh-create-template-tree` edited among
  pre-existing tracked files; everything else is new.
- **SC-006:** every shim in `coshsh_pycompat.py` carries a `WHY` comment naming the
  incompatibility, target Python version, and the contract clause (C1–C4).

**Open item (T024):** the CI workflow `.github/workflows/python-app.yml` is present and
correctly structured (modern `build` 3.8–3.13 + `legacy` 3.6/3.7 in slim-bullseye containers,
non-root provisioning, UTF-8 by default). Confirming the legacy job goes **green** requires an
actual GitHub Actions run and could not be executed from the implementation environment.
