# Lessons

## 2026-07-03 — Legacy Python (<3.8) compat layer (spec 006)

### The compat layer must transform SOURCE, not runtime
- **Failure mode considered**: a pure "import a shim module first" approach cannot make
  an unmodified `coshsh` module import on 3.6, because `from __future__ import annotations`
  is a **compile-time** `SyntaxError` — the module never reaches runtime.
- **Prevention rule**: for compile-time incompatibilities, intercept via a `sys.meta_path`
  finder + a `SourceFileLoader` that AST-rewrites the source before `compile()`. Scope the
  finder to the owning namespace (`coshsh.*`) so stdlib/third-party stay untouched (FR-013).

### Disable the bytecode cache for transformed modules
- **Failure mode**: a `.pyc` compiled from *untransformed* source (by a modern interpreter
  or another tool) can shadow the transform on <3.8 and reintroduce the SyntaxError path;
  conversely a transformed `.pyc` would persist a shimmed artifact.
- **Prevention rule**: in the strip loader, override `get_code()` to always recompile from
  source and `set_data()` to a no-op so no `.pyc` is read or written.

### Validate in a DISPOSABLE copy, never run the suite on the host
- **Failure mode (detected the hard way)**: several *unmodified* test files
  (`test_datarecipient`, `test_recipes`, `test_extensions`, `test_for_tool`) drive a
  `datarecipient_simplesample` whose default `objects_dir="/tmp"`; its cleanup `rmtree`s
  that dir and **deletes `/tmp` itself** mid-run. In a *dirty* playground it even escalated
  to wiping the whole playground tree.
- **Detection signal**: pytest crashes at teardown with `chdir(...startdir...)` ENOENT, and
  later `tempfile`-based tests fail with `FileNotFoundError: /tmp/tmpXXXX.cfg`. Failure
  counts vary run-to-run (ordering-dependent) — a tell that it is an isolation quirk, not a
  deterministic code defect.
- **Prevention rule**: run the full suite only inside the disposable container playground
  (`/packages/coshsh/coshsh-12.2.1.1`), rebuilt fresh via `rsync` with `var/objects` removed
  (per quickstart.md). Do **not** run it on the mounted host — it can delete the host `/tmp`.
  Recreate `/tmp` & `/var/tmp` (chmod 1777) before each run.

### CentOS 7 needs an explicit UTF-8 locale
- **Failure mode**: with `LANG` unset the interpreter defaults to ASCII; Python 3.6 then
  opens cookbook files in ascii mode → `UnicodeDecodeError: 'ascii' codec ... byte 0xc3`.
- **Prevention rule**: run with `LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8`. (The CI legacy job
  uses `python:<ver>-slim-bullseye`, which sets `LANG=C.UTF-8` by default, so it is immune.)

### `podman exec` needs `-i` to feed a heredoc
- **Failure mode**: `podman exec CID python3 - <<'EOF'` silently ran no code (empty stdin),
  leaving files unchanged with no error.
- **Prevention rule**: use `podman exec -i` whenever piping stdin into the container.
