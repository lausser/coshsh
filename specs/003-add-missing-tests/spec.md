# Spec 003 — Add Missing Tests for Untested Features

**Branch:** `003-add-missing-tests`
**Date:** 2026-02-22
**Baseline:** 100 tests passing (after spec 002)

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

## File map: test file → source module(s) under test

| Test file (new or extended) | Source modules |
|-----------------------------|----------------|
| `tests/test_host.py` (NEW) | `coshsh/host.py` |
| `tests/test_item.py` (NEW) | `coshsh/item.py` |
| `tests/test_configparser.py` (NEW) | `coshsh/configparser.py` |
| `tests/test_dependency.py` (NEW) | `coshsh/dependency.py` |
| `tests/test_util.py` (NEW) | `coshsh/util.py` |
| `tests/test_datarecipient.py` (NEW) | `coshsh/datarecipient.py` |
| `tests/test_delta.py` (EXTEND) | `coshsh/datarecipient.py` — `too_much_delta()` |
| `tests/test_details.py` (EXTEND) | `coshsh/item.py` — `resolve_monitoring_details()` |
| `tests/test_merge.py` (EXTEND) | `coshsh/datasource.py` — `transform_hostname()` |
| `tests/test_jinja2_extensions.py` (NEW) | `coshsh/jinja2_extensions.py` |
| `tests/test_recipes.py` (EXTEND) | `coshsh/recipe.py` — `@MAPPING_`, `env_*`, `substsecret()` |
| `tests/test_vault.py` (EXTEND) | `coshsh/vault.py` — `get()` missing key, `getall()` |
| `tests/test_contacts.py` (EXTEND) | `coshsh/contact.py` — umlaut replacement |

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

#### 1e. `test_default_ports_is_ssh` **[BUG]**
Arrange: create `Host({'host_name': 'srv01'})`.
Assert: `host.ports == [22]`.
*(This test should pass — confirming the SSH default is in place.)*

#### 1f. `test_is_correct_raises_typeerror` **[BUG — exposes latent defect]**
Arrange: create `Host({'host_name': 'srv01'})`.
Assert: calling `host.is_correct()` raises `TypeError`.
Rationale: `hasattr(self.host_name)` passes only one argument to `hasattr()`; Python
requires exactly two (`hasattr(obj, name)`).  This call will raise `TypeError` at
runtime whenever `is_correct()` is invoked.  The test documents the bug so it will be
caught immediately if `is_correct()` is ever wired up.

#### 1g. `test_fingerprint_returns_host_name`
Arrange: create `Host({'host_name': 'srv01'})`.
Assert: `Host.fingerprint({'host_name': 'srv01'}) == 'srv01'`.

---

### 2. `tests/test_item.py` (NEW) — `ItemTest`

Module docstring: `"""Tests for Item base class: pythonize/depythonize, resolve_monitoring_details, and render."""`

These tests use minimal MonitoringDetail stubs — no recipe or datasource needed.

#### 2a. `test_pythonize_splits_comma_separated_strings`
Arrange: create an `Application` with `hostgroups='a,b,c'` set after construction.
Call `app.pythonize()`.
Assert: `app.hostgroups == ['a', 'b', 'c']`.

#### 2b. `test_depythonize_joins_lists_to_string`
Arrange: create an `Application`; set `app.hostgroups = ['b', 'a', 'c']`.
Call `app.depythonize()`.
Assert: `app.hostgroups == 'a,b,c'` (sorted, deduplicated).

#### 2c. `test_depythonize_deduplicates`
Arrange: set `app.contacts = ['alice', 'bob', 'alice']`.
Call `app.depythonize()`.
Assert: `app.contacts == 'alice,bob'`.

#### 2d. `test_pythonize_depythonize_roundtrip`
Arrange: create an `Application`; set `app.hostgroups = ['web', 'linux']`.
Call `app.depythonize()` then `app.pythonize()`.
Assert: `set(app.hostgroups) == {'web', 'linux'}`.

#### 2e. `test_templates_order_preserved_by_depythonize`
Arrange: set `app.templates = ['base', 'override']`.
Call `app.depythonize()`.
Assert: `app.templates == 'base,override'` (NOT sorted — template order matters for
Nagios inheritance).

