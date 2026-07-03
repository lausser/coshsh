# Phase 1 Data Model: Legacy Python Compatibility

This feature has no business data entities. The "entities" here are the software components of the compatibility layer and their relationships/lifecycle.

## Components

### `coshsh_pycompat` (new top-level module)

The single compatibility unit. Purely additive; stdlib-only.

**Public surface**: importing the module is the entire API. On import it decides, from `sys.version_info`, whether to install anything.

**Internal parts**:
- **Version gate** — `if sys.version_info < (3, 8): _install()`. Above the gate, importing is a no-op on modern Python.
- **AST annotation-stripper** (`ast.NodeTransformer`) — removes `from __future__ import annotations`; nulls `arg.annotation` / `FunctionDef.returns`; converts annotated assignments with a value to plain assignments; drops annotation-only statements; repairs emptied blocks with `pass`.
- **Strip loader** (`importlib.machinery.SourceFileLoader` subclass) — overrides `source_to_code()` to parse → transform → `compile()`.
- **coshsh finder** (`importlib.abc.MetaPathFinder`) — returns a spec (from the default `PathFinder`) with the strip loader swapped in, **only** for `fullname == "coshsh"` or `fullname.startswith("coshsh.")`.
- **`typing.Protocol` shim** — injects a no-op `Protocol` and `runtime_checkable` if absent.
- **`subprocess.run` shim** — wraps `subprocess.run` to translate `capture_output=`.

**Invariants**:
- Idempotent: finder not re-added if already present; shims guarded by `hasattr`/sentinel.
- Scope-limited: transforms **only** `coshsh.*` modules (FR-013).
- Inert on ≥3.8: nothing is installed; behavior identical to upstream (FR-003).

### `tests/conftest.py` (new)

Test-suite bootstrap. Under `sys.version_info < (3, 8)`, inserts the package root onto `sys.path` and imports `coshsh_pycompat`. Runs before pytest collects any test module, so the finder is active before the first `import coshsh`.

### `bin/coshsh-cook`, `bin/coshsh-create-template-tree` (edited)

Entry points. Edit = replace the file's own `from __future__ import annotations` (line 9, itself a 3.6 compile error) with a `sys.version_info < (3, 8)`-gated block that inserts the source root onto `sys.path` and imports `coshsh_pycompat`, placed above the first `import coshsh`.

## Relationships / activation graph

```text
        Python ≥ 3.8                     Python < 3.8
        ───────────                      ───────────
  bin scripts ─┐                   bin scripts ──┐  (drop future-import,
  conftest.py ─┼─► import coshsh   conftest.py ──┼─► import coshsh_pycompat ─► _install()
               │   (unchanged)                   │        │
               ▼                                 ▼        ├─► sys.meta_path finder (coshsh.*)
        gate is False:                    import coshsh ──┘        └─► StripLoader ─► ast transform ─► compile
        nothing installed,                (now compiles &          ├─► typing.Protocol shim
        fully inert                        runs unmodified)         └─► subprocess.run shim
```

## Lifecycle

1. Interpreter starts an entry path (bin script or pytest via conftest).
2. Version gate evaluated once. On ≥3.8 → stop (inert). On <3.8 → `_install()` (idempotent).
3. First `import coshsh` / `import coshsh.<mod>` is intercepted by the finder; source is transformed and compiled; module behaves as on modern Python.
4. Dynamically-loaded recipe classes and test modules load normally (they contain no post-3.6 syntax; not intercepted).

## Validation rules (map to acceptance)

- No file under `coshsh/` changes (diff = empty) — SC-003.
- Edited pre-existing files == exactly `{bin/coshsh-cook, bin/coshsh-create-template-tree}` — SC-004.
- On ≥3.8, suite results identical with/without the layer — SC-002/SC-005.
- On 3.6 with a provisioned environment, `pytest-3` succeeds — SC-001.
