# Implementation Plan: Legacy Python (<3.8) Compatibility Layer

**Branch**: `006-legacy-python-compat` | **Date**: 2026-07-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/006-legacy-python-compat/spec.md`

## Summary

coshsh's core sources target Python 3.12 and use `from __future__ import annotations` (a compile-time `SyntaxError` on Python <3.7), PEP 585/604 annotation syntax, and `typing.Protocol` (3.8+). On CentOS 7 / Python 3.6.8 the test suite cannot even be collected (47 collection errors). This feature adds an **additive, version-gated compatibility layer** that lets the *unmodified* `coshsh/` sources import and run on Python 3.6, achieved through **one new file** (`coshsh_pycompat.py`) plus a new `tests/conftest.py`, and a minimal edit to the two permitted entry points. On Python ≥3.8 the layer is never installed and is completely inert.

**Technical approach (validated on the container, see [research.md](./research.md)):** a `sys.meta_path` finder scoped to the `coshsh.*` namespace swaps in a `SourceFileLoader` subclass whose `source_to_code()` runs an `ast` transform — it removes the `from __future__ import annotations` statement and strips all annotations (so PEP 585/604 syntax is never evaluated) before compilation. The same module injects a no-op `typing.Protocol` and translates `subprocess.run(capture_output=…)` (3.7+) for 3.6. Activation is a plain `import coshsh_pycompat` guarded by `if sys.version_info < (3, 8)` at the top of `bin/coshsh-cook`, `bin/coshsh-create-template-tree`, and `tests/conftest.py`.

**Proven result:** suite goes from *47 collection errors (0 tests run)* → **206 passed**. Every residual failure is an ordinary test-environment prerequisite (writable `/tmp` & `/var/tmp`, non-root execution, optional deps `python36-pycryptodomex` / `prometheus_client`, a running pushgateway, a clean working tree) — **none** is a coshsh-source Python-version incompatibility.

## Technical Context

**Language/Version**: Python 3.6.8 (target floor; gate triggers for any `< 3.8`). Core sources remain Python 3.12-authored and untouched.

**Primary Dependencies**: stdlib only for the compat layer (`ast`, `importlib.abc`, `importlib.machinery`, `sys`, `typing`, `subprocess`). Runtime deps unchanged: Jinja2 (EPEL `python36-jinja2` 2.11.1 on target), `configparser` (stdlib).

**Storage**: Filesystem (generated config files); N/A to this feature beyond needing writable temp dirs for tests.

**Testing**: pytest (EPEL `python36-pytest` 2.9.2 on target; runner binary `pytest-3`). Modern coshsh CI uses newer pytest; tests must pass on both.

**Target Platform**: Linux (CentOS 7 / RHEL 7-era distros with Python 3.6/3.7), standalone and inside OMD, built from the source tree.

**Project Type**: Single Python library + CLI (config generator). Not web/mobile.

**Performance Goals**: No new performance surface. Import-time transform runs once per coshsh module on legacy interpreters only; negligible. Constitution's 60k-services/10s benchmark is unaffected (modern Python path is byte-for-byte unchanged).

**Constraints**:
- MUST NOT modify any file under `coshsh/` (byte-for-byte identical to upstream).
- Only `bin/coshsh-cook` and `bin/coshsh-create-template-tree` may be edited among pre-existing files.
- `setup.py` is **not** editable → the compat module is a top-level source-tree module discovered via `sys.path`, not a `py_modules` install entry. `setup.py`'s `python_requires='>=3.8'` already blocks `pip install` on 3.6, so the only supported legacy path is running from the source tree (exactly the OMD-packaging and `pytest-3` scenarios). This is acceptable and documented.
- Layer MUST be inert and uninstalled on Python ≥3.8 (FR-003, FR-013).

**Scale/Scope**: ~1 new module (~120 LOC), 1 new `tests/conftest.py` (~4 LOC), 2 one-line-region edits to bin scripts. 215-test suite is the acceptance surface.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|-----------|------------|
| I. Configuration-as-Code | ✅ N/A — no change to generation model. |
| II. Extensibility via Class/Template files; **no core source modified** | ✅ **Reinforced.** The entire feature is additive; `coshsh/` stays pristine. This is the strongest possible expression of the principle. |
| III. Test-First | ✅ Red baseline is captured and reproducible (47 collection errors → then per-run counts). Acceptance is the green suite on 3.6. No new product code needing unit tests beyond the compat module itself, whose "test" is the existing suite passing on 3.6. |
| IV. Performance & determinism | ✅ Modern-Python path unchanged (byte-for-byte); legacy path adds a one-time import transform only. |
| V. Simplicity / minimal surface | ✅ One stdlib-only module + a 4-line conftest + tiny bin edits. No new runtime dependency. |
| VI. AI-First (comment-rich) | ✅ Compat module will carry `WHY` comments explaining the compile-time-SyntaxError constraint and each shim. |

**✅ Technology-Constraints: covered by the legacy-Python carve-out (Constitution v1.2.0).** The base constraint states *"no Python 2 or pre-3.12 compatibility shims permitted in new code,"* but Constitution v1.2.0 adds an explicit **"Legacy-Python compatibility exception (bounded)"** that permits pre-3.12 support *iff* it is delivered as an additive compat layer in **extra new files** with core sources untouched, version-gated and fully inert on modern interpreters, and scoped to coshsh's own modules. This feature satisfies every condition of that carve-out: (1) it modifies **zero** core source files — `coshsh/` stays byte-for-byte pure 3.12; (2) all logic lives in new files (`coshsh_pycompat.py`, `tests/conftest.py`), with only a minimal version-gated activation `import` in the two permitted entry-point scripts; (3) it is version-gated and completely inert on Python ≥3.8 (and 3.12+); (4) its transform is scoped to `coshsh.*` only and never touches third-party/stdlib imports (FR-013). It therefore falls under an **approved, first-class pattern** and does **not** require a Principle-V Complexity-Tracking waiver. **Gate: PASS (carve-out applies).**

## Project Structure

### Documentation (this feature)

```text
specs/006-legacy-python-compat/
├── plan.md              # This file
├── spec.md              # Feature spec (+ Clarifications)
├── research.md          # Phase 0 — mechanism + failure taxonomy (validated on container)
├── data-model.md        # Phase 1 — compat components & their relationships
├── quickstart.md        # Phase 1 — exact provision+run verification steps
├── contracts/
│   └── compat-activation.md   # Activation & transform contract
└── checklists/
    └── requirements.md  # Spec quality checklist (from /speckit-specify)
