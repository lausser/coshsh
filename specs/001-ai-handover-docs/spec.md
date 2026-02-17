# Feature Specification: Comprehensive Status Quo Documentation for AI Agent Handover

**Feature Branch**: `001-ai-handover-docs`
**Created**: 2026-02-17
**Status**: Draft

## Context

Coshsh is a Python 3 framework that transforms data from arbitrary datasources (CMDBs,
CSV files, databases, LDAP, etc.) into configuration files for open-source monitoring
systems (Nagios, Icinga, Naemon, Shinken, Prometheus). The project author intends to hand
over all future maintenance, bug fixing, and feature development to AI agents.

For AI agents to work safely on a production infrastructure tool used by large
enterprises, they require a single authoritative, fine-grained documentation corpus that
captures the complete state of the codebase as of February 2026 — the last version
written and maintained by humans.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - AI Agent First Contact (Priority: P1)

An AI agent is asked to make a change to coshsh with no prior context about the project.
The agent reads the status quo documentation and — without any human explanation — gains
enough understanding to correctly locate the relevant code, understand the design intent,
avoid breaking existing behaviour, and produce a correct implementation.

**Why this priority**: Every future AI maintenance task begins here. Without this
capability, all other stories are blocked. This is the foundational requirement.

**Independent Test**: An AI agent given only the documentation corpus must correctly
describe the four-phase pipeline, identify the correct module to modify for a datasource
change, and explain why the delta safety mechanism exists — all three answers correct
and complete without consulting source files.

**Acceptance Scenarios**:

1. **Given** a fresh AI agent with only the documentation corpus, **When** asked "where
   does coshsh read host data from and how does the object reach the output directory?",
   **Then** the agent produces an accurate step-by-step answer referencing the correct
   modules, classes, and method names.

2. **Given** a bug report describing incorrect host configuration output, **When** the
   AI agent consults the documentation, **Then** it correctly identifies the rendering
   pipeline (item.render → template_rules → Jinja2 → config_files) as the area to
   investigate, without hallucinating non-existent components.

3. **Given** no prior session context, **When** an AI agent is asked to add a new
   MonitoringDetail type, **Then** it follows the established plugin pattern exactly as
   described in the documentation.

---

### User Story 2 - AI Agent Plugin Authoring (Priority: P1)

An AI agent is asked to author a new plugin — a datasource adapter, an application
class, a MonitoringDetail type, or a Jinja2 extension. The documentation provides a
complete, worked guide covering every step from the ident function through to the
template rules and configuration, with concrete examples.

**Why this priority**: Plugin authoring is the primary extension mechanism of coshsh and
the most common change request. Getting this wrong generates incorrect monitoring
configuration in production.

**Independent Test**: Given only the plugin authoring guide, an AI agent must produce a
syntactically and semantically correct, runnable datasource class and application class
without any additional hints.

**Acceptance Scenarios**:

1. **Given** the plugin authoring documentation, **When** an AI agent creates a new
   datasource plugin file, **Then** the file contains a correct ident function, inherits
   from the correct base class, implements the required interface methods, and the
   resulting code passes the existing test suite without modification.

2. **Given** the plugin authoring documentation, **When** an AI agent creates a new
   application class file, **Then** the file contains a correct ident function, inherits
   from the correct base class, declares template rules, and the class is discoverable
   by the coshsh class factory.

3. **Given** the plugin authoring documentation, **When** an AI agent creates a new
   MonitoringDetail plugin, **Then** it correctly sets all required class-level
   attributes consistent with the documented conventions for scalar and list-type details.

---

### User Story 3 - AI Agent Code Comprehension via Inline Comments (Priority: P1)

An AI agent reads any source file in the coshsh package and immediately understands the
*why* behind every non-obvious piece of logic — not just what the code does, but why it
was written that way, what constraints shaped it, and what would break if it were changed.

**Why this priority**: The constitution mandates that inline comments are the primary
documentation channel for AI collaborators. Without this, the documentation and the code
can diverge. The code itself must be self-explanatory.

