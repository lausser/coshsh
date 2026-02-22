# Tasks: 003-add-missing-tests

Generated: 2026-02-22
Baseline: 100 collected, 100 passed, 0 failed
Final: 205 collected, 205 passed, 0 failed (+105 new tests)
Spec: specs/003-add-missing-tests/spec.md
Branch: 003-add-missing-tests

## Dependency Order

```
TASK-000  Record baseline
  └─ TASK-001  tests/test_util.py (NEW, no coshsh setup needed)
     TASK-002  tests/test_dependency.py (NEW, trivial)
     TASK-003  tests/test_templaterule.py (NEW, trivial)
     TASK-004  tests/test_contactgroup.py (NEW, trivial)
     TASK-005  tests/test_configparser.py (NEW, tempfile-based)
     TASK-006  tests/test_host.py (NEW, includes BUG-1)
     TASK-007  tests/test_item.py (NEW, largest file, includes BUG-3a)
     TASK-008  tests/test_jinja2_extensions.py (NEW)
     TASK-009  tests/test_datasource.py (NEW, needs recipe fixture)
     TASK-010  tests/test_datarecipient.py (NEW, needs recipe fixture)
     TASK-011  tests/test_details.py (EXTEND, includes BUG-3b)
     TASK-012  tests/test_merge.py (EXTEND)
     TASK-013  tests/test_recipes.py (EXTEND, includes BUG-2)
     TASK-014  tests/test_vault.py (EXTEND)
     TASK-015  tests/test_contacts.py (EXTEND)
     TASK-016  tests/test_generic.py (EXTEND)
     TASK-017  tests/test_package.py (EXTEND)
     TASK-018  tests/test_delta.py (EXTEND)
       └─ (all above) → TASK-019 (final verification)
                         └─ TASK-020 (fix DeprecationWarning in filter_re_sub)
```

---

## TASK-000 — Record baseline

**Status**: done
**Depends on**: —

Run the full test suite and record the exact numbers before any changes.

Steps:
1. `python -m pytest tests/ -v --tb=short 2>&1 | tee /tmp/coshsh_003_baseline.txt`
2. Confirm 100 collected, 100 passed, 0 failed.
3. Update the baseline numbers at the top of this file if different.

Acceptance: baseline recorded; no code touched.

---

## TASK-001 — `tests/test_util.py` (NEW)

**Status**: done
**Depends on**: TASK-000
**Spec section**: 5
**Tests**: 5a–5m (~13 tests)

Create `tests/test_util.py` with class `UtilTest(unittest.TestCase)`.
Module docstring: `"""Tests for coshsh.util helper functions."""`

Tests cover:
- `compare_attr` (equal, not-equal)
- `is_attr` (present, absent)
- `cleanout` (directory cleaning)
- `normalize_dict` (key normalisation, two variants)
- `clean_umlauts` (German umlaut replacement)
- `sanitize_filename` (three variants: spaces, slashes, clean input)
- `odict` (ordered dict behaviour, two variants)
- `substenv` (environment variable substitution)

Note: These are pure utility functions — no CommonCoshshTest or recipe setup needed.
Use `unittest.TestCase` directly.

Acceptance: all new tests pass; `python -m pytest tests/test_util.py -v` green.

---

## TASK-002 — `tests/test_dependency.py` (NEW)

**Status**: done
**Depends on**: TASK-000
**Spec section**: 4
**Tests**: 4a–4c (3 tests)

Create `tests/test_dependency.py` with class `DependencyTest(unittest.TestCase)`.
Module docstring: `"""Tests for Dependency object construction and attribute access."""`

Tests cover:
- Construction stores `host_name` and `parent_host_name`
- `Dependency` is NOT a subclass of `Item`
- Missing key raises `KeyError` (or similar)

Acceptance: `python -m pytest tests/test_dependency.py -v` green.

---

## TASK-003 — `tests/test_templaterule.py` (NEW)

**Status**: done
**Depends on**: TASK-000
**Spec section**: 14
**Tests**: 14a–14c (3 tests)

