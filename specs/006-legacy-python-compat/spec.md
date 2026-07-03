# Feature Specification: Legacy Python (<3.8) Compatibility Layer

**Feature Branch**: `006-legacy-python-compat`

**Created**: 2026-07-03

**Status**: Draft

**Input**: User description: "add a compat layer so that older pythons < 3.8 are supported. Goal: running `pytest-3` in the coshsh package tree must end with success on a CentOS 7 system with Python 3.6. Constraints: on Python >=3.8 the sources must stay untouched; on Python <3.8 the modifications must be minimal, non-intrusive, and achieved by adding new files rather than editing existing ones. No `.py` file under `coshsh/` may be modified; only `bin/coshsh-cook` and `bin/coshsh-create-template-tree` may be edited."

## Clarifications

### Session 2026-07-03

- Q: The user prefers a version-gated `import <compat>` in `coshsh-cook` / `coshsh-create-template-tree` (and possibly a `tests/` file) over source-transform. But on Python 3.6, `from __future__ import annotations` (present in every coshsh module) fails at **compile time**, so a pure import cannot load the sources at all. How is this reconciled? → A: Keep activation exactly as an import — a version-gated `import` of a new compat module at the top of `bin/coshsh-cook`, `bin/coshsh-create-template-tree`, and a new `tests/conftest.py`. That compat module (a NEW file) installs an import hook that transforms the incompatible source lines **in memory for coshsh's own modules only**, before compilation. The user-visible activation stays a clean import; the source transform is an encapsulated internal mechanism confined to new files (no edits to `coshsh/*.py`) and is uninstalled/inert on Python >=3.8. *(Recorded as the recommended default while the user was away; may be revisited.)*
- Q: Which interpreter does "legacy" concretely mean here? → A: Python 3.6 (CentOS 7 stock `python3` = 3.6.8, consistent with the `python36-jinja2` package name). The compat gate triggers for any interpreter `< 3.8`; 3.6 is the concrete floor and the interpreter on which "success" is judged.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Test suite passes on legacy Python (Priority: P1)

An operator maintaining coshsh for a distribution that still ships an old interpreter (CentOS 7 with Python 3.6) checks out the coshsh source tree, installs the platform packages (`python3-pytest`, `python36-jinja2`), and runs the project test runner (`pytest-3`) from the package root. Today one or more modules fail to import because the sources rely on language and library features that do not exist before Python 3.8. After this feature, the test run completes successfully.

**Why this priority**: This is the headline goal. Without it, coshsh cannot be packaged or trusted on any distribution older than Python 3.8, which excludes an important class of long-lived enterprise Linux systems. Every other outcome depends on the code being importable and runnable there.

**Independent Test**: On a Python 3.6 environment with the coshsh source tree and the required packages installed, run the project test runner from the package root. Success = the runner exits 0 with no import-time or collection-time errors attributable to Python-version incompatibility.

**Acceptance Scenarios**:

1. **Given** a Python 3.6 environment with `python3-pytest` and `python36-jinja2` installed, **When** the test runner is invoked from the package root, **Then** it completes and reports success (exit code 0).
2. **Given** the same environment, **When** any coshsh module is imported, **Then** the import succeeds without a `SyntaxError`, `ImportError`, or `TypeError` caused by unsupported language/library features.
3. **Given** the same environment, **When** the `coshsh-cook` and `coshsh-create-template-tree` entry points are executed, **Then** they run without version-related import failures.

---

### User Story 2 - Modern Python behaviour and sources are unchanged (Priority: P1)

A maintainer packaging coshsh for a mainstream distribution (Python >=3.8, typically 3.12) must be able to ship the sources exactly as they are in the upstream repository, with the compatibility work contributing nothing at runtime. The compatibility layer must be completely inert on modern interpreters.

**Why this priority**: coshsh runs standalone and as part of OMD across many distributions, the majority on Python >=3.8. The compatibility work cannot be allowed to alter, slow, or risk the behaviour that the overwhelming majority of installations depend on. A regression here would be worse than the problem being solved. This shares P1 with User Story 1 because "make it work on old Python" is only acceptable if it provably changes nothing on new Python.

**Independent Test**: On a Python >=3.8 environment, run the full existing test suite before and after this feature is added and confirm identical results; confirm that every file under `coshsh/` is byte-for-byte unchanged versus upstream; confirm the compatibility code is never activated (no compatibility branch executes).

**Acceptance Scenarios**:

1. **Given** a Python 3.12 environment, **When** the full test suite runs with the compatibility feature present, **Then** results are identical to a run without it.
2. **Given** the repository after this feature is merged, **When** the contents of `coshsh/*.py` are compared to their pre-feature state, **Then** there are zero differences.
3. **Given** a Python >=3.8 interpreter, **When** coshsh is imported, **Then** no compatibility-shim code path is taken.

