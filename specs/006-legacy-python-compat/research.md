# Phase 0 Research: Legacy Python (<3.8) Compatibility

All findings below were **empirically validated** on the provided podman container `4e89e6751911` (CentOS 7, Python 3.6.8) on 2026-07-03, not merely reasoned about. See [quickstart.md](./quickstart.md) for the exact reproduction steps.

## Decision 1 — Where the incompatibilities live

**Decision**: Only the `coshsh/` package needs source-level compatibility treatment.

**Evidence**:
- `from __future__ import annotations` appears in **19 files, all under `coshsh/`**. It appears in **zero** files under `recipes/`, `tests/`, or `contrib/`.
- No PEP 585 (`dict[str, Any]`) or PEP 604 (`type | None`) annotation syntax exists in `recipes/` or `tests/`.
- `typing.Protocol` (3.8+) is imported at module load in `coshsh/datainterface.py` and used as a base class (`class IdentFunction(Protocol)`).
- The 30 default recipe class files (`recipes/default/classes/*.py`), which coshsh loads dynamically via `importlib.util.spec_from_file_location`, use **no** post-3.6 syntax.

**Rationale**: A meta-path finder scoped to the `coshsh.*` namespace is sufficient and honors FR-013 (do not rewrite third-party/stdlib modules). Dynamically-loaded recipe files and test modules need no transform.

**Alternatives considered**: Globally monkey-patching `importlib.machinery.SourceFileLoader.source_to_code` (covers every file-based load in one patch) — **rejected**: it would also transform third-party libraries (Jinja2 etc.), violating FR-013, for no benefit given the evidence above.

## Decision 2 — Handling the compile-time `SyntaxError`

**Decision**: An `ast`-based source transform inside a custom `SourceFileLoader`, installed via a `sys.meta_path` finder for `coshsh.*`.

**Evidence**:
- On 3.6, `from __future__ import annotations` raises `SyntaxError: future feature annotations is not defined` at **compile time** (confirmed). A pure "import a shim first" approach therefore cannot make an unmodified `coshsh` module import — the module never compiles.
- `ast.parse()` on 3.6 **tolerates** both the future-import statement and PEP 585/604 syntax (validation happens during `compile()`, not during `PyCF_ONLY_AST` parsing) — confirmed. So the source can be parsed, transformed, and recompiled.
- The transform: (a) drop `from __future__ import annotations`; (b) strip every annotation (`arg.annotation`, `FunctionDef.returns`, convert annotated-assignments-with-value to plain assignments, drop annotation-only statements, insert `pass` into any emptied block). With annotations removed, the PEP 585/604 syntax is never evaluated → no runtime error.
- Because the upstream code already uses `from __future__ import annotations`, its annotations are never evaluated at runtime on modern Python either; stripping them on 3.6 preserves identical *runtime* behavior.

**Validation**: Importing the real, unmodified `coshsh` package (Generator, Application, `datainterface.IdentFunction`) through the prototype loader succeeded on 3.6. Full suite: **47 collection errors → 186 passed** with just this transform + the `Protocol` shim.

**Alternatives considered**:
- `compile(src, path, 'exec', flags=annotations.compiler_flag)` to enable PEP 563 without the source line — **rejected**: the `annotations` future/flag does not exist on 3.6.
- Text/regex source rewriting — **rejected**: fragile; annotations span multiple lines and contexts. AST is robust and stdlib-only.
- The `strip-hints` PyPI package — **rejected**: adds a dependency; target is offline/EPEL and the constitution prefers stdlib.

## Decision 3 — `typing.Protocol`

**Decision**: Inject a no-op `typing.Protocol` (and `typing.runtime_checkable`) when absent.

**Evidence**: `from typing import Protocol` raises `ImportError` on 3.6 (confirmed). `IdentFunction(Protocol)` only needs `Protocol` to be a usable base class at runtime; coshsh does no structural-typing enforcement against it. A bare `class Protocol: pass` suffices.

## Decision 4 — `subprocess.run(capture_output=…)`

**Decision**: Monkey-patch `subprocess.run` (in the compat module) to translate `capture_output=True` → `stdout=PIPE, stderr=PIPE` on <3.7.

