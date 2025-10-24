# Coshsh Test Writing Guide

This guide explains how to write modern, well-documented, and readable tests for coshsh.

## Table of Contents

1. [General Principles](#general-principles)
2. [Test Structure](#test-structure)
3. [Naming Conventions](#naming-conventions)
4. [Documentation](#documentation)
5. [Assertions](#assertions)
6. [Common Patterns](#common-patterns)
7. [Examples](#examples)

## General Principles

### 1. Clarity Over Cleverness
Tests should be **obvious** and **easy to understand**. Someone reading your test should immediately understand:
- What is being tested
- How it's being tested
- What the expected result is

### 2. One Concept Per Test
Each test should verify **one specific behavior**. If a test has multiple unrelated assertions, split it into multiple tests.

### 3. Descriptive Names
Test names should clearly describe what they test. Use the pattern:
```python
def test_<what>_<condition>_<expected_result>(self):
```

### 4. Comprehensive Documentation
Every test should have a docstring explaining:
- **What** is being tested
- **Why** it's important
- **How** the test works
- Any special setup or assumptions

### 5. Type Hints
All test methods should have type hints for parameters and return values.

## Test Structure

### Standard Test Layout

```python
from __future__ import annotations

import os
import unittest
from typing import Any, Dict, List, Optional

from tests.common_coshsh_test import CommonCoshshTest
import coshsh


class MyFeatureTest(CommonCoshshTest):
    """Test suite for MyFeature functionality.

    This test suite verifies that MyFeature correctly handles:
    - Feature aspect 1
    - Feature aspect 2
    - Edge cases and error conditions

    Test Configuration:
        Uses test recipes in tests/recipes/test_myfeature/
        Requires config file: etc/myfeature.cfg
    """

    def test_feature_basic_functionality(self) -> None:
        """Test that MyFeature works in the basic case.

        Verifies that when given valid input X, MyFeature produces
        expected output Y.

        Setup:
            - Creates a recipe with standard configuration
            - Loads test data from CSV

        Assertions:
            - Output files are created
            - Output contains expected content
        """
        # Arrange: Set up the test data
        self.setUpConfig("etc/myfeature.cfg", "test_recipe")

        # Act: Execute the feature
        recipe = self.generator.get_recipe("test_recipe")
        recipe.collect()

        # Assert: Verify the results
        self.assertEqual(len(recipe.objects['hosts']), 5)
        self.assertFileExists("var/objects/output/hosts/test_host.cfg")

    def test_feature_handles_edge_case(self) -> None:
        """Test that MyFeature handles edge case Z correctly.

        ... detailed docstring ...
        """
        pass
```

### Using setUp and tearDown

```python
class MyTest(CommonCoshshTest):
    """Test suite with custom setup."""

    def setUp(self) -> None:
        """Set up test environment.

        Creates:
            - Test recipe configuration
            - Sample data files
            - Output directories
        """
        super().setUp()
        # Custom setup here
        self.test_data = {"key": "value"}

    def tearDown(self) -> None:
        """Clean up after test.

        Removes:
            - Temporary files
            - Output directories
        """
        # Custom cleanup here
        super().tearDown()
```

## Naming Conventions

### Test Class Names
- End with `Test`
- Describe what's being tested
- Use PascalCase

```python
# Good
class DatasourceCSVTest(CommonCoshshTest):
class PluginLoadingTest(CommonCoshshTest):
class RecipeCollectionTest(CommonCoshshTest):

# Bad
class TestStuff(CommonCoshshTest):
class Tests(CommonCoshshTest):
```

### Test Method Names
- Start with `test_`
- Use snake_case
- Be descriptive

```python
# Good
def test_datasource_reads_csv_file_correctly(self):
def test_recipe_collection_with_empty_datasource(self):
def test_plugin_loading_fails_with_invalid_syntax(self):

# Bad
def test_1(self):
def test_csv(self):
def test_stuff(self):
```

### Variable Names in Tests

```python
# Good - Clear and descriptive
recipe = self.generator.get_recipe("production")
csv_datasource = recipe.get_datasource("main_csv")
expected_host_count = 42

# Bad - Unclear abbreviations
r = self.generator.get_recipe("production")
ds = recipe.get_datasource("main_csv")
n = 42
```

## Documentation

### Test Class Docstring

Every test class should have a comprehensive docstring:

```python
class ApplicationLoadingTest(CommonCoshshTest):
    """Test suite for application plugin loading and identification.

    This suite verifies that:
    - Application plugins are correctly discovered and loaded
    - The __mi_ident__ function correctly identifies applications
    - Application class priority is respected (user > default)
    - Multiple class paths work correctly

    Test Data:
        Uses recipes in tests/recipes/test_app_loading/
        Test configuration: etc/app_loading.cfg

    Related:
        See also: test_classes.py for general class loading tests
    """
```

### Test Method Docstring

Every test method should explain what, why, and how:

```python
def test_datasource_csv_reads_all_columns(self) -> None:
    """Test that CSV datasource reads all columns from the file.

    This is critical because the CSV datasource must preserve all
    columns, even those not explicitly mapped, for flexible downstream
    processing.

    Test Setup:
        1. Create a CSV file with 10 columns
        2. Configure a CSV datasource pointing to the file
        3. Read the datasource

    Expected Behavior:
        - All 10 columns are present in the resulting host objects
        - Column data types are correctly inferred
        - Empty columns are handled gracefully

    Edge Cases Tested:
        - Columns with special characters in names
        - Columns with missing values
        - Columns with only whitespace
    """
```

## Assertions

### Use Descriptive Assertions

```python
# Bad - Unclear what's being tested
self.assertTrue(len(hosts) == 5)
self.assertTrue('test_host' in hosts)

# Good - Clear intent
self.assertEqual(
    len(hosts), 5,
    "Should load exactly 5 hosts from test CSV"
)
self.assertIn(
    'test_host', hosts,
    "Host 'test_host' should be in loaded hosts"
)

# Even Better - Use helper methods
self.assertDictHasKey(hosts, 'test_host')
```

### Custom Assertion Methods

CommonCoshshTest provides helper methods:

```python
# Check file exists
self.assertFileExists(
    "var/objects/hosts/test_host.cfg",
    "Host configuration file should be created"
)

# Check file contains content
self.assertFileContains(
    "var/objects/hosts/test_host.cfg",
    "host_name test_host",
    "Config should contain host_name directive"
)

# Check dictionary has key
self.assertDictHasKey(
    recipe.objects,
    'hosts',
    "Recipe should have hosts object type"
)
```

### Assertion Messages

Always provide clear messages for assertions:

```python
# Bad
self.assertEqual(recipe.render_errors, 0)

# Good
self.assertEqual(
    recipe.render_errors, 0,
    f"Recipe should render without errors, but had {recipe.render_errors} errors"
)

# Even Better - Show context
self.assertEqual(
    recipe.render_errors, 0,
    f"Recipe '{recipe.name}' should render without errors. "
    f"Errors: {recipe.render_errors}. "
    f"Check {recipe.log_file} for details."
)
```

## Common Patterns

### Testing Plugin Loading

```python
def test_plugin_loads_for_matching_type(self) -> None:
    """Test that plugin loads when type matches pattern.

    Verifies the __mi_ident__ function correctly identifies
    its target applications.
    """
    # Arrange: Set up config and load plugins
    self.setUpConfig("etc/coshsh.cfg", "test_app")
    recipe = self.generator.get_recipe("test_app")

    # Act: Create application with matching type
    params = {"type": "linux", "name": "os", "host_name": "test"}
    app = coshsh.application.Application(params)

    # Assert: Verify correct class was loaded
    self.assertIsInstance(
        app, coshsh.application.Linux,
        "Application with type='linux' should be Linux instance"
    )
```

### Testing File Generation

```python
def test_recipe_generates_host_config_files(self) -> None:
    """Test that recipe generates configuration files for all hosts.

    Ensures the complete workflow of collect -> assemble -> render -> output
    produces the expected config files.
    """
    # Arrange
    self.setUpConfig("etc/coshsh.cfg", "test_recipe")
    recipe = self.generator.get_recipe("test_recipe")

    # Act
    recipe.collect()
    recipe.assemble()
    recipe.render()
    recipe.output()

    # Assert
    expected_hosts = ['test_host_1', 'test_host_2', 'test_host_3']

    for host_name in expected_hosts:
        config_file = f"var/objects/test/dynamic/hosts/{host_name}/host.cfg"

        self.assertFileExists(
            config_file,
            f"Config file should exist for host {host_name}"
        )

        self.assertFileContains(
            config_file,
            f"host_name {host_name}",
            f"Config should contain correct host_name for {host_name}"
        )
```

### Testing Error Conditions

```python
def test_datasource_raises_exception_for_missing_file(self) -> None:
    """Test that datasource raises DatasourceNotAvailable for missing file.

    This ensures graceful error handling when configured datasource
    files don't exist.
    """
    # Arrange
    self.setUpConfig("etc/bad_config.cfg", "test_recipe")
    recipe = self.generator.get_recipe("test_recipe")
    ds = recipe.get_datasource("missing_csv")

    # Act & Assert
    with self.assertRaises(coshsh.datasource.DatasourceNotAvailable) as context:
        ds.open()

    self.assertIn(
        "does not exist",
        str(context.exception),
        "Exception message should explain that file doesn't exist"
    )
```

### Testing with Environment Variables

```python
def test_config_substitutes_environment_variables(self) -> None:
    """Test that config parser substitutes %VAR% with environment values.

    Verifies the %ENV_VAR% substitution feature works correctly.
    """
    # Arrange: Set environment variable
    os.environ['TEST_DIR'] = '/opt/test'

    try:
        # Act: Load config with %TEST_DIR%
        self.setUpConfig("etc/env_test.cfg", "test_recipe")
        recipe = self.generator.get_recipe("test_recipe")
        ds = recipe.get_datasource("env_ds")

        # Assert: Variable was substituted
        self.assertEqual(
            ds.dir, "/opt/test/data",
            "Config should substitute %TEST_DIR% with environment value"
        )
    finally:
        # Cleanup: Remove environment variable
        del os.environ['TEST_DIR']
```

## Examples

### Complete Example: Well-Documented Test

```python
from __future__ import annotations

import os
import unittest
from typing import Any, Dict

from tests.common_coshsh_test import CommonCoshshTest
import coshsh


class CSVDatasourceTest(CommonCoshshTest):
    """Test suite for CSV file datasource functionality.

    This suite verifies that the CSV datasource correctly:
    - Reads hosts from CSV files
    - Reads applications from CSV files
    - Reads monitoring details from CSV files
    - Handles missing files gracefully
    - Processes comments in CSV files
    - Substitutes environment variables

    Test Data:
        Located in: tests/recipes/csv_test/data/
        Config: etc/csv_test.cfg

    CSV Format:
        - Hosts: host_name,address,type,os
        - Applications: host_name,name,type,component
        - Details: host_name,name,type,monitoring_type,monitoring_0
    """

    def test_csv_datasource_reads_hosts_from_file(self) -> None:
        """Test that CSV datasource correctly reads hosts from CSV file.

        This test verifies the basic functionality of reading host
        definitions from a CSV file and creating Host objects.

        Test Data:
            File: csv_test_hosts.csv
            Contains 3 hosts with different operating systems

        Expected Behavior:
            - 3 Host objects are created
            - Each host has correct attributes (name, address, type, os)
            - Attributes are normalized (lowercase where appropriate)

        Assertions:
            - Number of loaded hosts is correct
            - Host objects exist in recipe.objects['hosts']
            - Host attributes match CSV data
        """
        # Arrange: Load config and prepare recipe
        self.setUpConfig("etc/csv_test.cfg", "csv_test")
        recipe = self.generator.get_recipe("csv_test")

        # Act: Read datasource
        datasource = recipe.get_datasource("csv_main")
        datasource.open()
        datasource.read(objects=recipe.objects)
        datasource.close()

        # Assert: Verify hosts were loaded correctly
        hosts = recipe.objects.get('hosts', {})

        self.assertEqual(
            len(hosts), 3,
            f"Should load 3 hosts from CSV, but loaded {len(hosts)}"
        )

        # Verify specific host exists
        self.assertIn(
            'test_linux_host',
            hosts,
            "Host 'test_linux_host' should be loaded from CSV"
        )

        # Verify host attributes
        linux_host = hosts['test_linux_host']
        self.assertEqual(
            linux_host.address,
            "192.168.1.10",
            "Host address should match CSV data"
        )
        self.assertEqual(
            linux_host.os,
            "linux",
            "OS should be lowercase (normalized)"
        )

    def test_csv_datasource_handles_missing_file_gracefully(self) -> None:
        """Test that CSV datasource handles missing files without crashing.

        When a CSV file doesn't exist, the datasource should:
        - Log a warning
        - Continue processing other files
        - Not crash the entire recipe

        This is important because in production, some CSV files
        (like contacts or details) may not always exist.
        """
        # Arrange
        self.setUpConfig("etc/csv_test.cfg", "csv_missing")
        recipe = self.generator.get_recipe("csv_missing")
        datasource = recipe.get_datasource("csv_missing")

        # Act: Try to read from datasource with missing file
        datasource.open()
        datasource.read(objects=recipe.objects)
        datasource.close()

        # Assert: Should not crash, but hosts dict should be empty or minimal
        hosts = recipe.objects.get('hosts', {})

        # The datasource should handle missing files gracefully
        # We expect either 0 hosts or only hosts from existing files
        self.assertLessEqual(
            len(hosts), 0,
            "Missing CSV files should result in 0 hosts loaded"
        )

    def test_csv_datasource_skips_comment_lines(self) -> None:
        """Test that CSV datasource correctly skips lines starting with #.

        CSV files can contain comment lines for documentation.
        These should be ignored during parsing.

        Test Data:
            CSV file with 5 data rows and 3 comment rows

        Expected:
            Only 5 hosts are created (comments are ignored)
        """
        # Arrange
        self.setUpConfig("etc/csv_test.cfg", "csv_comments")
        recipe = self.generator.get_recipe("csv_comments")
        datasource = recipe.get_datasource("csv_comments")

        # Act
        datasource.open()
        datasource.read(objects=recipe.objects)
        datasource.close()

        # Assert
        hosts = recipe.objects.get('hosts', {})

        self.assertEqual(
            len(hosts), 5,
            "Should load 5 hosts (comment lines should be skipped)"
        )


if __name__ == '__main__':
    unittest.main()
```

## Best Practices Checklist

When writing a test, ask yourself:

- [ ] Does the test name clearly describe what's being tested?
- [ ] Does the test have a comprehensive docstring?
- [ ] Are all variables descriptively named?
- [ ] Are assertions clear with helpful messages?
- [ ] Is the test focused on one specific behavior?
- [ ] Does the test follow Arrange-Act-Assert pattern?
- [ ] Are edge cases considered?
- [ ] Is cleanup handled properly?
- [ ] Would a new developer understand this test?

## Anti-Patterns to Avoid

### ❌ Don't: Unclear Assertions
```python
# Bad
self.assertTrue(len(hosts) > 0)
self.assertTrue(hosts[0].name == "test")
```

### ✅ Do: Clear Assertions
```python
# Good
self.assertGreater(
    len(hosts), 0,
    "Should load at least one host from CSV"
)
self.assertEqual(
    hosts[0].name, "test",
    "First host should have name 'test'"
)
```

### ❌ Don't: Multiple Concepts in One Test
```python
# Bad - Testing multiple unrelated things
def test_everything(self):
    # Test CSV loading
    # Test plugin loading
    # Test rendering
    # Test output
```

### ✅ Do: One Concept Per Test
```python
# Good - Separate focused tests
def test_csv_loading(self):
    # Only test CSV loading

def test_plugin_loading(self):
    # Only test plugin loading

def test_rendering(self):
    # Only test rendering
```

### ❌ Don't: Magic Numbers
```python
# Bad
self.assertEqual(len(hosts), 42)
```

### ✅ Do: Named Constants
```python
# Good
EXPECTED_HOST_COUNT = 42  # Number of hosts in test CSV file
self.assertEqual(len(hosts), EXPECTED_HOST_COUNT)
```

---

## Summary

Good tests are:
1. **Clear**: Anyone can understand what they test
2. **Documented**: Docstrings explain why and how
3. **Focused**: One behavior per test
4. **Descriptive**: Names and assertions are self-explanatory
5. **Maintainable**: Easy to update when code changes

Following these guidelines will make the coshsh test suite a valuable asset for development and debugging.
