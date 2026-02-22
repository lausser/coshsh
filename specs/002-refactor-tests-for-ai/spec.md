# Feature Specification: Refactor Tests for AI Readability

**Feature Branch**: `002-refactor-tests-for-ai`
**Created**: 2026-02-21
**Status**: Draft

## Context

Coshsh has 98 tests spread across 43 test files written over several years by multiple
contributors. The tests are functionally correct — they cover the generator, recipe,
datasource, application, monitoring detail, and output layers — but they were written
without a shared style guide or structural convention. The result is heterogeneous code
that is hard for AI agents to reason about: different patterns for setup, different
assertion styles, inconsistent naming, embedded comments that describe process rather
than intent, and test methods grouped by accident rather than by design.

The **human-written production code is the oracle**. No production code changes are in
scope for this feature. All refactoring is confined to the `tests/` directory.

The goal is a test suite that an AI agent (or a new human contributor) can read with
confidence: knowing immediately what a test covers, why it passes or fails, and where
in the system to look when it fails.

---

## Objectives

1. **Homogeneous structure** — every test file and every test method follows the same
   skeleton. No cognitive overhead from switching styles.
2. **Intent-revealing names** — test method names describe the behaviour under test,
   not the implementation mechanism. `test_recipe_exceeds_max_delta_aborts_output` is
   better than `test_growing_hosts`.
3. **Lean setup** — each test class declares exactly what it needs via
   `_configfile` / `_objectsdir` class attributes or explicit `mySetUp`. No
   redundant `setUpConfig` calls that duplicate the class-level declaration.
4. **Single assertion focus** — each test method covers one logical scenario.
   A 120-line test method with fifteen assertions should be split into multiple
   focused tests where each can fail independently with a clear message.
5. **Consistent assertion style** — use `assertEqual`, `assertIn`, `assertTrue`,
   `assertFalse`, `assertIsNone`, `assertIsNotNone`, `assertRaises` throughout.
   Drop bare `assertTrue(x == y)` in favour of `assertEqual(x, y)`.
6. **No debug artefacts** — remove `print()` statements, commented-out code, and
   TODO comments that were never resolved.
7. **Explicit imports** — each test file imports only what it uses. No unused imports.
8. **Grouped by concern** — tests within a file are ordered from simple to complex,
   and files are named after the coshsh component they test, not after the recipe
   number they happen to use.

---

## Non-Goals

- **No production code changes.** `coshsh/` is read-only throughout this feature.
- **No new test coverage.** The refactoring must not add scenarios that do not
  already exist; the 98 passing tests remain the only passing set after refactoring
  (with the known pre-existing failure `test_datasource_attributes_in_tpl` excluded).
- **No test infrastructure changes.** `tests/common_coshsh_test.py` may receive
  minor cleanup (unused imports, duplicate `print_header` definition) but its
  public API — `setUp`, `tearDown`, `setUpConfig`, `setUpObjectsDir`,
  `clean_generator` — must remain unchanged.
- **No recipe or fixture changes.** Files under `tests/recipes/`,
  `tests/etc/`, `tests/var/` are out of scope unless a test file contains an
  obvious bug (e.g. wrong path string) that is masking a real failure.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — AI Agent Reads a Failing Test (Priority: P1)

An AI agent is given a failing test and must determine whether the failure indicates
a regression in production code or a mistake in the test itself, without running any
code.

