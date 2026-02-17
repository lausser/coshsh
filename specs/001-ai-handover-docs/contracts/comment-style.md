# Contract: Inline Comment Style for `coshsh/*.py`

**Branch**: `001-ai-handover-docs` | **Date**: 2026-02-17

This contract defines the agreed conventions for inline comments and docstrings added to
all files in the `coshsh/` core package.

---

## Module-Level Docstring (required in every file)

Every `.py` file in `coshsh/` MUST begin with a module-level docstring immediately after
any `# coding` or `# !` lines. The docstring MUST contain:

1. **One-sentence summary** of what this module is responsible for.
2. **Responsibility boundary**: what this module does NOT do (prevents scope creep when AI
   agents modify it).
3. **Key classes** exported (brief list).
4. **AI agent note** (optional): any non-obvious constraint or invariant that an AI agent
   must not violate.

**Template**:
```python
"""
<Module name>: <one-sentence summary of sole responsibility>.

Does NOT: <list what this module explicitly delegates to other modules>.

Key classes:
    <ClassName>: <one-line description>

AI agent note: <any critical invariant, e.g., "class_factory must be reset between
tests; failure to do so causes cross-test contamination">
"""
```

---

## Class Docstring (required for every public class)

Every public class MUST have a docstring that covers:

1. What this class represents (entity or controller?).
2. Its lifecycle: how it is created, used, and discarded.
3. Key attributes (those an AI agent might need to read or modify).

---

## Method / Function Docstring (required for every public method)

Every public method MUST have a docstring covering:

1. What it does (one sentence).
2. **Preconditions**: what the caller MUST have done / set before calling.
3. **Side effects**: what state changes on `self` or shared objects.
4. **Exceptions**: what can be raised and under what conditions.

---

## `# WHY:` Inline Comments (required for non-obvious logic)

Any code block whose intent is not immediately obvious from the code itself MUST have a
`# WHY:` comment on the line above (or at the end of the line for short lines).

**When to use**:
- Non-obvious algorithm choices
- Non-obvious ordering (e.g., reversed iteration)
- Deliberate fallbacks or swallowed exceptions with justification
- Non-obvious data structure choices
- Historical decisions (e.g., "kept for backward compat with X")
- Cross-module invariants that must hold

**Format**:
```python
# WHY: <reason this non-obvious thing was done this way>
some_non_obvious_code()
```

**Do NOT use `# WHY:` for**:
- Self-explanatory code (e.g., `# WHY: increment counter` above `count += 1`)
- Standard library usage that is well-known

---

## `# NOTE:` Comments (optional, for AI agent warnings)

Use `# NOTE:` for facts that an AI agent must know to avoid introducing bugs:

```python
# NOTE: This list is iterated in reverse later (see get_class). Appending to this list
# means the appended entry has HIGHER priority than earlier entries.
cls.class_factory.append([filepath, module_name, ident_fn])
```

---

## Forbidden Patterns

- Do NOT add comments that merely restate the code (`# increment i` above `i += 1`).
- Do NOT add type annotations if they did not exist in the baseline (out of scope for
  this feature; changes to signatures require separate planning).
- Do NOT remove existing comments.
- Do NOT alter executable code; this feature adds comments only.
