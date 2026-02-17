<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.0 → 1.1.0 (MINOR — new principle added, Python version tightened)

Modified principles:
  - Technology Constraints: Python 3 → Python 3.12+

Added sections:
  - Core Principles: VI. AI-First Development (new)
  - Governance: AI Transition Baseline sub-section (new)

Removed sections: N/A

Templates reviewed:
  ✅ .specify/templates/plan-template.md   — Constitution Check section present; aligns with these principles
  ✅ .specify/templates/spec-template.md   — User Scenarios, Requirements, and Success Criteria sections align
  ✅ .specify/templates/tasks-template.md  — Phase structure and parallel markers align with Principles III, V, VI
  ✅ .specify/templates/constitution-template.md — Source template used as basis

Follow-up TODOs:
  None — all placeholders resolved.
-->

# coshsh Constitution

## Core Principles

### I. Configuration-as-Code (NON-NEGOTIABLE)

All monitoring configuration MUST be generated programmatically from datasources via coshsh.
Manual editing of generated output files is prohibited.
Datasources (CSV, database, LDAP, etc.) are the single source of truth for host and
application data.
Template files are the single source of truth for monitoring check definitions.

**Rationale**: Manual configuration does not scale. coshsh exists precisely to eliminate
human-maintained config files. Any feature that encourages direct editing of generated
output undermines the core value proposition.

### II. Extensibility via Class and Template Files

coshsh MUST be extended through Python class files and Jinja2 template files only.
Class files MUST implement `__mi_ident__` for auto-registration.
Classes MUST inherit from `coshsh.application.Application` or equivalent base classes.
Template rules MUST be declared as `coshsh.templaterule.TemplateRule` instances.
No core coshsh source files may be modified to add application-specific behaviour.

**Rationale**: Separation of core framework from user-supplied extensions allows coshsh to
be upgraded independently of local customisations. The plugin-style architecture means
organisations can share class/template packs without coupling to core internals.

### III. Test-First Development (NON-NEGOTIABLE)

All new features and bug fixes MUST have corresponding pytest tests before implementation.
Tests MUST fail (red) before implementation, then pass (green) after.
The `tests/` directory structure MUST be maintained; each test MUST be independently
runnable via `pytest tests/test_<feature>.py`.
Test recipes placed under `tests/recipes/` MUST be self-contained and not depend on
external services.

**Rationale**: coshsh generates configuration consumed directly by production monitoring
systems. Regressions in generated output can silently disable monitoring for thousands of
services. A failing test suite is always preferable to silent configuration drift.

### IV. Performance and Correctness at Scale

coshsh MUST generate ≥ 60,000 services in ≤ 10 seconds on reference hardware.
Generated output MUST be deterministic: identical datasource input MUST produce byte-for-byte
identical output across runs (modulo intentional timestamps).
Delta/cache mechanisms MUST only write files that have changed.
Memory usage MUST remain bounded regardless of datasource size (streaming preferred over
loading all records into memory simultaneously where feasible).

**Rationale**: Deployments at large enterprises (60 k+ services demonstrated) require
predictable, fast generation. Determinism is essential for change-detection pipelines and
version-controlled configuration repositories.

### V. Simplicity and Minimal Surface Area

New abstractions MUST solve a demonstrated problem; speculative/YAGNI additions are
rejected.
Public API surface (Python classes, CLI flags, config-file keys) follows
MAJOR.MINOR.PATCH semantic versioning; breaking changes require a MAJOR bump.
Dependencies introduced into the core package MUST be justified against the added
maintenance burden; prefer stdlib where equivalent functionality exists.
Generated config output format changes MUST be backward-compatible or versioned.

**Rationale**: coshsh is infrastructure software used in production by many organisations.
Stability and predictability matter more than feature richness. A small, well-understood
codebase is easier to audit, debug, and contribute to.

### VI. AI-First Development (NON-NEGOTIABLE)

coshsh is an **AI-First** project as of February 2026. This means:

- All source code MUST be thoroughly commented so that AI agents can understand intent,
  constraints, and non-obvious design decisions without additional context.
- Comments are the primary documentation channel for AI collaborators; they MUST explain
  *why* a decision was made, not merely *what* the code does.
- Human-readable documentation (README, docs/, changelogs) MUST continue to be maintained
  for human users and operators, but it is a secondary artifact.
- No code change is considered complete unless its comments are sufficient for an AI agent
  to independently understand, modify, and extend that code correctly.
- AI agents MUST follow every other principle in this constitution exactly as a human
  contributor would.

**Rationale**: Delegating implementation, maintenance, and enhancement to AI agents
requires machine-readable intent embedded in the code itself. A comment-rich codebase
removes the need for out-of-band tribal knowledge and makes AI-assisted development
reliable and auditable.

## Technology Constraints

- **Language**: Python 3.12+ (modern language features are encouraged; no Python 2 or
  pre-3.12 compatibility shims permitted in new code).
- **Templating**: Jinja2 is the exclusive templating engine; custom Jinja2 extensions are
  permitted via the class-file mechanism.
- **Datasources**: Any datasource adapter MUST implement the standard coshsh datasource
  interface (`fill_objects` / `read` pattern).
- **Output targets**: Any data-recipient adapter MUST implement the standard coshsh
  datarecipient interface.
- **Testing framework**: pytest exclusively; `unittest`-style tests are tolerated but new
  tests MUST use pytest idioms.
- **Config format**: INI-style recipe files parsed by Python `configparser`; no YAML/TOML
  config added to core without a MAJOR version bump.

## Development Workflow

1. A feature starts with a specification (`specs/<branch>/spec.md`) describing WHAT and
   WHY, not HOW.
2. Tests are written and confirmed to fail before any implementation begins.
3. Implementation proceeds in the smallest increment that makes the failing tests pass.
4. Generated output is committed to the repository only when the change is intentional and
   reviewed.
5. All PRs MUST pass the full `pytest` suite and must not regress the performance
   benchmark (60 k services / 10 s).
6. Commit messages MUST be descriptive; reference the feature branch or issue number.
7. Breaking API changes MUST be communicated via CHANGELOG and a version bump before merge.

## Governance

This constitution supersedes all other development practices documented in this repository.
Amendments require:
1. A written proposal describing the change and its rationale.
2. Review and approval by at least one maintainer.
3. A version bump following the semantic versioning policy described in Principle V.
4. An update to `LAST_AMENDED_DATE` below.

Versioning policy:
- **MAJOR**: Backward-incompatible removal or redefinition of a principle.
- **MINOR**: New principle, section, or materially expanded guidance added.
- **PATCH**: Clarification, wording improvement, or typo fix.

All PRs and code reviews MUST verify compliance with the principles above.
Complexity that violates Principle V MUST be justified in the plan's Complexity Tracking
table before implementation is approved.

### AI Transition Baseline

The state of the coshsh codebase as of **February 2026** constitutes the official baseline:
the last version designed, written, and maintained exclusively by human contributors.
From this point forward:

- All new code, bug fixes, refactoring, and enhancements MUST be authored by AI agents.
- Human contributors MUST NOT directly write or modify source code; their role is to
  specify intent, review AI-authored output, and approve or reject changes.
- The February 2026 baseline is preserved in git history and serves as the reference point
  for measuring AI-driven evolution of the project.

**Version**: 1.1.0 | **Ratified**: 2026-02-17 | **Last Amended**: 2026-02-17
