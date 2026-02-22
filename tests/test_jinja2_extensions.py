"""Tests for coshsh Jinja2 custom filters and helper functions."""

import os
import unittest
from coshsh.jinja2_extensions import (
    filter_re_sub, filter_re_escape, get_re_flags, filter_custom_macros,
    filter_rfc3986, is_re_match, filter_host, filter_neighbor_applications,
    global_environ,
)


class Jinja2ExtensionsTest(unittest.TestCase):

    def test_filter_re_sub_basic(self):
        """filter_re_sub performs regex substitution."""
        result = filter_re_sub('hello world', 'world', 'earth')
        self.assertEqual(result, 'hello earth')

    def test_filter_re_sub_no_match(self):
        """filter_re_sub returns original string when pattern does not match."""
        result = filter_re_sub('hello world', 'xyz', 'abc')
        self.assertEqual(result, 'hello world')

    def test_filter_re_escape(self):
        """filter_re_escape escapes regex metacharacters."""
        result = filter_re_escape('a.b*c')
        self.assertIn('\\', result)
        self.assertNotEqual(result, 'a.b*c')

    def test_get_re_flags_ignorecase(self):
        """get_re_flags returns IGNORECASE flag for 'i' string."""
        import re
        flags = get_re_flags('i')
        self.assertTrue(flags & re.IGNORECASE)

    def test_get_re_flags_empty(self):
        """get_re_flags returns 0 for empty/None flag string."""
        self.assertEqual(get_re_flags(''), 0)
        self.assertEqual(get_re_flags(None), 0)

    def test_filter_custom_macros_dict(self):
        """filter_custom_macros formats macro dict into Nagios custom macro lines."""
        class Obj:
            macros = {'ENVIRONMENT': 'prod'}
            custom_macros = {}
        result = filter_custom_macros(Obj())
        self.assertIn('_ENVIRONMENT', result)
        self.assertIn('prod', result)

    def test_filter_custom_macros_empty(self):
        """filter_custom_macros returns empty string when no macros exist."""
        class Obj:
            pass
        result = filter_custom_macros(Obj())
        self.assertEqual(result, '')

    def test_filter_rfc3986_encodes_text(self):
        """filter_rfc3986 returns a string starting with rfc3986://."""
        result = filter_rfc3986('hello world')
        self.assertTrue(result.startswith('rfc3986://'))

    def test_is_re_match_returns_true_on_match(self):
        """is_re_match returns True when regex matches."""
        self.assertTrue(is_re_match('hello world', 'wor'))

    def test_is_re_match_returns_false_on_no_match(self):
        """is_re_match returns False when regex does not match."""
        self.assertFalse(is_re_match('hello', 'xyz'))

    def test_is_re_match_with_flags(self):
        """is_re_match supports flag strings like 'i' for case-insensitive."""
        self.assertTrue(is_re_match('Hello', 'hello', 'i'))

    def test_filter_host_simple_output(self):
        """filter_host returns a string starting with 'define host {' containing the hostname."""
        class StubHost:
            host_name = 'myhost01'
            contact_groups = []
            macros = {}
        result = filter_host(StubHost())
        self.assertIn('define host {', result)
        self.assertIn('myhost01', result)

    def test_filter_neighbor_applications_returns_host_apps(self):
        """filter_neighbor_applications returns all applications on the same host."""
        class StubApp:
            pass
        class StubHost:
            applications = []
        app1 = StubApp()
        app2 = StubApp()
        host = StubHost()
        host.applications = [app1, app2]
        app1.host = host
        result = filter_neighbor_applications(app1)
        self.assertEqual(result, [app1, app2])

    def test_global_environ_reads_env_var(self):
        """global_environ returns the value of a set environment variable."""
        os.environ['COSHSH_TEST_J2'] = 'testval'
        self.assertEqual(global_environ('COSHSH_TEST_J2'), 'testval')
        del os.environ['COSHSH_TEST_J2']

    def test_global_environ_returns_default_when_missing(self):
        """global_environ returns the default value when the variable is missing."""
        self.assertEqual(global_environ('NONEXISTENT_VAR_XYZ', 'fallback'), 'fallback')

    def test_global_environ_returns_empty_string_when_missing_no_default(self):
        """global_environ returns empty string when variable is missing and no default given."""
        self.assertEqual(global_environ('NONEXISTENT_VAR_XYZ'), '')
