# Spec 005 — Performance Optimization of the 4-Phase Pipeline

**Branch:** `master`
**Date:** 2026-02-28
**Status:** FINISHED (2026-02-28)
**Baseline:** 205 tests passing (after specs 002-004)
**Final:** 205 tests passing, 0 warnings

---

## Goal

Identify and eliminate algorithmic bottlenecks, redundant work, and wasteful patterns
in the core 4-phase pipeline (collect -> assemble -> render -> output). All
optimizations must preserve the existing 205-test suite and maintain code readability
established by spec 004.

---

## Scope

Changes confined to 5 core files in `coshsh/` and 1 test file:

| File | Changes |
|------|---------|
| `coshsh/item.py` | Pre-compiled regex, depythonize hoist, O(n^2) dedup fix |
| `coshsh/recipe.py` | Bug fix, itertools.chain, setdefault, flat counting, broadcast fix, getattr elimination |
| `coshsh/templaterule.py` | Pre-compile regex in `__init__` |
| `coshsh/datainterface.py` | dict.get() for usage counter |
| `coshsh/datasource.py` | dict membership test for add() |
| `tests/test_recipes.py` | Updated test from asserting TypeError to asserting correct behavior |

---

## Bottlenecks Identified (ranked by impact)

| # | Bottleneck | File | Complexity | Impact |
|---|-----------|------|-----------|--------|
| 1 | depythonize/pythonize called per template rule instead of per object | item.py | O(K*9) per object | **Critical** |
| 2 | O(n^2) dedup in resolve_monitoring_details + O(n) list.remove per detail | item.py | O(n^2) | **High** |
| 3 | re.match() without pre-compilation in template rule loop | item.py + templaterule.py | 50K+ compiles | **High** |
| 4 | Generic detail broadcast with list.insert(0,...) which is O(M) per insert | recipe.py | O(G*N*M) | **Medium-High** |
| 5 | Triple-nested list comprehension for detail counting | recipe.py | O(all objects) x4 | **Medium** |
| 6 | sum([], []) O(n^2) list concatenation in render | recipe.py | O(n^2) | **Medium** |
| 7 | Exception-as-flow-control in hot paths | multiple | overhead per call | **Low-Medium** |
| 8 | Redundant getattr() in assemble sort loop | recipe.py | 2x per attr | **Low-Medium** |
| 9 | Bug: count_after_objects sum() args reversed | recipe.py:568 | crash | **Bug fix** |

---

## Latent Bug Fixed

| ID | Location | Bug | Fix |
|----|----------|-----|-----|
| BUG-2 | `recipe.py:568` | `sum(0, [list])` args reversed; raises `TypeError` | `sum([list], 0)` — matches `count_before_objects` pattern |

This bug was originally discovered and documented (but not fixed) in spec 003.

---

## User Scenarios & Testing

### User Story 1 - Pipeline Runs Faster on Large Datasets (Priority: P1)

A coshsh operator running a recipe with 1000+ hosts and many applications observes
faster wall-clock times because:
- Regex is compiled once per TemplateRule instead of once per match attempt
- depythonize/pythonize runs once per object instead of once per template rule
- Monitoring detail resolution is O(n) instead of O(n^2)
- Generic detail broadcast uses O(1) prepend instead of O(M) per insert

**Acceptance**: All 205 tests pass with identical output.

### User Story 2 - count_after_objects() No Longer Crashes (Priority: P1)

The `count_after_objects()` method can now be called without raising a `TypeError`.
This was a latent bug that prevented the delta-safety mechanism from working in
any recipe that used multiple datarecipients.

**Acceptance**: Test `test_recipe_count_after_objects_works` passes.

### User Story 3 - External Callers of render_cfg_template() Unaffected (Priority: P1)

Any external code that calls `render_cfg_template()` directly (outside of `render()`)
continues to work identically. The depythonize/pythonize hoisting uses a
`_skip_pythonize` parameter that defaults to `False`, preserving backward compatibility.

**Acceptance**: All 205 tests pass.

---

## Changes by Phase

### Phase 1: Quick Wins (low risk, mechanical)

1. **1A** Fixed `count_after_objects` bug: `sum(0, [...])` -> `sum([...], 0)`
2. **1B** Replaced `sum([], [])` with `itertools.chain.from_iterable()` in render()
3. **1C** Replaced try/except with `if objtype not in self.objects` in datasource.add()
4. **1D** Replaced try/except with `dict.get(key, 0) + 1` in datainterface.get_class()
5. **1E** Replaced try/except with `setdefault(hostgroup, []).append()` in assemble()
6. **1F** Simplified triple-nested list comprehension to flat generator in collect()

### Phase 2: Core Algorithmic Improvements (high impact)

7. **2A** Pre-compiled regex in `TemplateRule.__init__` (`self._isattr_re`); used `rule._isattr_re.match()` and `any()` for early exit in `Item.render()`
8. **2B** Hoisted `depythonize()` to start of `render()`, `pythonize()` to end; added `_skip_pythonize` parameter to `render_cfg_template()` for backward compatibility
9. **2C** Replaced O(n) `self.monitoring_details.remove(detail)` per iteration with single `.clear()` after loop; replaced O(n) list rebuild for unique_attribute dedup with in-place `prop_list[i] = detail`; replaced try/except with direct attribute checks

### Phase 3: Structural Optimizations (more code touched)

10. **3A** Replaced per-detail `insert(0, detail)` O(M) inserts with collecting all generics first, then single list concatenation per object
11. **3B** Replaced `for k in dict.keys()` + `isinstance(getattr(...))` + `getattr(...).sort()` with `for k, v in dict.items()` eliminating double attribute access