---

### User Story 3 - Additive, review-ready, upstreamable change (Priority: P2)

A coshsh project maintainer reviews the change as a pull request. The diff must be small, obviously correct, and easy to reason about: new files that carry the compatibility logic, and at most the two permitted entry-point files touched to activate it. The reviewer must be able to understand what is shimmed, why, and confirm it is confined to old interpreters.

**Why this priority**: The stated deliverable is a set of modifications ready to become a PR against the coshsh project. A compatibility layer that works but is sprawling, opaque, or intrusive would not be merged and would not achieve the real objective (upstream support for legacy Python). This is P2 because the software could function without perfect elegance, but the deliverable explicitly demands review-readiness.

**Independent Test**: A reviewer unfamiliar with the change can read the added files and the entry-point diffs and, within a few minutes, state exactly which incompatibilities are addressed and confirm the shim is gated on interpreter version.

**Acceptance Scenarios**:

1. **Given** the change as a diff, **When** a maintainer reviews it, **Then** all compatibility behaviour lives in newly added files and the only edited files are `bin/coshsh-cook` and `bin/coshsh-create-template-tree`.
2. **Given** the added files, **When** they are read, **Then** the interpreter-version gate and the specific incompatibilities handled are explicit and self-documenting.

---

### Edge Cases

- **Interpreter exactly at the 3.8 boundary**: The gate must treat Python 3.8+ as "no shim" and anything below as "shim". Behaviour at 3.7 and 3.6 must be well-defined (both are "legacy").
- **Byte-compiled artefacts**: If the environment writes `.pyc` files, stale or wrongly-targeted bytecode must not cause a legacy interpreter to load an incompatible cached form, nor cause a modern interpreter to pick up shimmed output.
- **Import ordering**: Any code path that imports coshsh (test runner, entry points, third-party importer) must trigger the compatibility layer before the first coshsh module is loaded; a coshsh import that bypasses the entry points must still succeed on legacy Python.
- **Partial platform packages**: If `python36-jinja2` or `python3-pytest` is missing, the failure must be an ordinary missing-dependency error, not a confusing version-shim error.
- **Repeated activation**: The shim being installed more than once (e.g. re-imported) must be idempotent and must not corrupt import state.
- **Features that cannot be expressed on the old interpreter**: Where a source construct has no runtime equivalent on the legacy interpreter, the shim must make the affected symbols behave equivalently for coshsh's actual usage, without changing the source.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The coshsh test suite MUST complete successfully (runner exit code 0) on a Python 3.6 (CentOS 7) environment provisioned with `python3-pytest` and `python36-jinja2`.
- **FR-002**: On Python 3.6/3.7, every coshsh module that is exercised by the test suite and the two entry points MUST be importable and usable despite the sources using language/library features introduced after Python 3.6.
- **FR-003**: The compatibility mechanism MUST be activated only when the running interpreter is older than Python 3.8; on Python 3.8 and newer it MUST be completely inert (no behavioural change, no code path taken).
- **FR-004**: No file under `coshsh/` (no `.py` file, no other file in that package directory) may be modified. Compatibility MUST be delivered by adding new files.
- **FR-005**: The only pre-existing files permitted to change are `bin/coshsh-cook` and `bin/coshsh-create-template-tree`, and only to the minimal extent needed to activate the compatibility layer on legacy interpreters — specifically a version-gated `import` of the new compat module placed above the first coshsh import. The test-suite activation path MUST be provided by a NEW `tests/conftest.py` (an added file, not an edit to an existing source), which performs the same version-gated import before any coshsh module is collected.
- **FR-006**: The compatibility layer MUST handle the source's use of `from __future__ import annotations` (PEP 563), which raises a **compile-time** `SyntaxError` on interpreters older than Python 3.7. Because this failure occurs before any module-level code runs, the compat module MUST install an import hook that transforms the offending source in memory prior to compilation, so that affected modules load on the legacy interpreter without editing them.
- **FR-007**: The compatibility layer MUST handle annotation syntax that is only valid on newer interpreters (built-in generic subscripting such as `dict[str, Any]` from PEP 585, and union syntax such as `type | None` from PEP 604) so that importing the modules does not fail on the legacy interpreter.
- **FR-008**: The compatibility layer MUST make runtime imports that reference symbols absent from the legacy standard library resolvable — specifically `typing.Protocol` (introduced in Python 3.8) and any equivalently missing symbols the sources import at module load time — without editing the sources.
- **FR-009**: Behaviour and public results of coshsh on a legacy interpreter MUST be equivalent to its behaviour on a modern interpreter for the scenarios covered by the existing test suite (the shim provides compatibility, not new or altered functionality).
- **FR-010**: Activation of the compatibility layer MUST be idempotent and MUST reliably occur before the first coshsh module is imported by any supported entry path — the two console scripts (`bin/coshsh-cook`, `bin/coshsh-create-template-tree`) and the test-suite bootstrap (`tests/conftest.py`).
- **FR-013**: The in-memory source transformation MUST be scoped to coshsh's own modules only (it MUST NOT rewrite third-party or standard-library modules), and the import hook MUST be uninstalled or never installed on Python >=3.8, guaranteeing FR-003 inertness.
- **FR-011**: The change set contained in the coshsh package tree MUST be self-contained and ready to be submitted as a pull request to the coshsh project (no reliance on files outside the tracked source tree).
- **FR-012**: The added files MUST be self-documenting: a reviewer MUST be able to identify the interpreter-version gate and the specific incompatibilities addressed by reading them.