**Acceptance Scenario**:
Given a test method whose name is `test_recipe_collects_two_datasources`, the agent
can immediately locate the relevant production class (`Recipe`), understand the
assertion (`two hosts from two datasources appear in `recipe.objects`), and decide
whether a change to `datasource.py` is likely to explain the failure.

### User Story 2 — AI Agent Adds a New Test (Priority: P1)

An AI agent is asked to write a test for a new behaviour. It reads the existing test
file for the relevant component and understands the pattern well enough to produce a
correct, passing test without a human review cycle.

**Acceptance Scenario**:
Given the task "add a test proving that a recipe with `safe_output=True` does not
overwrite the existing output directory when no objects are collected", the agent
reads `tests/test_recipes.py`, identifies the correct setup pattern, and writes a
test that passes on the first try.

### User Story 3 — New Contributor Orientation (Priority: P2)

A human contributor opens the test suite for the first time. Within five minutes they
understand: which file to look in for a given behaviour, how test setup works, and
what the assertion failures mean.

---

## Structural Standard (the golden template)

Every refactored test file must conform to this structure:

```python
"""
Tests for <ComponentName> — <one sentence description of what is covered>.
"""
import os
# ... only used imports ...
from tests.common_coshsh_test import CommonCoshshTest


class <ComponentName>Test(CommonCoshshTest):
    """<Optional class docstring for multi-scenario files.>"""

    # --- class-level fixtures (if uniform across all methods) ---
    _configfile = "etc/coshsh.cfg"
    _objectsdir = "./var/objects/testNN"

    # --- tests ordered from simple to complex ---

    def test_<behaviour_under_test>(self):
        """<One sentence: what this test proves.>"""
        # arrange
        ...
        # act
        ...
        # assert
        self.assertEqual(expected, actual)
```

Rules:
- Class name: `<ComponentName>Test` (e.g. `RecipeTest`, `DeltaTest`, `VaultTest`).
  The legacy `CoshshTest` name is replaced everywhere.
- Module docstring: present and meaningful.
- Arrange / Act / Assert sections: separated by blank lines; inline comments only
  where the intent is non-obvious.
- No `print()` calls.
- Assertion methods: prefer the specific form (`assertEqual`, `assertIn`, etc.) over
  the generic `assertTrue(x == y)`.

---

## File Mapping

The following table maps current filenames to their refactored name and class name.
Files whose scope is already clear keep their name.

| Current file              | Refactored name           | Class name              |
|---------------------------|---------------------------|-------------------------|
| test_application_mysql.py | test_application_mysql.py | ApplicationMysqlTest    |
| test_attrstrip.py         | test_attrstrip.py         | AttrStripTest           |
| test_bin.py               | test_bin.py               | BinTest                 |
| test_catchall.py          | test_catchall.py          | CatchallTest            |
| test_classes.py           | test_classes.py           | ClassFactoryTest        |
| test_contacts.py          | test_contacts.py          | ContactsTest            |
| test_csv_filter.py        | test_csv_filter.py        | CsvFilterTest           |
| test_datainterface.py     | test_datainterface.py     | DatainterfaceTest       |
| test_delta.py             | test_delta.py             | DeltaTest               |
| test_dest.py              | test_dest.py              | DatarecipientTest       |
| test_details.py           | test_details.py           | MonitoringDetailTest    |
| test_extensions.py        | test_extensions.py        | ExtensionsTest          |
| test_for_tool.py          | test_for_tool.py          | ForToolTest             |
| test_generic.py           | test_generic.py           | GenericApplicationTest  |
| test_git.py               | test_git.py               | GitOutputTest           |
| test_host_attributes.py   | test_host_attributes.py   | HostAttributesTest      |
| test_inheritance.py       | test_inheritance.py       | InheritanceTest         |
| test_logging.py           | test_logging.py           | LoggingTest             |
| test_macros.py            | test_macros.py            | MacrosTest              |
| test_merge.py             | test_merge.py             | MergeTest               |
| test_myjinja.py           | test_myjinja.py           | MyJinjaTest             |
| test_nagiosconf.py        | test_nagiosconf.py        | NagiosconfTest          |
| test_obdir_paths.py       | test_obdir_paths.py       | ObdirPathsTest          |
| test_order.py             | test_order.py             | OrderTest               |
| test_package.py           | test_package.py           | PackageTest             |
| test_pid.py               | test_pid.py               | PidTest                 |
| test_pushgateway.py       | test_pushgateway.py       | PushgatewayTest         |
| test_rcp_logs.py          | test_rcp_logs.py          | RecipeLogsTest          |
| test_recex.py             | test_recex.py             | RecexTest               |
| test_recipeattrs.py       | test_recipeattrs.py       | RecipeAttrsTest         |
| test_recipes.py           | test_recipes.py           | RecipesTest             |
| test_regex_filters.py     | test_regex_filters.py     | RegexFiltersTest        |
| test_snmptt.py            | test_snmptt.py            | SnmpttTest              |
| test_suffix.py            | test_suffix.py            | SuffixTest              |
| test_timeperiod.py        | test_timeperiod.py        | TimeperiodTest          |
| test_vault.py             | test_vault.py             | VaultTest               |

---

## Acceptance Criteria

1. `python -m pytest tests/` passes with the same count as before this feature
   (98 collected, ≥97 passing — `test_datasource_attributes_in_tpl` is the single
   known pre-existing failure and may remain).
2. Every test class is named `<Component>Test`, not `CoshshTest`.
3. Every test file has a module-level docstring.
4. No test method contains bare `print()` calls.
5. No test method uses `assertTrue(x == y)` — replaced by `assertEqual(x, y)`.
6. Every test method has a one-line docstring.
7. No unused imports in any test file.
8. `common_coshsh_test.py` retains its public API unchanged; the duplicate
   `print_header` method definition is removed.
9. All changes are committed atomically per file (one commit per test file).

---

## Out of Scope / Risks

- **Large test methods** (e.g. `test_growing_hosts`, `test_create_recipe_multiple_sources`):
  splitting these into multiple focused tests is desirable but must not change what
  is covered. Split only when the split does not require new fixtures or recipe data.
- **test_delta.py git subprocess calls**: the repeated Popen git blocks are
  implementation noise; they should be extracted into a private helper
  `_commit_objects_dir(path)` within `DeltaTest`.
- **Pre-existing failure**: `test_datasource_attributes_in_tpl` — do not touch; do
  not mark as expected failure (xfail) unless the user explicitly requests it.
