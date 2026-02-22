# Spec 003 — Add Missing Tests for Untested Features

**Branch:** `003-add-missing-tests`
**Date:** 2026-02-22 (updated 2026-02-22, second pass)
**Status:** FINISHED (2026-02-22)
**Baseline:** 100 tests passing (after spec 002)
**Final:** 205 tests passing, 0 warnings

---

## Goal

Add tests for code paths in the core coshsh library that have no coverage or only
incidental coverage via full-pipeline runs.  No production code is changed.  Every
new test must pass against the current source as-is, *except* where a test is
deliberately written to expose a confirmed latent bug (marked **[BUG]** below).

---

## Scope

Tests are grouped by source file and priority.  HIGH items must all be included.
MEDIUM items are all included.  LOW items are included where the effort is trivial.

---

## Latent bugs discovered during analysis

Three latent bugs were found.  Tests are written to **document** them (asserting the
broken behavior), not to fix them.  Fixes belong in a separate spec/PR.

| ID | Location | Bug |
|----|----------|-----|
| BUG-1 | `host.py:121` | `hasattr(self.host_name)` — 1 arg instead of 2; raises `TypeError` |
| BUG-2 | `recipe.py:565` | `sum(0, [list])` — args reversed; raises `TypeError` (cf. line 559 which is correct) |
| BUG-3a | `item.py:397` | `raise "impossible fingerprint"` — Python 2 string raise; raises `TypeError` in Python 3 |
| BUG-3b | `monitoringdetail.py:196` | Same as BUG-3a |

---

## File map: test file → source module(s) under test

| Test file (new or extended) | Source modules |
|-----------------------------|----------------|
| `tests/test_host.py` (NEW) | `coshsh/host.py` |
| `tests/test_item.py` (NEW) | `coshsh/item.py` |
| `tests/test_configparser.py` (NEW) | `coshsh/configparser.py` |
| `tests/test_dependency.py` (NEW) | `coshsh/dependency.py` |
| `tests/test_util.py` (NEW) | `coshsh/util.py` |
| `tests/test_datarecipient.py` (NEW) | `coshsh/datarecipient.py` |
| `tests/test_jinja2_extensions.py` (NEW) | `coshsh/jinja2_extensions.py` |
| `tests/test_templaterule.py` (NEW) | `coshsh/templaterule.py` |
| `tests/test_contactgroup.py` (NEW) | `coshsh/contactgroup.py` |
| `tests/test_datasource.py` (NEW) | `coshsh/datasource.py` |
| `tests/test_delta.py` (EXTEND) | `coshsh/datarecipient.py` — `too_much_delta()` |
| `tests/test_details.py` (EXTEND) | `coshsh/item.py` / `coshsh/monitoringdetail.py` |
| `tests/test_merge.py` (EXTEND) | `coshsh/datasource.py` — `transform_hostname()` |
| `tests/test_recipes.py` (EXTEND) | `coshsh/recipe.py` |
| `tests/test_vault.py` (EXTEND) | `coshsh/vault.py` |
| `tests/test_contacts.py` (EXTEND) | `coshsh/contact.py` |
| `tests/test_generic.py` (EXTEND) | `coshsh/application.py` — GenericApplication |
| `tests/test_package.py` (EXTEND) | `coshsh/application.py` — lower_columns |

---

## Detailed test specifications

### 1. `tests/test_host.py` (NEW) — `HostTest`

Module docstring: `"""Tests for Host construction, attribute normalisation, and is_correct() validation."""`

#### 1a. `test_lower_columns_normalised_on_construction`
Arrange: create `Host({'host_name': 'srv01', 'os': 'LINUX', 'hardware': 'X86', 'type': 'SERVER'})`.
Assert: `host.os == 'linux'`, `host.hardware == 'x86'`, `host.type == 'server'`.

#### 1b. `test_lower_columns_non_string_set_to_none`
Arrange: create `Host({'host_name': 'srv01', 'os': 42})` (non-string value for a lower_column).
Assert: `host.os is None`.

#### 1c. `test_alias_defaults_to_host_name`
Arrange: create `Host({'host_name': 'srv01'})` (no `alias` key).
Assert: `host.alias == 'srv01'`.

#### 1d. `test_alias_preserved_when_supplied`
Arrange: create `Host({'host_name': 'srv01', 'alias': 'my-server'})`.
Assert: `host.alias == 'my-server'`.