**Independent Test**: An AI agent reads any single source file from the core package and,
without consulting any other document, answers correctly: (a) the module's
responsibility, (b) why at least two non-obvious implementation decisions were made, (c)
what the caller must guarantee as a precondition for each public method.

**Acceptance Scenarios**:

1. **Given** the core recipe orchestrator file with comments, **When** an AI agent reads
   it, **Then** it correctly explains why process-lock protection exists, what the
   safe output guard prevents, and why assembly is a separate phase from collection.

2. **Given** the class factory framework file with comments, **When** an AI agent reads
   it, **Then** it correctly explains the reversed iteration order of the class registry,
   why dynamic module imports are used, and what happens when two ident functions both
   claim the same parameters.

3. **Given** the base item file with comments, **When** an AI agent reads it, **Then**
   it correctly explains why rendered output is keyed by tool name, what monitoring
   detail resolution does to the object's attributes, and when unique config naming
   applies.

---

### User Story 4 - New Human Maintainer Orientation (Priority: P2)

A human engineer joining the project reads the status quo document and within one working
session fully understands the architecture, can navigate the codebase confidently, and
can describe to a colleague how coshsh processes a CSV file into a Nagios configuration.

**Why this priority**: Human reviewers must approve AI-authored changes. They need enough
architectural understanding to review changes responsibly, even if they no longer write
code themselves.

**Independent Test**: A human reading only the status quo document must answer the five
most common architecture questions without opening any source file.

**Acceptance Scenarios**:

1. **Given** the status quo document, **When** a human is asked "what is a recipe?",
   **Then** they can answer with the correct attributes and explain the four-phase
   lifecycle without having read any source code.

2. **Given** the status quo document, **When** a human is asked "how do I add monitoring
   for a new application type?", **Then** they can describe the three steps: create a
   class file with an ident function, declare template rules, create the template file.

3. **Given** the status quo document, **When** asked "what prevents coshsh from
   accidentally deleting all monitoring configs?", **Then** they correctly describe the
   object-count delta mechanism, the action options, and the git-based revert behaviour.

---

### User Story 5 - AI Agent Test Authoring (Priority: P2)

An AI agent is asked to add tests for a new or modified feature. The documentation
describes the existing test infrastructure clearly enough that the agent produces a
passing test without guidance.

**Why this priority**: Test-first development is non-negotiable per the project
constitution. AI agents must write tests as readily as implementation code.

**Independent Test**: An AI agent given only the test infrastructure documentation
produces a pytest test for a new datasource that correctly sets up a recipe, invokes the
full pipeline, and asserts on the presence and content of output files — and the test
passes on first run.

**Acceptance Scenarios**:

1. **Given** the test infrastructure documentation, **When** an AI agent writes a new
   test, **Then** it correctly inherits from the base test class, calls the required
   setup methods, and cleans up output directories.

2. **Given** the test infrastructure documentation, **When** the test is run, **Then**
   it passes without modification and produces no warnings about missing fixtures or
   undefined symbols.

---

### Edge Cases

- What happens when two ident functions both return a class for the same params dict?
- What happens when a datasource raises an unavailability exception mid-collection?
- How does a positive vs negative `max_delta` value differ in behaviour?
- What happens when a template references an attribute the object does not have?
- What happens when two application instances share the same fingerprint?
- What happens when circular `isa` inheritance exists in a recipe config file?
- How does the catchall class directory differ from a regular class directory in
  its search priority?
- What happens when a vault section is defined but the vault backend is unreachable?

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The documentation MUST provide a complete architectural overview of
  coshsh: purpose, the four-phase pipeline (collect → assemble → render → output), and
  the relationship between all major components.

- **FR-002**: The documentation MUST describe every module in the core package with its
  responsibility, its public classes, and its key methods including preconditions,
  postconditions, and side effects.

- **FR-003**: The documentation MUST describe the plugin/extension system in full:
  class factory mechanism, all four ident function conventions, class path search order,
  and the catchall mechanism and how it differs from regular class paths.