**Evidence**: `capture_output` is a 3.7+ kwarg (`TypeError` on 3.6, confirmed). It is used **only** in `tests/test_delta.py` (git subprocess calls). Since test files are not editable, the shim — active because `tests/conftest.py` imports the compat module — fixes it without touching the test.

## Decision 5 — Activation points & module location

**Decision**: Top-level `coshsh_pycompat.py`; activated by a `sys.version_info < (3, 8)` guarded `import` in `bin/coshsh-cook`, `bin/coshsh-create-template-tree`, and a new `tests/conftest.py` (which inserts the package root onto `sys.path` first).

**Rationale**: The module must run before the `coshsh` package imports, so it cannot live inside `coshsh/`. `setup.py` cannot be edited (constraint) and already sets `python_requires='>=3.8'`, so `pip install` on 3.6 is impossible anyway; the supported legacy path is running from the source tree (OMD build + `pytest-3`), where `sys.path` discovery works. The bin scripts' existing fallback already appends the source root to `sys.path`; the edit adds the gated compat import above the first `coshsh` import and removes the bin file's own `from __future__ import annotations` (which would otherwise fail the script on 3.6 — this is why the bin subprocess tests, e.g. `test_bin`, fail until the bin files are fixed).

**Idempotence**: the finder checks it is not already installed; the `typing`/`subprocess` shims check `hasattr`/a sentinel. Importing the module repeatedly is safe (FR-010).

## Failure taxonomy after full activation (validated)

Starting point: **47 collection errors, 0 tests run.** After the compat module + bin edits + conftest, and progressively provisioning the environment:

| Run | Config | Result |
|-----|--------|--------|
| Baseline | none | 47 collection errors |
| Hook + Protocol shim + conftest | core language compat | **186 passed**, 29 failed, 2 error |
| + bin edits + `python36-pycryptodomex` | vault + bin subprocess | 190 passed, 25 failed |
| + `prometheus_client`, `/var/tmp`, clean tree | optional deps + dirs | 201 passed, 14 failed |
| + `subprocess` shim | test_delta git calls | 201 passed, 14 failed (delta symptom changed) |
| + git identity + clean root `var/objects` | env hygiene | **206 passed**, 9 failed, 2 error |

**The 9 residual failures + 2 errors are all environmental — none is a coshsh-source Python-version incompatibility:**

1. **`test_bin` (1 fail + tempfiles)** — the container has no writable `/var/tmp` (and `/tmp` is recreated ad hoc); `CommonCoshshTest` temp files fail to create. → **Env**: ensure writable `/tmp` and `/var/tmp`.
2. **`test_pid:112` "non-writable pid dir was not correctly detected"** — the suite runs as **root**; root bypasses permission bits, so the negative test cannot trigger. → **Env**: run tests as a non-root user.
3. **`test_pushgateway:19/:25` + 2 teardown errors** — need a Prometheus pushgateway listening on `127.0.0.1:9091` (`Connection refused`). → **Env**: run a pushgateway (as coshsh CI/real deployments do) or the tests are skipped there.

Additionally required as ordinary install prerequisites (already applied above; a real coshsh install/CI has them): `python36-pycryptodomex` (vault backend), `prometheus_client` (pushgateway datarecipient), `git` + a git identity (delta tests), and a **clean working tree** (untracked `var/objects/**/dynamic/*` leftovers from prior local runs caused `NotADirectoryError`; absent in a fresh checkout).

**Conclusion**: The compatibility deliverable (compat module + 2 bin edits + conftest) resolves **100%** of the Python-3.6 language/stdlib incompatibilities. Reaching a fully green `pytest-3` is then a matter of standard test-environment provisioning, documented in [quickstart.md](./quickstart.md), and is independent of the coshsh sources.

## Open items for implementation (not blockers)

- Decide `tests/conftest.py` vs. a root `conftest.py`. Both work; `tests/conftest.py` (inserting the package root onto `sys.path`) matches the spec wording. The prototype used a root `conftest.py`; either is acceptable.
- Confirm on modern Python (≥3.8) CI that `tests/conftest.py` and the bin edits are inert (the gate short-circuits; `bin` scripts no longer carry `from __future__ import annotations`, which is a harmless removal there).