#### 1e. `test_default_ports_is_ssh`
Arrange: create `Host({'host_name': 'srv01'})`.
Assert: `host.ports == [22]`.

#### 1f. `test_is_correct_raises_typeerror` **[BUG-1]**
Arrange: create `Host({'host_name': 'srv01'})`.
Assert: calling `host.is_correct()` raises `TypeError`.
Rationale: `hasattr(self.host_name)` passes only one argument to `hasattr()`.

#### 1g. `test_fingerprint_returns_host_name`
Assert: `Host.fingerprint({'host_name': 'srv01'}) == 'srv01'`.

#### 1h. `test_default_empty_collections`
Arrange: create `Host({'host_name': 'srv01'})`.
Assert: `host.hostgroups == []`, `host.contacts == []`, `host.contact_groups == []`,
`host.templates == []`.

#### 1i. `test_macros_default_empty_dict`
Arrange: create `Host({'host_name': 'srv01'})`.
Assert: `host.macros == {}`.

---

### 2. `tests/test_item.py` (NEW) — `ItemTest`

Module docstring: `"""Tests for Item base class: init, pythonize/depythonize, resolve_monitoring_details, render, and chronicle."""`

#### 2a. `test_pythonize_splits_comma_separated_strings`
Arrange: create an `Application` with `hostgroups='a,b,c'` set after construction.
Call `app.pythonize()`.
Assert: `app.hostgroups == ['a', 'b', 'c']`.

#### 2b. `test_depythonize_joins_lists_to_string`
Arrange: set `app.hostgroups = ['b', 'a', 'c']`.
Call `app.depythonize()`.
Assert: `app.hostgroups == 'a,b,c'` (sorted, deduplicated).

#### 2c. `test_depythonize_deduplicates`
Arrange: set `app.contacts = ['alice', 'bob', 'alice']`.
Call `app.depythonize()`.
Assert: `app.contacts == 'alice,bob'`.

#### 2d. `test_pythonize_depythonize_roundtrip`
Arrange: set `app.hostgroups = ['web', 'linux']`.
Call `app.depythonize()` then `app.pythonize()`.
Assert: `set(app.hostgroups) == {'web', 'linux'}`.

#### 2e. `test_templates_order_preserved_by_depythonize`
Arrange: set `app.templates = ['base', 'override']`.
Call `app.depythonize()`.
Assert: `app.templates == 'base,override'` (NOT sorted — template order matters).

#### 2f. `test_resolve_monitoring_details_unique_attribute_deduplication`
Define a stub `MonitoringDetail` subclass with `property='filesystems'`,
`property_type=list`, `unique_attribute='path'`.  Two instances, same `path`.
Assert: `len(app.filesystems) == 1`.

#### 2g. `test_resolve_monitoring_details_unique_attribute_different_values`
Same setup but different `path` values.
Assert: `len(app.filesystems) == 2`.

#### 2h. `test_resolve_monitoring_details_property_attr`
Detail subclass with `property_attr='url'`.
Assert: `app.urls == ['http://x']` (scalar, not detail object).

#### 2i. `test_resolve_monitoring_details_property_flat`
Detail subclass with `property_flat=True`.
Assert: `app.role == 'primary'` (scalar, not detail object).

#### 2j. `test_resolve_monitoring_details_generic_scalar`
`property='generic'`, `property_type=str`.
Assert: `app.custom_field == 'hello'`.

#### 2k. `test_resolve_monitoring_details_generic_list`
`property='generic'`, `property_type=list`.
Assert: `app.tags == ['web', 'prod']`.

#### 2l. `test_record_in_chronicle_appends_entry`
Call `item.record_in_chronicle('created')` twice.
Assert: `len(item.object_chronicle) == 2`.

#### 2m. `test_record_in_chronicle_ignores_empty_message`
Call `item.record_in_chronicle('')`.
Assert: `item.object_chronicle == []`.

#### 2n. `test_dont_strip_attributes_bool_true`
Create a minimal Item subclass with `dont_strip_attributes = True`.
Construct with `params={'host_name': ' srv01 '}`.
Assert: `item.host_name == ' srv01 '` (whitespace preserved).

