# Data Model: Comprehensive Status Quo Documentation for AI Agent Handover

**Branch**: `001-ai-handover-docs` | **Date**: 2026-02-17

This document describes the structure of the documentation entities — what each artefact
contains, how they relate, and what completeness means for each.

---

## Entity 1: Status Quo Document (`docs/ai_handover.md`)

**What it is**: The primary AI-oriented documentation corpus. A single Markdown file
stored in the repository. Structured with a table of contents for efficient navigation.

**Completeness criteria**: All 20 FRs from the spec are covered; all 8 SCs are satisfied.

**Top-level outline**:

```text
# coshsh Status Quo — AI Agent Reference (February 2026 Baseline)

## Table of Contents

## 1. Project Purpose and Use Cases
   1.1 What coshsh does (problem it solves)
   1.2 Core use cases: Nagios/Icinga config generation
   1.3 Use case: OMD integration
   1.4 Use case: SNMP trap config via check_logfiles
   1.5 Known deployments and scale

## 2. Architecture Overview
   2.1 Component diagram (text)
   2.2 The four-phase pipeline: collect → assemble → render → output
   2.3 Phase dependency chain (why order is non-negotiable)
   2.4 The shared objects dictionary (recipe.objects)

## 3. Core Module Reference (18 modules)
   3.1 generator.py
   3.2 recipe.py
   3.3 datasource.py
   3.4 datarecipient.py
   3.5 datainterface.py
   3.6 item.py
   3.7 host.py
   3.8 application.py
   3.9 contact.py
   3.10 contactgroup.py
   3.11 hostgroup.py
   3.12 monitoringdetail.py
   3.13 templaterule.py
   3.14 vault.py
   3.15 configparser.py
   3.16 jinja2_extensions.py
   3.17 dependency.py
   3.18 util.py
   [Each subsection: responsibility, public API, key methods, preconditions/postconditions]

## 4. Plugin / Extension System
   4.1 Class factory mechanism (CoshshDatainterface)
   4.2 Class path search order and the catchall mechanism
   4.3 Ident function conventions
        4.3.1 __ds_ident__ (datasource plugins)
        4.3.2 __mi_ident__ (application/host/contact plugins)
        4.3.3 __detail_ident__ (MonitoringDetail plugins)
        4.3.4 __vault_ident__ (vault plugins)
   4.4 Class file naming prefixes
   4.5 Reversed iteration order and what it means for override priority
   4.6 Catchall directories (appended last; lowest priority)

## 5. MonitoringDetail Type Reference (19 types)
   [For each: monitoring_type value, monitoring_0..N parameter mapping,
    resulting object attributes, property_type (str/list/dict), example]
   5.1  LOGIN
   5.2  LOGINSNMPV2
   5.3  LOGINSNMPV3
   5.4  FILESYSTEM
   5.5  PORT
   5.6  INTERFACE
   5.7  DATASTORE
   5.8  TABLESPACE
   5.9  URL
   5.10 TAG
   5.11 ROLE
   5.12 DEPTH
   5.13 VOLUME
   5.14 PROCESS
   5.15 SOCKET
   5.16 ACCESS
   5.17 KEYVALUES
   5.18 NAGIOSCONF
   5.19 CUSTOM_MACRO

## 6. INI Configuration File Reference
   6.1 [defaults] section
   6.2 [recipe_NAME] section — all keys, types, defaults, effects
   6.3 [datasource_NAME] section
   6.4 [datarecipient_NAME] section
   6.5 [vault_NAME] section
   6.6 [mapping_NAME] section
   6.7 [prometheus_pushgateway] section
   6.8 Variable substitution: %ENV_VAR%, @VAULT[key], @MAPPING_NAME[key]
   6.9 Recipe inheritance via isa

## 7. Jinja2 Template System
   7.1 Template discovery (FileSystemLoader, templates_path)
   7.2 Template caching
   7.3 Built-in filters: service, host, contact, custom_macros, re_sub,
       re_escape, rfc3986, neighbor_applications
   7.4 Built-in tests: re_match
   7.5 Built-in globals: environ
   7.6 Registering custom Jinja2 extensions (my_jinja2_extensions config key)
   7.7 How the service filter generates Nagios service definitions with NAGIOSCONF
   7.8 Template file naming and the .tpl extension

## 8. Output Directory Structure
   8.1 dynamic/ vs static/ directories
   8.2 dynamic/hosts/<host_name>/host.cfg
   8.3 dynamic/hosts/<host_name>/<app_template>.cfg
   8.4 dynamic/hostgroups/, dynamic/contacts/, dynamic/contactgroups/
   8.5 Generated filename conventions and sanitization

## 9. Delta / Cache Safety Mechanism
   9.1 count_before_objects() and count_after_objects()
   9.2 Positive vs negative max_delta semantics
   9.3 max_delta_action options (warn / error / none)
   9.4 safe_output and git reset --hard behaviour
   9.5 When to use and when to disable

## 10. Vault and Secrets Management
    10.1 Vault plugin discovery (__vault_ident__)
    10.2 @VAULT[key] substitution in recipe config
    10.3 %ENV_VAR% environment variable substitution
    10.4 @MAPPING_NAME[key] config mapping substitution
    10.5 Built-in vault types (vault_pass, vault_naemon)
    10.6 Recipe-level secret resolution (recipe.substsecret)

## 11. Hostname Transformations
    11.1 strip_domain
    11.2 to_lower / to_upper
    11.3 append_domain (DNS FQDN lookup)
    11.4 resolve_ip (reverse DNS)
    11.5 resolve_dns (forward DNS)
    11.6 Configuration and execution order

## 12. Plugin Authoring Guide
    12.1 Creating a datasource plugin (complete worked example)
    12.2 Creating an application class plugin (with list-type MonitoringDetail)
    12.3 Creating a MonitoringDetail plugin (scalar and list types)
    12.4 Creating a vault plugin
    12.5 Creating a custom Jinja2 extension
    12.6 Writing a full recipe INI file with vault integration (complete example)

## 13. Test Infrastructure Guide
    13.1 CommonCoshshTest base class
    13.2 Test recipe fixture layout (tests/recipes/<testNN>/)
    13.3 Setup, teardown, and cleanup patterns
    13.4 Asserting on generated output files
    13.5 Testing datasource plugins
    13.6 Testing application class plugins
    13.7 Running the test suite

## 14. Edge Cases and Gotchas
    14.1 Fingerprint collision (later object silently overwrites earlier)
    14.2 Ident function priority (reversed class_factory; last-registered wins)
    14.3 Catchall directory ordering (lowest priority)
    14.4 DatasourceNotAvailable handling (skipped, logged, pipeline continues)
    14.5 Jinja2 UndefinedError and the render_errors counter
    14.6 Circular isa inheritance (unsupported; behaviour undefined)
    14.7 Vault backend unreachable (raises exception; recipe aborted)
    14.8 max_delta with a baseline of zero objects (division by zero guard)

## 15. Prometheus Pushgateway Integration
    15.1 What metrics are emitted and when
    15.2 Configuration (address, job, credentials)
    15.3 Relationship to recipe execution

## 16. OMD Integration
    16.1 What OMD is and where coshsh fits
    16.2 OMD-specific path conventions (%OMD_ROOT%)
    16.3 Default recipe directory layout in an OMD site
    16.4 Running coshsh-cook inside OMD

## 17. SNMP Trap Configuration via check_logfiles
    17.1 Use case and context
    17.2 Relevant datarecipient and template pattern
    17.3 The testsnmptt test recipe as a runnable reference

## Appendix A: Quick Reference — All Config Keys
## Appendix B: Quick Reference — All MonitoringDetail Types
## Appendix C: Class Factory Decision Tree
```