- **FR-004**: The documentation MUST describe every built-in MonitoringDetail type
  (LOGIN, LOGINSNMPV2, LOGINSNMPV3, FILESYSTEM, PORT, INTERFACE, DATASTORE, TABLESPACE,
  URL, TAG, ROLE, DEPTH, VOLUME, PROCESS, SOCKET, ACCESS, KEYVALUES, NAGIOSCONF,
  CUSTOM_MACRO) including their monitoring_N parameter mapping and resulting object
  attributes.

- **FR-005**: The documentation MUST describe the complete INI recipe configuration
  file format: every section type, every recognised key, its type, default value, and
  effect on the pipeline.

- **FR-006**: The documentation MUST describe the Jinja2 template system: how templates
  are discovered, the complete list of custom filters and tests with examples, how the
  service/host/contact/custom_macros filters generate Nagios object definitions, and how
  to register custom Jinja2 extensions.

- **FR-007**: The documentation MUST describe the delta/cache safety mechanism:
  how before/after object counts are tracked, how positive vs negative max_delta values
  behave asymmetrically, the max_delta_action options, and safe_output git reset behaviour.

- **FR-008**: The documentation MUST describe the output directory structure produced
  by the default datarecipient, including the role of the dynamic and static directories
  and the naming conventions for generated files.

- **FR-009**: The documentation MUST include at least three complete worked examples:
  (a) creating a datasource adapter from scratch, (b) creating an application class with
  multiple template rules including conditional and list-type details, (c) writing a full
  recipe configuration file with vault integration.

- **FR-010**: The documentation MUST describe the vault and secrets management system:
  vault plugin discovery, @VAULT[key] substitution, %ENV_VAR% environment variable
  substitution, and @MAPPING_NAME[key] config mapping substitution, with examples of each.

- **FR-011**: The documentation MUST describe all hostname transformation operations,
  their configuration, and their execution order.

- **FR-012**: The documentation MUST describe the test infrastructure: base test class,
  test recipe fixture patterns, how to assert on generated output files, and how to
  structure a test for each plugin type.

- **FR-013**: The documentation MUST document all known non-obvious behaviours, edge
  cases, and gotchas: fingerprint collision behaviour, ident function priority ordering,
  catchall class ordering, datasource exception handling, Jinja2 render error counting,
  and the effect of circular isa inheritance.

- **FR-014**: Every source file in the core package MUST contain module-level docstrings
  and inline comments explaining *why* each non-obvious decision was made, including
  design constraints, historical context where known, and failure modes.

- **FR-015**: The documentation MUST describe the phase dependency chain: why assembly
  cannot happen before collection, why rendering cannot happen before assembly, and what
  state each phase expects to find in the shared objects dictionary.

- **FR-016**: The documentation MUST describe all built-in datasource and datarecipient
  types including their configuration parameters and expected behaviour.

- **FR-017**: The documentation MUST describe the Prometheus pushgateway integration:
  what metrics are emitted, when they are emitted, and how the integration is configured.

- **FR-018**: The documentation MUST be structured for efficient AI agent navigation:
  a top-level table of contents, per-section cross-references, and explicit links
  between related concepts (e.g., TemplateRule → Jinja2 rendering, MonitoringDetail →
  Application assembly).

- **FR-019**: The documentation MUST describe the OMD (Open Monitoring Distribution)
  integration: how coshsh is deployed inside an OMD site, the OMD-specific path
  conventions (%OMD_ROOT%), and the default recipe directory layout expected by OMD.

- **FR-020**: The documentation MUST describe the SNMP trap / check_logfiles use case:
  how coshsh generates check_logfiles configuration from SNMP trap definitions, the
  relevant datarecipient and template patterns, and how the SNMPTT-related test fixtures
  exercise this use case.

### Key Entities

- **Status Quo Document**: The primary AI-oriented documentation corpus stored in the
  repository; covers architecture, all components, extension patterns, and worked
  examples. Serves as the single authoritative reference for AI agents.