Create `tests/test_templaterule.py` with class `TemplateRuleTest(unittest.TestCase)`.
Module docstring: `"""Tests for TemplateRule construction and default attributes."""`

Tests cover:
- Default attributes (`suffix='cfg'`, `for_tool='nagios'`, etc.)
- Custom attributes passed through constructor
- `str()` representation contains key fields

Acceptance: `python -m pytest tests/test_templaterule.py -v` green.

---

## TASK-004 — `tests/test_contactgroup.py` (NEW)

**Status**: done
**Depends on**: TASK-000
**Spec section**: 15
**Tests**: 15a–15b (2 tests)

Create `tests/test_contactgroup.py` with class `ContactGroupTest(unittest.TestCase)`.
Module docstring: `"""Tests for ContactGroup construction and fingerprint."""`

Tests cover:
- Construction, `fingerprint()`, default `members == []`
- `str()` representation

Acceptance: `python -m pytest tests/test_contactgroup.py -v` green.

---

## TASK-005 — `tests/test_configparser.py` (NEW)

**Status**: done
**Depends on**: TASK-000
**Spec section**: 3
**Tests**: 3a–3e (5 tests)

Create `tests/test_configparser.py` with class `CoshshConfigParserTest(unittest.TestCase)`.
Module docstring: `"""Tests for CoshshConfigParser — isa section inheritance."""`

Tests cover:
- Child section inherits missing keys from parent via `isa`
- `isa` key itself is not copied to child
- Missing parent section leaves child unchanged
- Section without `isa` is unaffected
- `isa` is one-level only (no transitive inheritance)

Use `tempfile` to create temporary INI files for each test.

Acceptance: `python -m pytest tests/test_configparser.py -v` green.

---

## TASK-006 — `tests/test_host.py` (NEW)

**Status**: done
**Depends on**: TASK-000
**Spec section**: 1
**Tests**: 1a–1i (9 tests, one is BUG-1)

Create `tests/test_host.py` with class `HostTest(CommonCoshshTest)`.
Module docstring: `"""Tests for Host construction, attribute normalisation, and is_correct() validation."""`

Tests cover:
- `lower_columns` normalisation (`os`, `hardware`, `type` lowered)
- Non-string lower_column set to `None`
- `alias` defaults to `host_name` when absent
- `alias` preserved when supplied
- Default `ports == [22]`
- **[BUG-1]** `is_correct()` raises `TypeError` (mark with `@unittest.expectedFailure` or `assertRaises`)
- `fingerprint()` returns host_name
- Default empty collections (`hostgroups`, `contacts`, etc.)
- `macros` defaults to empty dict

Acceptance: all tests pass (BUG-1 test expected to demonstrate the bug).

---

## TASK-007 — `tests/test_item.py` (NEW)

**Status**: done
**Depends on**: TASK-000
**Spec section**: 2
**Tests**: 2a–2q (17 tests, one is BUG-3a)

Create `tests/test_item.py` with class `ItemTest(CommonCoshshTest)`.
Module docstring: `"""Tests for Item base class: init, pythonize/depythonize, resolve_monitoring_details, render, and chronicle."""`

This is the largest new file. Tests cover:
- `pythonize()` splits comma-separated strings
- `depythonize()` joins lists, deduplicates, sorts
- `pythonize`/`depythonize` roundtrip
- Template order preserved by `depythonize`
- `resolve_monitoring_details` with `unique_attribute` deduplication (same/different values)
- `resolve_monitoring_details` with `property_attr`
- `resolve_monitoring_details` with `property_flat`
- `resolve_monitoring_details` generic scalar and list
- `record_in_chronicle` appends entries, ignores empty
- `dont_strip_attributes` bool=True and list variants
- `fingerprint()` fallback to host_name
- **[BUG-3a]** `fingerprint()` raises `TypeError` on missing all fields

Note: For `resolve_monitoring_details` tests, create minimal stub subclasses with
the required class attributes (`property`, `property_type`, `unique_attribute`, etc.).

Acceptance: all tests pass (BUG-3a test expected to demonstrate the bug).

---

## TASK-008 — `tests/test_jinja2_extensions.py` (NEW)

