# Contract: Status Quo Document Structure (`docs/ai_handover.md`)

**Branch**: `001-ai-handover-docs` | **Date**: 2026-02-17

This contract defines the agreed structural requirements for the primary documentation
artefact. Any implementation that deviates from these rules MUST update this contract
first.

---

## File Location and Format

- Path: `docs/ai_handover.md` (relative to repository root)
- Format: CommonMark Markdown
- Encoding: UTF-8
- Line endings: Unix (LF)
- Max line length: soft limit 100 chars (enforced in prose; code blocks exempt)

## Mandatory Sections (all must be present)

| Section | FR Satisfied | Must Contain |
|---------|-------------|--------------|
| 1. Project Purpose and Use Cases | FR-001, FR-019, FR-020 | All 4 use cases including OMD and SNMP trap |
| 2. Architecture Overview | FR-001, FR-015 | Phase pipeline diagram; phase dependency rationale |
| 3. Core Module Reference | FR-002 | All 18 modules; responsibility + public API per module |
| 4. Plugin / Extension System | FR-003 | All 4 ident conventions; catchall ordering; override priority |
| 5. MonitoringDetail Type Reference | FR-004 | All 19 types; monitoring_N mapping; result attributes |
| 6. INI Configuration File Reference | FR-005, FR-010 | All 7 section types; all keys; substitution patterns |
| 7. Jinja2 Template System | FR-006 | All filters/tests/globals; NAGIOSCONF integration; custom extensions |
| 8. Output Directory Structure | FR-008 | dynamic/ and static/; all subdirectories; file naming |
| 9. Delta / Cache Safety Mechanism | FR-007 | Positive vs negative max_delta; git reset; action options |
| 10. Vault and Secrets Management | FR-010 | All substitution patterns; built-in vault types |
| 11. Hostname Transformations | FR-011 | All 5 transform ops; config; execution order |
| 12. Plugin Authoring Guide | FR-009 | 3 complete worked examples (datasource, app class, full recipe) |
| 13. Test Infrastructure Guide | FR-012 | Base class; fixture pattern; assertion strategy; full example |
| 14. Edge Cases and Gotchas | FR-013 | All 8 documented edge cases from spec |
| 15. Prometheus Pushgateway | FR-017 | Metrics emitted; config keys; timing |
| 16. OMD Integration | FR-019 | OMD paths; recipe layout; coshsh-cook in OMD |
| 17. SNMP Trap / check_logfiles | FR-020 | Use case; datarecipient pattern; testsnmptt reference |
| Appendices | FR-018 | ToC; config key quick reference; MonitoringDetail quick reference |

## Navigation Requirements (FR-018)

- The document MUST open with a complete, linked Markdown table of contents.
- Each major section MUST end with a "See also:" line referencing related sections.
- Cross-references MUST use anchor links: `[Section 4.5](#45-reversed-iteration-order)`.
- Every class/method name mentioned MUST be formatted in backticks.
- Every config key mentioned MUST be formatted in backticks.

## Accuracy Requirements (SC-008)

- Every class name, method signature, config key, and file path MUST match the
  February 2026 baseline commit exactly.
- If a fact cannot be verified from the source code, it MUST be omitted rather than
  guessed.
- Code examples in the worked examples section MUST be complete and runnable.

## Forbidden Content

- Do NOT include implementation HOW choices for future features (this is a status quo doc).
- Do NOT reference omd.consol.de/docs/coshsh as a source (known hallucinations).
- Do NOT describe behaviour that does not exist in the Feb 2026 baseline.
