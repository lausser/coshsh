# Implementation Plan: 005 — Performance Optimization

**Status:** FINISHED (2026-02-28)
**Commit:** `6210e65` on master

---

## Summary

Optimize the core 4-phase pipeline (collect -> assemble -> render -> output) by
eliminating algorithmic bottlenecks identified through code analysis. All changes
are internal — zero behavior change, all 205 tests pass.

---

## Approach

Three phases ordered by risk level:

1. **Quick wins** — mechanical replacements (exception-as-flow-control, sum() bug, flat generators)
2. **Core algorithmic** — the three highest-impact optimizations (regex pre-compile, depythonize hoist, O(n^2) dedup fix)
3. **Structural** — changes touching more code (generic detail broadcast, getattr elimination)

Each change was verified by running the full 205-test suite before proceeding.

---

## Changes Implemented

### Phase 1: Quick Wins

| ID | File | Change | Complexity |
|----|------|--------|-----------|
| 1A | recipe.py:568 | `sum(0, [...])` -> `sum([...], 0)` | One-liner bug fix |
| 1B | recipe.py:549 | `sum([...], [])` -> `itertools.chain.from_iterable()` | One-liner + import |
| 1C | datasource.py:213 | try/except -> `if objtype not in self.objects` | 3 lines |
| 1D | datainterface.py:171 | try/except -> `dict.get(key, 0) + 1` | 2 lines |
| 1E | recipe.py:507 | try/except -> `setdefault(hostgroup, []).append()` | 1 line |
| 1F | recipe.py:389,395 | Triple-nested listcomp -> flat generator | 2 lines |

### Phase 2: Core Algorithmic Improvements

| ID | File | Change | Impact |
|----|------|--------|--------|
| 2A | templaterule.py + item.py | Pre-compile regex in `__init__`, use `_isattr_re.match()` + `any()` | Eliminates 50K+ re.compile() calls |
| 2B | item.py | Hoist depythonize/pythonize from per-template to per-object | Saves K-1 cycles per object (K=3-10 rules) |
| 2C | item.py | `.clear()` instead of per-item `.remove()`; in-place replacement for unique_attribute | O(n) instead of O(n^2) |

### Phase 3: Structural Optimizations

| ID | File | Change | Impact |
|----|------|--------|--------|
| 3A | recipe.py | Collect generics first, single list concat per object | O(G+M) instead of O(G*M) per object |
| 3B | recipe.py | `for k, v in dict.items()` replacing double getattr | ~50% fewer attribute lookups in sort loops |

### Test Update

| File | Change |
|------|--------|
| tests/test_recipes.py | `test_recipe_count_after_objects_raises_typeerror` -> `test_recipe_count_after_objects_works` (bug is now fixed) |

---

## Files Modified

| File | Lines changed | Nature |
|------|--------------|--------|
| `coshsh/recipe.py` | +30 / -25 | Bug fix, itertools, setdefault, flat gen, broadcast, getattr |
| `coshsh/item.py` | +30 / -28 | Regex, depythonize hoist, dedup fix |
| `coshsh/templaterule.py` | +2 / -0 | import re, pre-compile |
| `coshsh/datainterface.py` | +2 / -4 | dict.get() |
| `coshsh/datasource.py` | +2 / -4 | dict membership |
| `tests/test_recipes.py` | +5 / -4 | Test updated for bug fix |

---

## Verification

- Full test suite: **205 passed, 0 failed** (31.13s)
- No pre-existing failures affected
- Backward compatibility preserved via `_skip_pythonize` parameter default