```

### Source Code (repository root)

```text
coshsh/                         # UNTOUCHED — 19 modules with `from __future__ import annotations`
├── __init__.py                 # line 40 future-import = the compile-time failure point
├── datainterface.py            # imports typing.Protocol (3.8+); dynamic class loading
├── jinja2_extensions.py        # heavy f-strings (fine on 3.6)
└── … (all other modules unchanged)

coshsh_pycompat.py              # NEW — the compatibility layer (top-level module)
                                #   • version gate (< 3.8)
                                #   • coshsh.*-scoped meta_path finder + AST-strip loader
                                #   • typing.Protocol / runtime_checkable shim
                                #   • subprocess.run(capture_output=) shim
bin/coshsh-cook                 # EDIT — replace line-9 future-import with gated bootstrap
bin/coshsh-create-template-tree # EDIT — same
tests/conftest.py               # NEW — gated `import coshsh_pycompat` before collection
tests/…                         # UNTOUCHED
recipes/default/classes/*.py    # UNTOUCHED — verified: none use post-3.6 syntax
setup.py                        # UNTOUCHED (python_requires='>=3.8' retained)
```

**Structure Decision**: Single-project layout, unchanged. The compat module lives at the **repository/source-tree root** (sibling to the `coshsh/` package) because it MUST execute *before* the `coshsh` package is imported — it cannot live inside `coshsh/` (importing anything there runs `coshsh/__init__.py`, which is exactly the file that fails to compile on 3.6). Discovery is via `sys.path` (the bin scripts insert `..`; `tests/conftest.py` inserts the package root), not `setup.py` registration.

## Complexity Tracking

> No Principle-V waiver is required: the pre-3.12 compat layer is an **approved, first-class
> pattern** under the Constitution v1.2.0 "Legacy-Python compatibility exception (bounded)" (see
> Constitution Check above). The rows below are retained only as **design-complexity notes** —
> they explain non-obvious mechanism choices, not constitution violations.

| Design note | Why Needed | Simpler Alternative Rejected Because |
|-------------|------------|--------------------------------------|
| External compat layer instead of editing the core | OMD/enterprise distros still ship Python 3.6/3.7; the pristine 3.12 core must be runnable there without forking it | Editing `coshsh/*.py` to be 3.6-compatible would pollute the core with backport code, violate the spec's hard constraint (and the carve-out's condition 1), and create a maintenance fork. The additive external layer keeps the core pure. |
| Import hook that rewrites source (vs. a pure "import a module" shim) | `from __future__ import annotations` is a **compile-time** `SyntaxError` on 3.6 — no runtime shim can make an unmodified module import without transforming its source before compilation | A pure runtime import shim was the user's initial preference but is technically impossible for the future-import case (confirmed on the container). The transform is confined to the compat module and scoped to `coshsh.*` only (FR-013). |