**Status**: done
**Depends on**: TASK-000
**Spec section**: 10
**Tests**: 10a–10p (16 tests)

Create `tests/test_jinja2_extensions.py` with class `Jinja2ExtensionsTest(unittest.TestCase)`.
Module docstring: `"""Tests for coshsh Jinja2 custom filters and helper functions."""`

Tests cover:
- `filter_re_sub` (basic substitution, no match returns original)
- `filter_re_escape` (escapes regex metacharacters)
- `get_re_flags` (flags string to int, empty string)
- `filter_custom_macros` (dict to Nagios macro format, empty dict)
- `filter_rfc3986` (encodes text)
- `is_re_match` (true/false/with flags)
- `filter_host` (basic output format)
- `filter_neighbor_applications` (returns host's app list)
- `global_environ` (reads env var, default when missing, empty string when missing no default)

Note: `filter_host` and `filter_neighbor_applications` need stub objects.

Acceptance: `python -m pytest tests/test_jinja2_extensions.py -v` green.

---

## TASK-009 — `tests/test_datasource.py` (NEW)

**Status**: done
**Depends on**: TASK-000
**Spec section**: 16
**Tests**: 16a–16g (7 tests)

Create `tests/test_datasource.py` with class `DatasourceUnitTest(CommonCoshshTest)`.
Module docstring: `"""Unit tests for Datasource.add(), find(), get(), and host linking."""`

Uses a concrete datasource from a test recipe (e.g., `coshsh.cfg` / `test1`).

Tests cover:
- `add()` host stores by fingerprint; `find()` and `get()` retrieve it
- `add()` application links `app.host` to existing host
- `add()` records in chronicle
- `get()` returns `None` for missing fingerprint
- `find()` returns `False` for missing
- `getall()` returns all objects of a type
- `getall()` returns empty list for unknown type

Acceptance: `python -m pytest tests/test_datasource.py -v` green.

---

## TASK-010 — `tests/test_datarecipient.py` (NEW)

**Status**: done
**Depends on**: TASK-000
**Spec section**: 6
**Tests**: 6a–6h (8 tests)

Create `tests/test_datarecipient.py` with class `DatarecipientUnitTest(CommonCoshshTest)`.
Module docstring: `"""Unit tests for Datarecipient helper methods: too_much_delta(), count_objects()."""`

Tests cover:
- `too_much_delta()` — below threshold, above threshold, zero threshold (disabled),
  empty counts, None threshold, percentage-based
- `count_objects()` — counting hosts/apps, empty recipe

Acceptance: `python -m pytest tests/test_datarecipient.py -v` green.

---

## TASK-011 — `tests/test_details.py` (EXTEND)

**Status**: done
**Depends on**: TASK-000
**Spec section**: 8
**Tests**: 8a–8f (6 new tests, one is BUG-3b)

Add to existing `MonitoringDetailTest` class.

Tests cover:
- Comparison operators (`<`, `==`, `!=`, `>`, `<=`, `>=`)
- Fingerprint uniqueness per instance
- `application_fingerprint()` host-level (no app info)
- `application_fingerprint()` app-level (with app info)
- **[BUG-3b]** `application_fingerprint()` raises `TypeError` on no host
- `__repr__` format

Acceptance: all existing + new tests pass (BUG-3b demonstrates the bug).

---

## TASK-012 — `tests/test_merge.py` (EXTEND)

**Status**: done
**Depends on**: TASK-000
**Spec section**: 9
**Tests**: 9a–9b (2 new tests)

Add to existing `MergeTest` class.

Tests cover:
- `transform_hostname` with `strip_domain` skips IP addresses
- `transform_hostname` with unknown op does not raise

Acceptance: all existing + new tests pass.

---

## TASK-013 — `tests/test_recipes.py` (EXTEND)

**Status**: done
**Depends on**: TASK-000
**Spec section**: 11
**Tests**: 11a–11i (9 new tests, one is BUG-2)

Add to existing `RecipesTest` class.

Tests cover:
- `env_*` key sets `os.environ`
- `get_datasource()` returns `None` for unknown name
- `get_datarecipient()` returns `None` for unknown name
- **[BUG-2]** `count_after_objects()` raises `TypeError`
- `max_delta` parsing with colon split (`'10:20'` → `(10, 20)`)
- `max_delta` parsing single value (`'15'` → `(15, 15)`)
- `assemble()` removes orphaned applications
- `assemble()` creates hostgroup objects
- `collect()` returns `False` on datasource exception

Acceptance: all existing + new tests pass (BUG-2 demonstrates the bug).

---

## TASK-014 — `tests/test_vault.py` (EXTEND)

**Status**: done
**Depends on**: TASK-000
**Spec section**: 12
**Tests**: 12a–12b (2 new tests)

Add to existing `VaultTest` class.

Tests cover:
- `vault.get()` returns `None` for missing key
- `vault.getall()` returns list of all values

Acceptance: all existing + new tests pass.

---

## TASK-015 — `tests/test_contacts.py` (EXTEND)

**Status**: done
**Depends on**: TASK-000
**Spec section**: 13
**Tests**: 13a–13b (2 new tests)

Add to existing `ContactsTest` class.

Tests cover:
- `clean_name()` replaces German umlauts
- Notification period fallback (generic → host/service specific)

Acceptance: all existing + new tests pass.

---

## TASK-016 — `tests/test_generic.py` (EXTEND)

**Status**: done
**Depends on**: TASK-000
**Spec section**: 17
**Tests**: 17a (1 new test)

Add to existing `GenericApplicationTest` class.

Test:
- `GenericApplication.render()` returns `0` and produces no config files when no
  monitoring details are attached.

Acceptance: all existing + new tests pass.

---

## TASK-017 — `tests/test_package.py` (EXTEND)

**Status**: done
**Depends on**: TASK-000
**Spec section**: 18
**Tests**: 18a (1 new test)

Add to existing `PackageTest` class.

Test:
- `Application` lower_columns (`name`, `type`) are normalised to lowercase on construction.

Acceptance: all existing + new tests pass.

---

## TASK-018 — `tests/test_delta.py` (EXTEND)

**Status**: done
**Depends on**: TASK-000
**Spec section**: 7
**Tests**: 7a (1 new test)

Add to existing `DeltaTest` class.

Test:
- `too_much_delta()` boundary: count exactly at threshold returns `False` (not exceeded).

Acceptance: all existing + new tests pass.

---

## TASK-019 — Final verification

**Status**: done
**Depends on**: TASK-001 through TASK-018

Full suite verification.

Steps:
1. `python -m pytest tests/ -v --tb=short 2>&1 | tee /tmp/coshsh_003_final.txt`
2. Confirm all 100 original tests still pass.
3. Count new tests — target is ~83 new tests (exact count may vary based on
   implementation decisions).
4. Confirm BUG tests (BUG-1, BUG-2, BUG-3a, BUG-3b) correctly demonstrate the
   bugs (either via `assertRaises` or `@unittest.expectedFailure`).
5. Verify no `print()` calls, no `assertTrue(x == y)` patterns, no unused imports.
6. Verify `git log --oneline` shows one commit per test file (or per logical group).

Acceptance: all tests pass; total count = 100 + N new; all spec acceptance criteria met.

---

## TASK-020 — Fix DeprecationWarning in `filter_re_sub`

**Status**: done
**Depends on**: TASK-008
**Commit**: `9060716`

Fix Python 3.13 `DeprecationWarning` in `coshsh/jinja2_extensions.py:131`:
change `re.sub(myre, repl, s, count)` → `re.sub(myre, repl, s, count=count)`.

This is a **source code fix**, not a test issue. The keyword form works on all
Python 3.x versions. No change to the Jinja2 filter interface — existing `.tpl`
files are unaffected.

Acceptance: `python -m pytest tests/ -q -W error::DeprecationWarning` passes all 205 tests with zero warnings.

---

## Completion

**Status**: FINISHED
**Date**: 2026-02-22
**Final**: 205 collected, 205 passed, 0 failed, 0 warnings
**Branch**: `003-add-missing-tests`