#### 2o. `test_dont_strip_attributes_list`
Create a minimal Item subclass with `dont_strip_attributes = ['description']`.
Construct with `params={'host_name': ' srv01 ', 'description': ' has spaces '}`.
Assert: `item.host_name == 'srv01'` (stripped), `item.description == ' has spaces '` (preserved).

#### 2p. `test_item_fingerprint_falls_back_to_host_name`
Create an Item with `host_name` but no `name`/`type`.
Call `item.fingerprint()`.
Assert: returns the host_name.

#### 2q. `test_item_fingerprint_raises_on_missing_all` **[BUG-3a]**
Create an Item with no `host_name`, `name`, or `type`.
Assert: calling `item.fingerprint()` raises `TypeError` (because `raise "string"`
is invalid in Python 3).

---

### 3. `tests/test_configparser.py` (NEW) — `CoshshConfigParserTest`

Module docstring: `"""Tests for CoshshConfigParser — isa section inheritance."""`

#### 3a. `test_isa_child_inherits_missing_keys_from_parent`
#### 3b. `test_isa_key_not_copied_to_child`
#### 3c. `test_isa_missing_parent_leaves_section_unchanged`
#### 3d. `test_section_without_isa_unaffected`
#### 3e. `test_isa_one_level_only`

*(Descriptions unchanged from v1 — write temp INI files using `tempfile`.)*

---

### 4. `tests/test_dependency.py` (NEW) — `DependencyTest`

Module docstring: `"""Tests for Dependency object construction and attribute access."""`

#### 4a. `test_dependency_stores_host_and_parent`
#### 4b. `test_dependency_is_not_item_subclass`
#### 4c. `test_dependency_missing_key_raises`

*(Descriptions unchanged from v1.)*

---

### 5. `tests/test_util.py` (NEW) — `UtilTest`

Module docstring: `"""Tests for coshsh.util helper functions."""`

#### 5a–5m: *(unchanged from v1)*

`compare_attr`, `is_attr`, `cleanout`, `normalize_dict` (two variants),
`clean_umlauts`, `sanitize_filename` (three variants), `odict` (two variants),
`substenv`.

---

### 6. `tests/test_datarecipient.py` (NEW) — `DatarecipientUnitTest`

Module docstring: `"""Unit tests for Datarecipient helper methods: too_much_delta(), count_objects()."""`

#### 6a–6h: *(unchanged from v1)*

`too_much_delta` (6 variants), `count_objects` (2 variants).

---

### 7. `tests/test_delta.py` (EXTEND) — add to `DeltaTest`

#### 7a. `test_too_much_delta_boundary_exactly_at_threshold`

*(Unchanged from v1.)*

---

### 8. `tests/test_details.py` (EXTEND) — add to `MonitoringDetailTest`

#### 8a. `test_comparison_operators`
Create two `MonitoringDetail` instances with different `monitoring_type`/`monitoring_0`
values; compare with `<`, `==`, `!=`, `>`, `<=`, `>=`.

#### 8b. `test_fingerprint_is_unique_per_instance`
Two otherwise-identical detail instances.
Assert: `d1.fingerprint() != d2.fingerprint()`.

#### 8c. `test_application_fingerprint_host_level`
Create a detail with `host_name` but no `application_name`/`application_type`.
Assert: `detail.application_fingerprint() == host_name`.

#### 8d. `test_application_fingerprint_app_level`
Create a detail with `host_name`, `application_name`, `application_type`.
Assert: fingerprint is `host_name+app_name+app_type`.

#### 8e. `test_application_fingerprint_raises_on_no_host` **[BUG-3b]**
Create a detail with `host_name=None` or `''`, no app info.
Assert: raises `TypeError` (Python 2 string raise).

#### 8f. `test_repr_format`
Assert: `repr(detail)` returns `"TYPE value"` format.

---

### 9. `tests/test_merge.py` (EXTEND) — add to `MergeTest`

#### 9a. `test_transform_hostname_strip_domain_skips_ip_address`
#### 9b. `test_transform_hostname_unknown_op_does_not_raise`

*(Unchanged from v1.)*

---

### 10. `tests/test_jinja2_extensions.py` (NEW) — `Jinja2ExtensionsTest`

Module docstring: `"""Tests for coshsh Jinja2 custom filters and helper functions."""`

#### 10a–10g: *(unchanged from v1)*