#### 2f. `test_resolve_monitoring_details_unique_attribute_deduplication`
Arrange: define a minimal `MonitoringDetail` subclass with `property='filesystems'`,
`property_type=list`, `unique_attribute='path'`.  Create two instances with the same
`path` value and add both to `app.monitoring_details`.
Call `app.resolve_monitoring_details()`.
Assert: `len(app.filesystems) == 1` (second replaces first).

#### 2g. `test_resolve_monitoring_details_unique_attribute_different_values`
Same setup but different `path` values.
Assert: `len(app.filesystems) == 2`.

#### 2h. `test_resolve_monitoring_details_property_attr`
Arrange: detail subclass with `property='urls'`, `property_type=list`,
`property_attr='url'`; detail instance has `.url = 'http://x'`.
Call `resolve_monitoring_details()`.
Assert: `app.urls == ['http://x']` (the scalar attribute, not the detail object).

#### 2i. `test_resolve_monitoring_details_property_flat`
Arrange: detail subclass with `property='role'`, `property_type=<not list, not dict>`,
`property_flat=True`; detail instance has `.role = 'primary'`.
Call `resolve_monitoring_details()`.
Assert: `app.role == 'primary'` (scalar, not the detail object).

#### 2j. `test_resolve_monitoring_details_generic_scalar`
Arrange: detail subclass with `property='generic'`, `property_type=str`;
detail has `.attribute = 'custom_field'`, `.value = 'hello'`.
Assert: after resolution `app.custom_field == 'hello'`.