### Key Entities *(include if feature involves data)*

- **Legacy interpreter environment**: A Python runtime older than 3.8 (concretely Python 3.6 on CentOS 7) plus the platform-provided packages `python3-pytest` and `python36-jinja2`. It is the environment in which the test suite must pass.
- **Compatibility layer (new files)**: The added, version-gated code that reconciles the post-3.6 constructs in the sources with what the legacy interpreter can execute. Inert on Python >=3.8.
- **Activation points**: The two entry points (`bin/coshsh-cook`, `bin/coshsh-create-template-tree`) — the only edited pre-existing files — plus a new `tests/conftest.py`, each performing a version-gated `import` of the compat module before coshsh is imported.
- **Protected sources**: All files under `coshsh/`, which must remain byte-for-byte identical to upstream.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running the project test runner from the package root on the Python 3.6 CentOS 7 environment finishes with success (exit code 0) and zero failures or collection errors caused by interpreter-version incompatibility.
- **SC-002**: On a Python >=3.8 environment, the test-suite outcome is identical with and without the compatibility feature present (same passed/failed/skipped counts).
- **SC-003**: A diff of `coshsh/` against its pre-feature state shows zero changed files.
- **SC-004**: The set of pre-existing files changed by this feature is exactly `{bin/coshsh-cook, bin/coshsh-create-template-tree}` and no others; all remaining compatibility logic resides in newly added files.
- **SC-005**: On Python >=3.8, no compatibility code path executes (verifiable by the gate short-circuiting on interpreter version).
- **SC-006**: A maintainer can review the change and, without prior context, correctly enumerate the incompatibilities it addresses and confirm the version gate within a single review pass.

## Assumptions

- The oldest interpreter that must be supported is Python 3.6 (CentOS 7 stock `python3` = 3.6.8, consistent with the `python36-jinja2` package name); the compatibility work targets the `< 3.8` range with 3.6 as the concrete floor. Interpreters older than 3.6 are out of scope. **Verified 2026-07-03** on the provided container (Python 3.6.8; EPEL `python36-pytest` 2.9.2 and `python36-jinja2` 2.11.1 installed as system packages): `from __future__ import annotations` and `from typing import Protocol` both fail as predicted, and a baseline `pytest-3` run in the package tree produces **47 collection errors**, every one rooted in `SyntaxError: future feature annotations is not defined` at `coshsh/__init__.py:40`.
- The legacy toolchain is old (pytest 2.9.2, jinja2 2.11.1). The success criterion is the test suite passing on *this* toolchain; the plan/implementation must account for possible secondary incompatibilities (e.g. older pytest collection semantics or older Jinja2 API) beyond the language-level ones, without editing `coshsh/*.py`.
- The activation mechanism is a version-gated `import` of a new compat module (per the Session 2026-07-03 clarification), not a build-time or checked-in rewrite of the sources. The unavoidable source transformation for `from __future__ import annotations` and post-3.6 annotation syntax is performed at import time by a hook the compat module installs, and remains an internal detail of the added files.
- Jinja2 is provided by the platform package `python36-jinja2` and the test runner by `python3-pytest`; the feature does not bundle or upgrade these and assumes they are installed.
- The exception mentioned in the task allowing a version-check import in a file header applies, in practice, to the two permitted entry-point files; the stricter success criterion (no `coshsh/*.py` modified) governs the protected source directory.
- The incompatibilities to address are those the sources actually exercise at import/run time: `from __future__ import annotations` (fails <3.7), PEP 585/PEP 604 annotation syntax, and `typing.Protocol` (added 3.8). The plan phase will confirm this is the complete set by exercising the full test suite on the target interpreter.
- Because all annotations in the sources are already deferred via `from __future__ import annotations`, they are never evaluated at runtime on modern Python; the legacy behaviour only needs to preserve that "annotations are not evaluated" property, not reproduce the new typing objects.
- The development/verification environment is the provided CentOS 7 podman container (Python 3.6); "success" is judged there.
- The `python2` branch referenced elsewhere in the repository is unrelated; this feature concerns Python 3.6/3.7 compatibility of the current Python 3 sources, not Python 2.