`filter_re_sub` (2), `filter_re_escape`, `get_re_flags` (2), `filter_custom_macros` (2).

#### 10h. `test_filter_rfc3986_encodes_text`
`filter_rfc3986('hello world')` returns a string starting with `'rfc3986://'`.

#### 10i. `test_is_re_match_returns_true_on_match`
`is_re_match('hello world', 'wor')` → `True`.

#### 10j. `test_is_re_match_returns_false_on_no_match`
`is_re_match('hello', 'xyz')` → `False`.

#### 10k. `test_is_re_match_with_flags`
`is_re_match('Hello', 'hello', 'i')` → `True`.

#### 10l. `test_filter_host_simple_output`
Create a stub host object with `host_name`, `contact_groups=[]`.
Assert: `filter_host(host)` starts with `'define host {'` and contains the host_name.

#### 10m. `test_filter_neighbor_applications_returns_host_apps`
Create a stub application with `host.applications = [app1, app2]`.
Assert: `filter_neighbor_applications(app1) == [app1, app2]`.

#### 10n. `test_global_environ_reads_env_var`
Set `os.environ['COSHSH_TEST_J2'] = 'testval'`.
Assert: `global_environ('COSHSH_TEST_J2') == 'testval'`.

#### 10o. `test_global_environ_returns_default_when_missing`
Assert: `global_environ('NONEXISTENT_VAR_XYZ', 'fallback') == 'fallback'`.

#### 10p. `test_global_environ_returns_empty_string_when_missing_no_default`
Assert: `global_environ('NONEXISTENT_VAR_XYZ') == ''`.

---

### 11. `tests/test_recipes.py` (EXTEND) — add to `RecipesTest`

#### 11a. `test_recipe_env_key_sets_os_environ`
#### 11b. `test_recipe_get_datasource_returns_none_for_unknown_name`
#### 11c. `test_recipe_get_datarecipient_returns_none_for_unknown_name`

*(Unchanged from v1.)*

#### 11d. `test_recipe_count_after_objects_raises_typeerror` **[BUG-2]**
Set up a recipe with at least one datarecipient.
Assert: calling `recipe.count_after_objects()` raises `TypeError`.
Rationale: `sum(0, [list])` on line 565 has reversed arguments.

#### 11e. `test_recipe_max_delta_parsing_colon_split`
Create a recipe with `max_delta='10:20'`.
Assert: `recipe.max_delta == (10, 20)`.

#### 11f. `test_recipe_max_delta_parsing_single_value_duplicated`
Create a recipe with `max_delta='15'`.
Assert: `recipe.max_delta == (15, 15)`.

#### 11g. `test_recipe_assemble_removes_orphaned_applications`
Add a host and an application whose `host_name` does not match any host.
Call `recipe.assemble()`.
Assert: the orphaned application is removed from `recipe.objects['applications']`.

#### 11h. `test_recipe_assemble_creates_hostgroup_objects`
Add a host with `host.hostgroups = ['web-servers']`.
Call `recipe.assemble()`.
Assert: `'web-servers' in recipe.objects['hostgroups']`.

#### 11i. `test_recipe_collect_returns_false_on_datasource_exception`
Use a datasource that raises `DatasourceNotAvailable` from `read()`.
Assert: `recipe.collect()` returns `False`.

---

### 12. `tests/test_vault.py` (EXTEND) — add to `VaultTest`

#### 12a. `test_vault_get_returns_none_for_missing_key`
#### 12b. `test_vault_getall_returns_list_of_values`

*(Unchanged from v1.)*

---

### 13. `tests/test_contacts.py` (EXTEND) — add to `ContactsTest`

#### 13a. `test_generic_contact_clean_name_replaces_umlauts`

*(Unchanged from v1.)*

#### 13b. `test_contact_notification_period_fallback`
Create a `Contact` with `notification_period='24x7'` but no
`host_notification_period` or `service_notification_period`.
Assert: `contact.host_notification_period == '24x7'` and
`contact.service_notification_period == '24x7'`.

---

### 14. `tests/test_templaterule.py` (NEW) — `TemplateRuleTest`

Module docstring: `"""Tests for TemplateRule construction and default attributes."""`

#### 14a. `test_default_attributes`
`rule = TemplateRule(template='mytemplate')`.
Assert: `rule.needsattr is None`, `rule.isattr is None`, `rule.suffix == 'cfg'`,
`rule.for_tool == 'nagios'`, `rule.self_name == 'application'`,
`rule.unique_attr == 'name'`, `rule.unique_config is None`.

