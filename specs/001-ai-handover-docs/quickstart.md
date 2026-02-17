# Quick Start: Using the coshsh AI Agent Documentation Corpus

**Branch**: `001-ai-handover-docs` | **Date**: 2026-02-17

This guide tells you — human or AI agent — how to use the documentation artefacts
produced by this feature.

---

## What was produced

| Artefact | Location | Purpose |
|----------|----------|---------|
| Status quo document | `docs/ai_handover.md` | Comprehensive architecture + reference for AI agents |
| Inline comments | `coshsh/*.py` (all 18 files) | Why-level explanations embedded in source |
| Plugin authoring guide | `docs/ai_handover.md` §12 | Step-by-step guide to creating any plugin type |
| Configuration reference | `docs/ai_handover.md` §6 | Every INI key, type, default, and effect |
| Test infrastructure guide | `docs/ai_handover.md` §13 | How to write a passing test for coshsh |

---

## For AI Agents: Where to Start

**"I need to understand coshsh before making a change"**
→ Read `docs/ai_handover.md` sections 1–4 (Purpose, Architecture, Module Reference,
  Plugin System). This gives you the complete mental model.

**"I need to add or modify a datasource"**
→ Read `docs/ai_handover.md` §4 (Plugin System) + §12.1 (datasource worked example).
  Then read `coshsh/datasource.py` — it is fully commented.

**"I need to add or modify an application class or template"**
→ Read §4 + §12.2 (application class worked example) + §7 (Jinja2 Template System).
  Then read `coshsh/application.py` and `coshsh/item.py`.

**"I need to understand a MonitoringDetail type"**
→ Read `docs/ai_handover.md` §5 (MonitoringDetail Type Reference). Each entry lists the
  `monitoring_N` parameters and the resulting object attributes.

**"I need to write a test"**
→ Read `docs/ai_handover.md` §13 (Test Infrastructure Guide) in full.
  The complete example in §13.6 is runnable; model your test on it.

**"Something went wrong in the pipeline"**
→ Read `docs/ai_handover.md` §14 (Edge Cases and Gotchas) and §2.2 (Pipeline phases).
  Check `coshsh/recipe.py` comments for the phase where the error occurred.

**"I need to configure vault/secrets"**
→ Read `docs/ai_handover.md` §10 (Vault and Secrets Management).

**"I'm working inside an OMD deployment"**
→ Read `docs/ai_handover.md` §16 (OMD Integration).

---

## For Human Maintainers: Where to Start

1. Read `docs/ai_handover.md` §1 (Purpose and Use Cases) to confirm your mental model.
2. Read §2 (Architecture Overview) to understand the data flow.
3. When reviewing an AI-authored change, use §3 (Module Reference) to verify the
   correct module is being modified.
4. Use Appendix A (All Config Keys) as a quick reference when reviewing recipe changes.

---

## Verifying Documentation Accuracy

To check that the documentation matches the codebase:

```bash
# Verify all 18 core modules are present
ls coshsh/*.py | wc -l   # should be 18

# Run the full test suite to confirm the baseline is intact
pytest tests/ -q

# Check that docs/ai_handover.md exists and is non-empty
wc -l docs/ai_handover.md
```

The documentation is considered accurate if all 8 success criteria in
`specs/001-ai-handover-docs/spec.md` are satisfied.

---

## What This Documentation Does NOT Cover

- Proposed future features or design changes (this is a status quo document)
- OMD internals beyond what coshsh needs (see https://omd.consol.de/docs/omd/)
- The omd.consol.de/docs/coshsh documentation (known to contain hallucinations;
  do not use it as a reference)