#### 2k. `test_resolve_monitoring_details_generic_list`
Arrange: `property='generic'`, `property_type=list`; detail's `.dictionary =
{'tags': ['web', 'prod']}`.
Assert: after resolution `app.tags == ['web', 'prod']`.

#### 2l. `test_record_in_chronicle_appends_entry`
Arrange: `item = Host({'host_name': 'h1'})`.
Call `item.record_in_chronicle('created')` twice.
Assert: `len(item.object_chronicle) == 2`.

#### 2m. `test_record_in_chronicle_ignores_empty_message`
Call `item.record_in_chronicle('')`.
Assert: `item.object_chronicle == []`.

---

### 3. `tests/test_configparser.py` (NEW) — `CoshshConfigParserTest`

Module docstring: `"""Tests for CoshshConfigParser — isa section inheritance."""`

No full generator needed.  Write temp INI files using `tempfile` or string buffers.

#### 3a. `test_isa_child_inherits_missing_keys_from_parent`
INI content: parent section with keys `a=1`, `b=2`; child section with `isa=parent`,
`b=99`.
After `read()`: assert child has `a == '1'` (inherited) and `b == '99'` (not overwritten).

#### 3b. `test_isa_key_not_copied_to_child`
Assert: child section does NOT have an `isa` key after read (the `isa` key itself must
not be inherited).

#### 3c. `test_isa_missing_parent_leaves_section_unchanged`
Child section references a parent section that does not exist.
Assert: no exception; child section has only its own keys.

#### 3d. `test_section_without_isa_unaffected`
A plain section with no `isa` key.
Assert: its keys are unchanged after read.

#### 3e. `test_isa_one_level_only`
Three sections: grandparent → parent (`isa=grandparent`) → child (`isa=parent`).
Assert: child inherits keys from parent but NOT from grandparent (one-level only).

---

### 4. `tests/test_dependency.py` (NEW) — `DependencyTest`

Module docstring: `"""Tests for Dependency object construction and attribute access."""`

#### 4a. `test_dependency_stores_host_and_parent`
`d = Dependency({'host_name': 'child', 'parent_host_name': 'parent'})`.
Assert: `d.host_name == 'child'`, `d.parent_host_name == 'parent'`.

#### 4b. `test_dependency_is_not_item_subclass`
Assert: `not isinstance(d, coshsh.item.Item)`.

#### 4c. `test_dependency_missing_key_raises`
Assert: `Dependency({'host_name': 'h'})` raises `KeyError` (no `parent_host_name`).

---

### 5. `tests/test_util.py` (NEW) — `UtilTest`

Module docstring: `"""Tests for coshsh.util helper functions."""`

#### 5a. `test_compare_attr_matches_regex`
`compare_attr('linux', 'lin.*')` → `True`.

#### 5b. `test_compare_attr_no_match`
`compare_attr('windows', 'lin.*')` → `False`.

#### 5c. `test_is_attr_case_insensitive_exact_match`
`is_attr('Linux', 'linux')` → `True`; `is_attr('Linux', 'lin')` → `False`.

#### 5d. `test_cleanout_removes_specified_chars`
`cleanout('hello_world!', chars='_!')` → `'helloworld'`.

#### 5e. `test_normalize_dict_lowercases_keys`
`normalize_dict({'Host': ' srv01 ', 'OS': 'Linux'})` → `{'host': 'srv01', 'os': 'Linux'}`.

#### 5f. `test_normalize_dict_lowercases_values_for_listed_columns`
`normalize_dict({'os': 'Linux'}, lower_columns=['os'])` → `{'os': 'linux'}`.

#### 5g. `test_clean_umlauts_replaces_all`
`clean_umlauts('ÄÖÜäöüß')` → `'AeOeUeaeoeueß'` (or whatever the mapping is — verify
against the actual replacement table in the source).

#### 5h. `test_sanitize_filename_replaces_slash`
`sanitize_filename('a/b')` returns a string not containing `/`.

#### 5i. `test_sanitize_filename_appends_md5_suffix_when_changed`
`sanitize_filename('a/b')` differs from `'ab'` (MD5 fragment appended to avoid
collisions).

#### 5j. `test_sanitize_filename_unchanged_input_no_suffix`
`sanitize_filename('valid_name')` → `'valid_name'` exactly (no suffix when nothing
was replaced).

#### 5k. `test_odict_preserves_insertion_order`
Insert keys `'c'`, `'a'`, `'b'`.  Assert `list(od) == ['c', 'a', 'b']`.

#### 5l. `test_odict_setitem_getitem_delitem`
Basic dict contract: set, get, delete, len.

#### 5m. `test_substenv_expands_env_var`
Set `os.environ['COSHSH_TEST_VAR'] = 'hello'`.
`substenv('%COSHSH_TEST_VAR%')` → `'hello'`.

---

### 6. `tests/test_datarecipient.py` (NEW) — `DatarecipientUnitTest`

Module docstring: `"""Unit tests for Datarecipient helper methods: too_much_delta(), count_objects()."""`

Uses a concrete `DatarecipientCoshshDefault` instance or a minimal stub — no full
recipe pipeline.

#### 6a. `test_too_much_delta_returns_false_when_not_configured`
A datarecipient with no `safe_output` / `max_delta` configured.
Assert: `dr.too_much_delta() == False`.

#### 6b. `test_too_much_delta_positive_threshold_not_exceeded`
`old_objects = (10, 20)`, `new_objects = (9, 19)`, `max_delta = 50` (positive = bidirectional).
Assert: `too_much_delta() == False`.

#### 6c. `test_too_much_delta_positive_threshold_exceeded_on_shrinkage`
`old = (100, 200)`, `new = (40, 80)`, `max_delta = 50`.
Assert: `too_much_delta() == True`.

#### 6d. `test_too_much_delta_positive_threshold_exceeded_on_growth`
`old = (40, 80)`, `new = (100, 200)`, `max_delta = 50`.
Assert: `too_much_delta() == True`.

#### 6e. `test_too_much_delta_negative_threshold_only_shrinkage`
`old = (100, 200)`, `new = (40, 80)`, `max_delta = -50` (negative = shrinkage only).
Assert: `too_much_delta() == True`.

#### 6f. `test_too_much_delta_negative_threshold_growth_ignored`
`old = (40, 80)`, `new = (100, 200)`, `max_delta = -50`.
Assert: `too_much_delta() == False`.

#### 6g. `test_count_objects_empty_dir_returns_zero_zero`
Point a datarecipient at a freshly-created empty temp directory.
Assert: `dr.count_objects() == (0, 0)`.

#### 6h. `test_count_objects_counts_hosts_and_nonempty_cfg_files`
Create a temp dir with a `hosts/myhost/app.cfg` file containing content and an empty
`hosts/myhost/empty.cfg`.
Assert: hosts count = 1, application files count = 1 (empty file excluded).

---

### 7. `tests/test_delta.py` (EXTEND) — add to `DeltaTest`

#### 7a. `test_too_much_delta_boundary_exactly_at_threshold`
Full-pipeline run where delta equals the threshold exactly (boundary condition).
Assert: `too_much_delta()` returns `False` (threshold is strictly greater-than, not ≥).
*(Verify actual operator in source before writing.)*

---

### 8. `tests/test_details.py` (EXTEND) — add to `MonitoringDetailTest`

#### 8a. `test_comparison_operators`
Create two `MonitoringDetail` instances; compare with `<`, `==`, `!=`.
Assert: comparisons are consistent with `(monitoring_type, str(monitoring_0))` tuple
ordering.

#### 8b. `test_fingerprint_is_unique_per_instance`
Create two otherwise-identical detail instances.
Assert: `d1.fingerprint() != d2.fingerprint()` (identity-based).

---

### 9. `tests/test_merge.py` (EXTEND) — add to `MergeTest`

#### 9a. `test_transform_hostname_strip_domain_skips_ip_address`
`ds.hostname_transform_ops = [{'strip_domain': None}]`.
`ds.transform_hostname('192.168.1.1')` → `'192.168.1.1'` (unchanged).

#### 9b. `test_transform_hostname_unknown_op_does_not_raise`
`ds.hostname_transform_ops = [{'unknown_op': None}]`.
Assert: no exception, input returned unchanged (or logged as warning).

---

### 10. `tests/test_jinja2_extensions.py` (NEW) — `Jinja2ExtensionsTest`

Module docstring: `"""Tests for coshsh Jinja2 custom filters and helper functions."""`

These are pure-function unit tests; no recipe pipeline needed.

#### 10a. `test_filter_re_sub_replaces_pattern`
`filter_re_sub('hello world', 'world', 'earth')` → `'hello earth'`.

#### 10b. `test_filter_re_sub_with_flags`
`filter_re_sub('Hello World', 'hello', 'Hi', 'i')` → `'Hi World'`.

#### 10c. `test_filter_re_escape_escapes_special_chars`
`filter_re_escape('a.b+c')` → `'a\\.b\\+c'`.

#### 10d. `test_get_re_flags_single_flag`
`get_re_flags('i') == re.IGNORECASE`.

#### 10e. `test_get_re_flags_combined_flags`
`get_re_flags('im') == re.IGNORECASE | re.MULTILINE`.

#### 10f. `test_filter_custom_macros_merges_and_prefixes`
Input: `custom_macros={'KEY': 'val'}`, `macros={'OTHER': 'x'}`.
Assert: result has `_KEY` and `_OTHER` keys.

#### 10g. `test_filter_custom_macros_adds_underscore_prefix`
Input macro key without leading `_`.
Assert: output key has `_` prefix.

---

### 11. `tests/test_recipes.py` (EXTEND) — add to `RecipesTest`

#### 11a. `test_recipe_env_key_sets_os_environ`
Write a temp cookbook config with a recipe section containing `env_COSHSH_SPEC003 = sentinel`.
After `Generator.read_cookbook()`, assert: `os.environ.get('COSHSH_SPEC003') == 'sentinel'`.

#### 11b. `test_recipe_get_datasource_returns_none_for_unknown_name`
Use any existing recipe.
Assert: `r.get_datasource('no_such_ds')` returns `None`.

#### 11c. `test_recipe_get_datarecipient_returns_none_for_unknown_name`
Assert: `r.get_datarecipient('no_such_dr')` returns `None`.

---

### 12. `tests/test_vault.py` (EXTEND) — add to `VaultTest`

#### 12a. `test_vault_get_returns_none_for_missing_key`
Open vault with correct password.
Assert: `r_prod.vaults[0].get('$NONEXISTENT$')` returns `None`.

#### 12b. `test_vault_getall_returns_list_of_values`
Open vault with correct password.
Assert: `r_prod.vaults[0].getall()` returns a non-empty list.

---

### 13. `tests/test_contacts.py` (EXTEND) — add to `ContactsTest`

#### 13a. `test_generic_contact_clean_name_replaces_umlauts`
Create a `GenericContact` (or `Contact`) with a name containing German umlauts.
Assert: the resulting `contact_name` attribute contains only ASCII characters.

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

- Fixing the `Host.is_correct()` bug (spec 004 or a separate PR).
- Adding test infrastructure for the pushgateway in-process path (requires mocking
  `prometheus_client`; defer to a dedicated metrics spec).
- `max_delta_action` external command execution (integration test, not unit test; defer).
- Vault exception hierarchy (`VaultNotReady`, `VaultCorrupt`, etc.) — not raised by
  any reachable code path in the current test fixtures; defer.
