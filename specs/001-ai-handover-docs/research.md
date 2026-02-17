# Research: Comprehensive Status Quo Documentation for AI Agent Handover

**Branch**: `001-ai-handover-docs` | **Date**: 2026-02-17

## Overview

No NEEDS CLARIFICATION items were raised in the spec. This research document records
decisions made during planning about documentation structure, comment conventions, and
information sources.

---

## Decision 1: Single Markdown File vs Multi-File Documentation

**Decision**: Deliver the primary status quo document as a single Markdown file
(`docs/ai_handover.md`) rather than a directory of smaller files.

**Rationale**: AI agents consume documentation most efficiently when the relevant context
fits in a single read operation. A monolithic but well-structured Markdown file with a
table of contents gives an agent the complete picture in one fetch. Fragmented files
require the agent to discover, traverse, and stitch together multiple reads, increasing
the chance of missed context.

**Alternatives considered**:
- Multi-file docs/ directory (rejected: requires discovery; increases chance of partial reads)
- External wiki (rejected: constitution Principle VI requires docs in-repo; contradicts AI-First)
- README-only (rejected: README is for human quick-start; insufficient depth for AI agents)

---

## Decision 2: Inline Comment Style

**Decision**: Use Python docstrings for module-level and class/method-level documentation;
use `# WHY:` prefixed inline comments for non-obvious single-line or block decisions.

**Rationale**: Python docstrings are the language-standard mechanism and are indexed by
documentation tools. The `# WHY:` prefix makes design-intent comments visually
distinguishable from descriptive comments, letting an AI agent quickly locate the
reasoning behind unusual choices without reading every comment.

**Convention**:
```python
# WHY: We iterate class_factory in reverse so that user-supplied classes (appended last)
# are found before built-in defaults. This allows local overrides without patching core.
for entry in reversed(cls.class_factory):
    ...
```

**Alternatives considered**:
- No convention (rejected: inconsistent; hard to scan)
- RST-style docstrings (rejected: project uses plain text style throughout)
- Sphinx-style `:param:` / `:returns:` (rejected: overkill for an infrastructure tool
  with no public API consumers other than AI agents and internal code)

---

## Decision 3: Reference Sources

**Decision**: Use the following sources during documentation authoring, with the noted
trust levels:

| Source | Trust Level | Notes |
|--------|-------------|-------|
| `coshsh/` source files (Feb 2026 baseline) | AUTHORITATIVE | Primary source |
| `tests/` directory | AUTHORITATIVE | Test behaviour is ground truth |
| `doc/coshsh.md` (tutorial) | HIGH | Written by original author |
| https://deepwiki.com/lausser/coshsh | HIGH | Modern, AI-generated from source |
| https://omd.consol.de/blog/2025/07/17/coshsh-can-keep-a-secret/ | HIGH | Authoritative blog on vault/secrets |
| https://omd.consol.de/docs/coshsh/ | LOW — DO NOT USE | Known to contain hallucinations in datasource section |

**Rationale**: The source code and test suite are the ground truth. The tutorial document
(`doc/coshsh.md`) was written by the original author and reflects design intent. The
deepwiki reference is reliable for cross-checking. The omd.consol.de documentation MUST
NOT be used because it is known to hallucinate in the datasource section (noted in AGENTS.md).

---

## Decision 4: Documentation Scope Boundary

**Decision**: Inline comments cover `coshsh/` (the core package, 18 files). The
`recipes/default/classes/` built-in plugins will be documented in the status quo document
but will NOT receive inline comments unless their logic is non-obvious.

**Rationale**: The `coshsh/` package is the stable, versioned core. Plugin files in
`recipes/` are examples and defaults that users regularly copy and modify; adding
authoritative comments there could mislead users into thinking copied plugin files are
immutable. The status quo document covers them descriptively.

**Alternatives considered**:
- Comment all Python files in repo (rejected: over-engineering; recipe files are user-territory)
- Comment only the three most complex core files (rejected: incomplete; misses module
  contracts needed by AI agents for safe edits)

---

## Decision 5: OMD Integration Documentation Placement

**Decision**: OMD-specific context (FR-019) goes in a dedicated section of
`docs/ai_handover.md` rather than being interspersed through other sections.

**Rationale**: OMD deployment is an optional context; most users and AI agents working on
core coshsh do not need it. Isolating it prevents it from cluttering the core architecture
sections while still satisfying FR-019.

---

## Decision 6: SNMP Trap / check_logfiles Documentation

**Decision**: The SNMP trap / check_logfiles use case (FR-020) is documented via the
`datarecipient_prometheus_snmp` pattern and the `testsnmptt` test recipe as worked examples.

**Rationale**: The test suite under `tests/recipes/testsnmptt/` is the ground truth for
this use case. Documenting it through the lens of the existing test recipe gives AI agents
a runnable reference they can verify independently.

---

## Codebase Facts Verified During Research

The following facts were verified directly from the source during planning (all match
the Feb 2026 baseline):

- Core package: `coshsh/` with exactly 18 `.py` files (including `__init__.py`)
- Four pipeline phases: `collect()`, `assemble()`, `render()`, `output()` — all on `Recipe`
- Class factory ident functions: `__ds_ident__`, `__mi_ident__`, `__detail_ident__`,
  `__vault_ident__`
- Class path prefix patterns: `datasource_*`, `app_*`, `os_*`, `detail_*`, `vault*`
- Catchall directories appended to END of class/templates path (not prepended)
- `class_factory` iterated in REVERSE (last-registered wins; user classes beat defaults)
- `config_files` keyed by tool name: `{'nagios': {...}, 'prometheus': {...}}`
- `max_delta` sign semantics: positive = bidirectional ±N%; negative = decrease-only guard
- `safe_output` triggers `git reset --hard` + `git clean -f -d` on delta violation
- `fingerprint()` on Host returns `host_name`; on Application returns `host_name+name+type`
- `isa` inheritance in ConfigParser: one level deep; no cycle detection
- Built-in datasources: `csv`, `recipe_csv`, `discard`, `simplesample`
- Built-in datarecipients: `datarecipient_coshsh_default`, `datarecipient_discard`,
  `datarecipient_prometheus_snmp`
- MonitoringDetail types: 19 built-in types confirmed in `recipes/default/classes/detail_*.py`
- PID file mechanism: `recipe.pid_protect()` / `recipe.pid_remove()` in `recipe.py`
- Prometheus pushgateway: optional section `[prometheus_pushgateway]` in cookbook
