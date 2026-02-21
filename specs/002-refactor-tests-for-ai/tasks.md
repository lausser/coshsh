# Tasks: 002-refactor-tests-for-ai

Generated: 2026-02-21
Spec: specs/002-refactor-tests-for-ai/spec.md
Branch: 002-refactor-tests-for-ai

## Dependency Order

```
TASK-000
  └─ TASK-001
       ├─ TASK-002 (batch: tiny 1-test files A)
       ├─ TASK-003 (batch: tiny 1-test files B)
       ├─ TASK-004 (batch: tiny 1-test files C)
       ├─ TASK-005 (batch: small 2-test files A)
       ├─ TASK-006 (batch: small 2-test files B)
       ├─ TASK-007  test_bin
       ├─ TASK-008  test_contacts
       ├─ TASK-009  test_delta       ← special: extract git helper
       ├─ TASK-010  test_dest
       ├─ TASK-011  test_rcp_logs
       ├─ TASK-012  test_recipeattrs
       ├─ TASK-013  test_recex
       ├─ TASK-014  test_application_mysql
       ├─ TASK-015  test_classes
       ├─ TASK-016  test_details
       ├─ TASK-017  test_git
       ├─ TASK-018  test_package
       ├─ TASK-019  test_pid
       ├─ TASK-020  test_recipes
       └─ TASK-021  test_vault
            └─ (all above) → TASK-022 (final verification)
```

---

## TASK-000 — Record baseline

**Status**: pending
**Depends on**: —

Run the full test suite and record the exact numbers before any changes are made.
This becomes the acceptance gate for TASK-022.

Steps:
1. `python -m pytest tests/ -v --tb=short 2>&1 | tee /tmp/coshsh_baseline.txt`
2. Note total collected, passed, failed, and the name of the one pre-existing failure.
3. Write the numbers into a comment at the top of `specs/002-refactor-tests-for-ai/tasks.md`
   (update this file).

Acceptance: baseline numbers recorded; no production code touched.

---

## TASK-001 — Refactor `tests/common_coshsh_test.py`

**Status**: pending
**Depends on**: TASK-000

`common_coshsh_test.py` is the base class used by every test file. Clean it up first
so that all subsequent tasks start from a correct base.

Changes required:
- Add module docstring: `"""Base test class and shared infrastructure for all coshsh tests."""`
- Remove the duplicate `print_header` method definition (it appears twice — keep the
  one already defined before `setUp`; remove the second at the bottom of the file).
- Remove unused import `pprint` (the `pp` attribute is still set in setUp — keep the
  import only if `pp` is actually used in any test file; if not, remove both).
- Do NOT change any public method signatures (`setUp`, `tearDown`, `setUpConfig`,
  `setUpObjectsDir`, `clean_generator`, `print_header`).

Commit message: `tests: clean up common_coshsh_test.py base class`

Acceptance: file passes `python -m py_compile tests/common_coshsh_test.py`; full
suite still shows the same baseline numbers.

---

## TASK-002 — Refactor batch A: five 1-test files

**Status**: pending
**Depends on**: TASK-001

Files (one test each — minimal effort per file):

| File | Current class | New class | Notes |
|------|--------------|-----------|-------|
| `tests/test_attrstrip.py` | CoshshTest | AttrStripTest | |
| `tests/test_catchall.py` | CoshshTest | CatchallTest | |
| `tests/test_datainterface.py` | CoshshTest | DatainterfaceTest | |
| `tests/test_extensions.py` | CoshshTest | ExtensionsTest | |
| `tests/test_inheritance.py` | CoshshTest | InheritanceTest | |

For each file apply the full golden-template checklist:
- [ ] Add module docstring (one sentence describing what the file tests).
- [ ] Rename class from `CoshshTest` to the name in the table above.
- [ ] Add a one-line docstring to every test method.
- [ ] Replace `assertTrue(x == y)` with `assertEqual(x, y)` throughout.
- [ ] Replace `assertTrue(x != y)` with `assertNotEqual(x, y)`.
- [ ] Replace `assertTrue(not x)` with `assertFalse(x)`.
- [ ] Replace `assertTrue(os.path.exists(p))` with `assertTrue(os.path.exists(p))` — this form is acceptable since there is no `assertPathExists` in unittest; leave as-is but add a comment if the path string is non-obvious.
- [ ] Remove all `print()` calls.
- [ ] Remove unused imports.
- [ ] Verify `python -m pytest <file> -v` passes before committing.

One commit per file. Commit message template:
`tests: refactor test_<name>.py → <ClassName>Test`

---

## TASK-003 — Refactor batch B: five 1-test files

**Status**: pending
**Depends on**: TASK-001

Files:

| File | New class |
|------|-----------|
| `tests/test_host_attributes.py` | HostAttributesTest |
| `tests/test_merge.py` | MergeTest |
| `tests/test_myjinja.py` | MyJinjaTest |
| `tests/test_nagiosconf.py` | NagiosconfTest |
| `tests/test_obdir_paths.py` | ObdirPathsTest |

Apply the full golden-template checklist from TASK-002. One commit per file.

---

## TASK-004 — Refactor batch C: four 1-test files

**Status**: pending
**Depends on**: TASK-001

Files:

| File | New class |
|------|-----------|
| `tests/test_order.py` | OrderTest |
| `tests/test_regex_filters.py` | RegexFiltersTest |
| `tests/test_suffix.py` | SuffixTest |
| `tests/test_timeperiod.py` | TimeperiodTest |

Apply the full golden-template checklist from TASK-002. One commit per file.

---

## TASK-005 — Refactor batch D: four 2-test files

**Status**: pending
**Depends on**: TASK-001

Files:

| File | New class | Notes |
|------|-----------|-------|
| `tests/test_csv_filter.py` | CsvFilterTest | |
| `tests/test_for_tool.py` | ForToolTest | |
| `tests/test_generic.py` | GenericApplicationTest | uses `_configfile`/`_objectsdir` class attrs AND explicit `setUpConfig` calls in each method — remove the class-level `_configfile`/`_objectsdir` only if the per-method calls differ; otherwise unify |
| `tests/test_logging.py` | LoggingTest | |

Apply the full golden-template checklist from TASK-002. One commit per file.

---

## TASK-006 — Refactor batch E: three 2-test files

**Status**: pending
**Depends on**: TASK-001

Files:

| File | New class |
|------|-----------|
| `tests/test_macros.py` | MacrosTest |
| `tests/test_pushgateway.py` | PushgatewayTest |
| `tests/test_snmptt.py` | SnmpttTest |

Apply the full golden-template checklist from TASK-002. One commit per file.

---

## TASK-007 — Refactor `tests/test_bin.py`

**Status**: pending
**Depends on**: TASK-001

3 tests. Class → `BinTest`.

Specific issues to address:
- Add module docstring: tests for the `coshsh-cook` CLI entry point.
- Each method tests a distinct invocation of the binary; make the docstring reflect the
  invocation being tested (e.g. `"""coshsh-cook with a valid cookbook produces output files."""`).
- Check for `assertTrue(x == y)` patterns and replace with `assertEqual`.
- Remove any `print()` calls.

Commit: `tests: refactor test_bin.py → BinTest`

---

## TASK-008 — Refactor `tests/test_contacts.py`

**Status**: pending
**Depends on**: TASK-001

3 tests. Class → `ContactsTest`.

Specific issues to address:
- Add module docstring: tests for Contact class factory and contact_name derivation.
- Replace `assertTrue(x == y)` with `assertEqual(x, y)`.
- Remove any `print()` calls.

Commit: `tests: refactor test_contacts.py → ContactsTest`

---

## TASK-009 — Refactor `tests/test_delta.py`  *(special: extract git helper)*

**Status**: pending
**Depends on**: TASK-001

3 tests (`test_growing_hosts`, `test_grow_grow_ok`, `test_grow_shrink_nok`), all very
long. This is the most complex refactoring task.

Class → `DeltaTest`.

Specific issues to address:

1. **Extract git helper**: all three tests contain an identical 8-line block:
   ```python
   os.chdir('./var/objects/testNN/dynamic')
   process = Popen(["git", "init", "."], ...)
   ...
   process = Popen(["git", "add", "."], ...)
   ...
   process = Popen(["git", "commit", "-a", "-m", "commit init"], ...)
   os.chdir(save_dir)
   ```
   Extract this to a private method `_git_commit_initial(self, objects_dir)` on
   `DeltaTest`. The method must not use `os.chdir` — use `cwd=` in `Popen` instead.
   Import `subprocess` at top level; remove `from subprocess import Popen, PIPE, STDOUT`.

2. **Rename test methods** to express the scenario rather than the mechanism:
   - `test_growing_hosts` → `test_delta_exceeded_on_growth_aborts_new_files`
   - `test_grow_grow_ok` → `test_delta_not_exceeded_when_threshold_allows_growth`
   - `test_grow_shrink_nok` → `test_delta_exceeded_on_shrink_restores_old_files`

3. **Add docstrings** to each method (one sentence).

4. **Replace `assertTrue(x == y)`** with `assertEqual(x, y)`.

5. **Remove `print()` calls**.

6. **Split assertions**: each test currently mixes "state after first run" and "state
   after second run" assertions. This is acceptable — do not split the tests
   themselves, but add a blank line + inline comment `# --- second run ---` to
   clearly mark the boundary.

Commit: `tests: refactor test_delta.py → DeltaTest, extract _git_commit_initial`