#### 14b. `test_custom_attributes`
`rule = TemplateRule(needsattr='os', isattr='linux', template='os_linux',
for_tool='prometheus', suffix='yml')`.
Assert all attributes match the constructor arguments.

#### 14c. `test_str_representation`
Assert: `str(rule)` contains `'needsattr='` and `'template='`.

---

### 15. `tests/test_contactgroup.py` (NEW) — `ContactGroupTest`

Module docstring: `"""Tests for ContactGroup construction and fingerprint."""`

#### 15a. `test_construction_and_fingerprint`
`cg = ContactGroup({'contactgroup_name': 'admins'})`.
Assert: `cg.contactgroup_name == 'admins'`, `cg.fingerprint() == 'admins'`,
`cg.members == []`.

#### 15b. `test_str_representation`
Assert: `str(cg)` contains `'admins'`.

---

### 16. `tests/test_datasource.py` (NEW) — `DatasourceUnitTest`

Module docstring: `"""Unit tests for Datasource.add(), find(), get(), and host linking."""`

These use a concrete datasource instance from a test recipe.

#### 16a. `test_add_host_stores_by_fingerprint`
Add a host to a datasource.
Assert: `ds.find('hosts', host.host_name)` is `True`.
Assert: `ds.get('hosts', host.host_name)` returns the host object.

#### 16b. `test_add_application_links_to_host`
Add a host, then add an application with the same `host_name`.
Assert: `app.host == host`.

#### 16c. `test_add_records_in_chronicle`
Add a host.
Assert: `len(host.object_chronicle) >= 1`.
Assert: `'datasource'` appears in the chronicle message.

#### 16d. `test_get_returns_none_for_missing_fingerprint`
Assert: `ds.get('hosts', 'nonexistent')` returns `None`.

#### 16e. `test_find_returns_false_for_missing`
Assert: `ds.find('hosts', 'nonexistent')` is `False`.

#### 16f. `test_getall_returns_all_objects`
Add two hosts.
Assert: `len(ds.getall('hosts')) == 2`.

#### 16g. `test_getall_returns_empty_for_missing_type`
Assert: `ds.getall('nonexistent_type') == []`.

---

### 17. `tests/test_generic.py` (EXTEND) — add to `GenericApplicationTest`

#### 17a. `test_generic_application_render_returns_zero_without_details`
Create a GenericApplication with no processes/filesystems/ports.
Call `app.render(template_cache, jinja2, recipe)`.
Assert: returns `0` and `app.config_files` is empty.

---

### 18. `tests/test_package.py` (EXTEND) — add to `PackageTest`

#### 18a. `test_application_lower_columns_normalised`
`app = Application({'host_name': 'h', 'name': 'MyApp', 'type': 'WEB'})`.
Assert: `app.name == 'myapp'`, `app.type == 'web'`.

---

## Acceptance criteria

1. All pre-existing 100 tests continue to pass.
2. All new tests pass, except tests explicitly marked **[BUG]** which must FAIL (they
   document latent defects).
3. Every new test file has a module docstring and a `<Component>Test` class name.
4. Every new test method has a one-line docstring.
5. No `print()` calls, no `assertTrue(x == y)` patterns, no unused imports.
6. `git log --oneline` shows one commit per test file (or per logical group).

---

## Out of scope

- Fixing BUG-1, BUG-2, BUG-3a, BUG-3b (separate fix-bugs spec/PR).
- Adding test infrastructure for the pushgateway in-process path (requires mocking
  `prometheus_client`; defer to a dedicated metrics spec).
- `max_delta_action` external command execution (integration test, not unit test; defer).
- Vault exception hierarchy (`VaultNotReady`, `VaultCorrupt`, etc.) — not raised by
  any reachable code path in the current test fixtures; defer.
- `set_recipe_sys_path` / `unset_recipe_sys_path` — sys.path manipulation is fragile
  to test in isolation without side effects; defer.
- `Recipe >>>` shorthand — requires a test cookbook fixture; include if trivial to
  add to an existing config, otherwise defer.
- Datasource dead code (`return 'i do not exist'` on line 236) — cosmetic; note in
  comments but no dedicated test.
