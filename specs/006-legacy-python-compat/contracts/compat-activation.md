# Contract: Compatibility Layer Activation & Transform

This is the behavioral contract the compatibility layer MUST satisfy. It is the "interface" this feature exposes (a library/CLI, not a network API).

## C1 — Activation gate

- **Given** any interpreter, **when** `coshsh_pycompat` is imported, **then** it installs its hooks **iff** `sys.version_info < (3, 8)`; on `>= (3, 8)` importing it is a no-op with no observable side effect (no `sys.meta_path` change, no attribute added to `typing`/`subprocess`).
- **Given** the module is imported more than once (or from multiple entry points), **then** installation is idempotent (finder present at most once; shims applied at most once).

## C2 — coshsh module loading (legacy)

- **Given** Python < 3.8 with the layer installed, **when** `import coshsh` or `import coshsh.<anything>` runs, **then** it succeeds; specifically the module compiles despite `from __future__ import annotations` and despite PEP 585/604 annotation syntax.
- **Then** the imported module's **runtime behavior is equivalent** to the same module on Python ≥3.8 (annotations are not evaluated in either case; only annotation metadata differs, which coshsh does not consume).

## C3 — Scope limitation

- **Given** the layer is installed, **when** a **non-`coshsh`** module is imported (stdlib, Jinja2, pytest, dynamically-loaded recipe class files), **then** the layer does **not** transform it (finder returns `None` for names outside `coshsh.*`).

## C4 — Symbol shims (legacy)

- **Given** Python < 3.8, **then** `typing.Protocol` and `typing.runtime_checkable` are importable/usable (no-op stand-ins) such that `class IdentFunction(Protocol)` in `coshsh/datainterface.py` loads.
- **Given** Python < 3.7, **then** `subprocess.run(..., capture_output=True)` behaves as `stdout=PIPE, stderr=PIPE` (used by `tests/test_delta.py`).

## C5 — Entry-point contract

- **Given** Python < 3.8, **when** `bin/coshsh-cook` or `bin/coshsh-create-template-tree` is executed (including as a subprocess by `tests/test_bin.py`), **then** the script starts without `SyntaxError` and activates the layer before importing `coshsh`.
- **Given** Python ≥ 3.8, **then** the edited bin scripts behave exactly as before (the removed `from __future__ import annotations` had no functional effect there; the gated block is skipped).

## C6 — Source-immutability contract

- No file under `coshsh/` is modified (byte-for-byte identical to upstream).
- Among pre-existing files, only `bin/coshsh-cook` and `bin/coshsh-create-template-tree` are edited. All other compatibility artifacts are **new** files (`coshsh_pycompat.py`, `tests/conftest.py`).

## Acceptance test (contract-level)

Run the coshsh suite on the target interpreter in a provisioned environment (see [quickstart.md](../quickstart.md)):

- **Pass condition (SC-001)**: `pytest-3` exits 0 with no failures attributable to Python-version incompatibility.
- **Regression guard (SC-002/SC-005)**: on Python ≥3.8, `pytest` results are identical with and without the layer present; the layer installs nothing.