---

## TASK-010 — Refactor `tests/test_dest.py`

**Status**: pending
**Depends on**: TASK-001

3 tests. Class → `DatarecipientTest`.

Specific issues to address:
- Add module docstring: tests for Datarecipient class factory and fallback behaviour.
- Replace `assertTrue(x == y)` with `assertEqual(x, y)`.
- Remove any `print()` calls.

Commit: `tests: refactor test_dest.py → DatarecipientTest`

---

## TASK-011 — Refactor `tests/test_rcp_logs.py`

**Status**: pending
**Depends on**: TASK-001

3 tests. Class → `RecipeLogsTest`.

Specific issues to address:
- Add module docstring: tests for recipe-level log file handling.
- Replace `assertTrue(x == y)` with `assertEqual(x, y)`.
- Remove any `print()` calls.

Commit: `tests: refactor test_rcp_logs.py → RecipeLogsTest`

---

## TASK-012 — Refactor `tests/test_recipeattrs.py`

**Status**: pending
**Depends on**: TASK-001

3 tests. Class → `RecipeAttrsTest`.

Specific issues to address:
- Add module docstring: tests for recipe configuration attribute parsing.
- Replace `assertTrue(x == y)` with `assertEqual(x, y)`.
- Remove any `print()` calls.

Commit: `tests: refactor test_recipeattrs.py → RecipeAttrsTest`

---

## TASK-013 — Refactor `tests/test_recex.py`

**Status**: pending
**Depends on**: TASK-001

4 tests. Class → `RecexTest`.

Specific issues to address:
- Add module docstring: tests for recipe exception / error handling paths.
- Replace `assertTrue(x == y)` with `assertEqual(x, y)`.
- Remove any `print()` calls.

Commit: `tests: refactor test_recex.py → RecexTest`

---

## TASK-014 — Refactor `tests/test_application_mysql.py`

**Status**: pending
**Depends on**: TASK-001

4 tests. Class → `ApplicationMysqlTest`.

Specific issues to address:
- Add module docstring: tests for the MySQL application class, hostgroup assignment,
  and port configuration.
- Replace `assertTrue(x == y)` with `assertEqual(x, y)`.
- Remove any `print()` calls.
- Check for and remove duplicate import lines.

Commit: `tests: refactor test_application_mysql.py → ApplicationMysqlTest`

---

## TASK-015 — Refactor `tests/test_classes.py`

**Status**: pending
**Depends on**: TASK-001

8 tests. Class → `ClassFactoryTest`. This is the largest conceptual cluster: it tests
the class factory mechanism, path resolution, and env-var interpolation.

Specific issues to address:
- Add module docstring: tests for the class factory loading mechanism — path
  resolution, environment variable interpolation, and datasource/application class
  selection.
- Add docstrings to every method (one sentence each).
- Replace `assertTrue(x == y)` with `assertEqual(x, y)`.
  Notable: `assertTrue(os.path.abspath(...) == ...)` → `assertEqual(os.path.abspath(...), ...)`.
- Replace `assertTrue([a, b] == [c, d])` with `assertEqual([a, b], [c, d])`.
- Remove any `print()` calls.
- `test_ds_handshake`: contains a bare `fail(...)` call that should be
  `self.fail(...)`.

Commit: `tests: refactor test_classes.py → ClassFactoryTest`

---

## TASK-016 — Refactor `tests/test_details.py`

**Status**: pending
**Depends on**: TASK-001

6 tests. Class → `MonitoringDetailTest`.

Specific issues to address:
- Add module docstring: tests for MonitoringDetail subtype behaviour — KEYVALUES,
  KEYVALUEARRAYS, URL parsing, RAM thresholds, and lazy datasource attribute merging.
- Add docstrings to every method (one sentence each).
- Replace `assertTrue(x == y)` with `assertEqual(x, y)`.
- `test_detail_2url`: contains a large commented-out block (`#coshsh.application...`).
  Remove it entirely — it is dead code.
- `test_detail_2url`: the `for line in outfile.read().split('\n'): print(line)` block
  at the end is debug output; remove it.
- Remove all other `print()` calls.

Commit: `tests: refactor test_details.py → MonitoringDetailTest`

---

## TASK-017 — Refactor `tests/test_git.py`

**Status**: pending
**Depends on**: TASK-001

4 tests. Class → `GitOutputTest`.

Specific issues to address:
- Add module docstring: tests for git-based output directory initialisation and commit
  behaviour.
- Add docstrings to every method.
- Replace `assertTrue(x == y)` with `assertEqual(x, y)`.
- Remove any `print()` calls.

Commit: `tests: refactor test_git.py → GitOutputTest`

---

## TASK-018 — Refactor `tests/test_package.py`

**Status**: pending
**Depends on**: TASK-001