**Relationships**:
- References `coshsh/*.py` inline comments (must be consistent)
- Is referenced by `quickstart.md` (entry point for new readers)
- Supersedes `doc/coshsh.md` (tutorial) and deepwiki as the authoritative AI reference

---

## Entity 2: Inline Code Comments (`coshsh/*.py`)

**What it is**: Docstrings and `# WHY:` comments embedded in each of the 18 core source
files. Not a separate deliverable but a modification to existing files.

**Completeness criteria**: Every source file has a module-level docstring; every
non-trivial code block (>5 lines of non-obvious logic) has a comment; every public
method has a docstring explaining purpose, preconditions, and side effects.

**Comment anatomy** (per research.md Decision 2):

```python
"""
Module docstring: one paragraph explaining this module's sole responsibility,
what it owns, and what it does NOT do (boundaries matter for AI agents).
"""

class Foo:
    """Class docstring: what this class represents and its lifecycle."""

    def bar(self, x):
        """
        Method docstring: what this does, what the caller must provide,
        what state changes occur, what exceptions can be raised.
        """
        # WHY: [reason for non-obvious logic]
        ...
```

---

## Entity 3: Plugin Authoring Guide (section 12 of `docs/ai_handover.md`)

**What it is**: A self-contained guide (within the status quo document) for creating each
plugin type. Contains complete, runnable code examples.

**Completeness criteria**: An AI agent reading only Section 12 can produce a correct,
passing plugin of any type without consulting any other source.

**Each plugin example must include**:
1. The ident function with correct signature and return type
2. The class definition with correct inheritance
3. The required interface methods with correct signatures
4. The corresponding recipe INI configuration snippet
5. A reference to the test pattern for verifying the plugin works

---

## Entity 4: Configuration Reference (section 6 of `docs/ai_handover.md`)

**What it is**: A structured table of every INI configuration key with type, default,
and effect. Formatted as Markdown tables for easy AI scanning.

**Completeness criteria**: Every key accepted by `coshsh/configparser.py` and
`coshsh/recipe.py` is listed; no undocumented keys exist after this feature.

**Table format** (example):

| Key | Section | Type | Default | Effect |
|-----|---------|------|---------|--------|
| `objects_dir` | `[recipe_*]` | path string | none (required) | Directory where the default datarecipient writes config files |
| `max_delta` | `[recipe_*]` | `int:int` | none (disabled) | Maximum allowed percentage change in host:app counts before aborting |
| `safe_output` | `[recipe_*]` | bool | `false` | If true, git-reset output dir when max_delta is exceeded |

---

## Entity 5: Test Infrastructure Guide (section 13 of `docs/ai_handover.md`)

**What it is**: A description of the `CommonCoshshTest` base class, test recipe fixtures,
and assertion patterns. Structured as a tutorial-style walkthrough with a complete example.

**Completeness criteria**: An AI agent reading only Section 13 can write a passing pytest
test for a new datasource plugin without any other guidance.

**Required content**:
1. `CommonCoshshTest` — what it does in `setUp()` and `tearDown()`
2. `setUpConfig(configfile, recipe_name)` — what it loads and what state results
3. How to write a test recipe config file and fixture data
4. How to call the pipeline: `collect()`, `assemble()`, `render()`, `output()`
5. How to assert on generated files: `os.path.exists()`, reading `.cfg` content
6. Complete working example: datasource test from scratch to passing