- **Inline Code Comments**: Comments within each core source file; cover module purpose,
  class design intent, method pre/post conditions, and non-obvious logic. The primary
  documentation channel per the project constitution.
- **Plugin Authoring Guide**: A self-contained section describing how to create each
  plugin type with complete, runnable examples covering datasource, application,
  MonitoringDetail, and vault plugins.
- **Configuration Reference**: A structured reference for the INI recipe file format,
  listing every key, its type, its default, and its effect.
- **Test Infrastructure Guide**: A description of the base test class, fixture patterns,
  and assertion strategies sufficient for an AI agent to write a passing test without
  human guidance.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An AI agent with no prior coshsh context, given only the documentation
  corpus, correctly answers 9 out of 10 architecture questions drawn from a predefined
  question bank covering all major subsystems on its first attempt.

- **SC-002**: An AI agent produces a syntactically and semantically correct, runnable
  datasource plugin and application class plugin using only the plugin authoring guide,
  with zero corrections required from a human reviewer.

- **SC-003**: Every source file in the core package contains at least one module-level
  docstring and inline comments on every non-trivial code block; verified by a
  documentation coverage audit comparing files before and after.

- **SC-004**: All 18 core modules are documented with responsibility, public API, and
  at least one usage example; verified by cross-referencing against the actual file
  listing.

- **SC-005**: An AI agent reading only the core recipe orchestrator file with its
  comments can correctly explain the process-lock mechanism, the safe output guard, and
  the role of each of the four pipeline phases — without consulting any other file.

- **SC-006**: A new human maintainer, reading the status quo document for the first time,
  can correctly describe the complete data flow from a CSV file row to a written cfg file,
  including every class and method touched along the way.

- **SC-007**: All edge cases and non-obvious behaviours listed in FR-013 are explicitly
  documented with the observed behaviour, the reason for that behaviour, and any gotchas
  for callers.

- **SC-008**: The documentation passes a factual accuracy check: every class name, method
  signature, configuration key, and file path mentioned in the document matches the
  actual codebase as of the February 2026 baseline commit.

---

## Assumptions

- The documentation describes the February 2026 baseline codebase. It does not propose
  code changes; it documents existing behaviour only.
- Inline comments will be added to all files in the core package. Files under tests/,
  recipes/, and build/ are out of scope for inline commenting unless directly relevant
  to understanding core behaviour.
- The primary format for the status quo document is Markdown, stored in the repository.
- No external documentation platform is required; the repository itself is the
  documentation home, consistent with the AI-First principle in the project constitution.
- The documentation is complete when all functional requirements are satisfied and all
  success criteria are measurable and verifiable against the codebase.
- **Reference sources**: https://deepwiki.com/lausser/coshsh is considered a reliable
  modern reference and may be consulted during authoring. https://omd.consol.de/docs/coshsh/
  exists but is known to contain hallucinations in the datasource section and MUST NOT be
  used as a source of truth. The secrets blog post at
  https://omd.consol.de/blog/2025/07/17/coshsh-can-keep-a-secret/ is a reliable reference
  for the vault/secrets system.

## Additional Use Cases to Document

The following use cases MUST be covered in the status quo document in addition to the
core Nagios/Icinga configuration generation flow:

- **OMD Integration**: Coshsh ships as a component of the Open Monitoring Distribution
  (OMD). The status quo document MUST describe how coshsh is deployed and configured
  within an OMD site, including the OMD-specific path conventions (%OMD_ROOT%) and the
  default recipe layout expected by OMD. Reference: https://github.com/Consol-Monitoring/omd

- **SNMP Trap Configuration via check_logfiles**: Within OMD, coshsh can generate
  configuration files for check_logfiles, enabling monitoring systems to scan and alert
  on SNMP traps written to log files. The status quo document MUST describe this
  datarecipient use case, the relevant template pattern, and the SNMPTT-related test
  fixtures in the test suite.