6 tests. Class → `PackageTest`.

Specific issues to address:
- Add module docstring: tests for Host, Application, Contact, and HostGroup object
  creation and default attribute values.
- Add docstrings to every method.
- `test_create_application` is defined **twice** (duplicate method name — Python silently
  keeps only the last one). Rename the first to `test_create_application_default_class`
  and ensure both docstrings are distinct. Verify both still pass after renaming.
- Replace `assertTrue(x == y)` with `assertEqual(x, y)`.
- Remove any `print()` calls.

Commit: `tests: refactor test_package.py → PackageTest, fix duplicate method name`

---

## TASK-019 — Refactor `tests/test_pid.py`

**Status**: pending
**Depends on**: TASK-001

8 tests. Class → `PidTest`. This is one of the most complex test files.

Specific issues to address:
- Add module docstring: tests for recipe PID-file protection — creation, stale PID
  detection, active PID blocking, garbled file handling, empty file handling, and
  unwritable directory detection.
- Add docstrings to every method (one sentence).
- Replace `assertTrue(x == y)` with `assertEqual(x, y)`.
  Notable: `assertTrue(pid == str(os.getpid()))` → `assertEqual(pid, str(os.getpid()))`.
- Replace `assertTrue(exp.__class__.__name__ == "RecipePidAlreadyRunning")` with
  `assertIsInstance(exp, RecipePidAlreadyRunning)` — but only if the exception class is
  importable. If not, `assertEqual(exp.__class__.__name__, "RecipePidAlreadyRunning")`
  is acceptable.
- Replace bare `fail(...)` calls with `self.fail(...)`.
- Remove all `print()` calls.
- The `tearDown` override calls `super().tearDown()` correctly — leave it.

Commit: `tests: refactor test_pid.py → PidTest`

---

## TASK-020 — Refactor `tests/test_recipes.py`

**Status**: pending
**Depends on**: TASK-001

7 tests. Class → `RecipesTest`. This file covers the widest range of recipe
behaviours.

Specific issues to address:
- Add module docstring: integration tests for recipe execution — multi-source
  collection, delta protection, template errors, environment variable expansion,
  max_delta configuration parsing, and git initialisation.
- Add docstrings to every method (one sentence).
- Replace `assertTrue(x == y)` with `assertEqual(x, y)`.
  Notable: `assertTrue([f.path for f in ...] == ['C','D','F','G','Z'])` →
  `assertEqual([f.path for f in ...], ['C', 'D', 'F', 'G', 'Z'])`.
- Replace `assertTrue(not x)` with `assertFalse(x)`.
- `test_create_recipe_multiple_sources`: has a large inline comment block explaining
  what each step does. These are good — keep the section comments, but prune any that
  just restate the code (e.g. `# write hosts/apps to the filesystem` above
  `r.output()` is worth keeping; `# remove target dir / create empty` above
  `r.count_before_objects()` is obvious — remove).
- Remove all `print()` calls.

Commit: `tests: refactor test_recipes.py → RecipesTest`

---

## TASK-021 — Refactor `tests/test_vault.py`

**Status**: pending
**Depends on**: TASK-001

5 tests. Class → `VaultTest`.

Specific issues to address:
- Add module docstring: tests for vault/secrets integration — file opening, password
  validation, production vs non-production mode, and missing file handling.
- Add docstrings to every method (one sentence).
- Replace `assertTrue(x == y)` with `assertEqual(x, y)`.
- Replace bare `assertTrue(not x)` with `assertFalse(x)`.
- Remove any `print()` calls.

Commit: `tests: refactor test_vault.py → VaultTest`

---

## TASK-022 — Final verification

**Status**: pending
**Depends on**: TASK-002 through TASK-021

Run the full suite and confirm every acceptance criterion from the spec is met.

Steps:
1. `python -m pytest tests/ -v --tb=short`
   - Collected count must match baseline (98).
   - Passed count must match baseline (≥97).
   - Only `test_datasource_attributes_in_tpl` is permitted as a failure, if it was
     already failing at baseline.
2. Verify no `CoshshTest` class name remains in any test file:
   `grep -r "class CoshshTest" tests/`  → must return nothing.
3. Verify no bare `print(` remains in any test file:
   `grep -rn "^\s*print(" tests/test_*.py` → must return nothing.
4. Verify no `assertTrue.*==` remains (quick heuristic):
   `grep -n "assertTrue.*==" tests/test_*.py` → must return nothing.
5. Verify every test file has a module docstring:
   `python -c "import ast, sys, glob; [sys.exit(1) for f in glob.glob('tests/test_*.py') if not ast.get_docstring(ast.parse(open(f).read()))]"`
   → must exit 0.
6. If all checks pass, commit:
   `tests: 002-refactor-tests-for-ai — all files refactored, suite green`
