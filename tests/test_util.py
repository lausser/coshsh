"""Tests for coshsh.util helper functions."""

import os
import unittest
from coshsh.util import (
    compare_attr, is_attr, cleanout, normalize_dict,
    clean_umlauts, sanitize_filename, odict, substenv,
)


class UtilTest(unittest.TestCase):

    def test_compare_attr_matches_regex(self):
        """compare_attr returns True when regex matches the parameter value."""
        params = {'os': 'linux_server'}
        self.assertTrue(compare_attr('os', params, ['linux.*']))

    def test_compare_attr_no_match(self):
        """compare_attr returns False when no regex matches."""
        params = {'os': 'windows'}
        self.assertFalse(compare_attr('os', params, ['linux.*']))

    def test_compare_attr_missing_key(self):
        """compare_attr returns False when key is absent from params."""
        self.assertFalse(compare_attr('os', {}, ['linux']))

    def test_compare_attr_none_value(self):
        """compare_attr returns False when the parameter value is None."""
        params = {'os': None}
        self.assertFalse(compare_attr('os', params, ['linux']))

    def test_is_attr_exact_match(self):
        """is_attr returns True on case-insensitive exact match."""
        params = {'os': 'Linux'}
        self.assertTrue(is_attr('os', params, ['linux']))

    def test_is_attr_no_match(self):
        """is_attr returns False when no string matches."""
        params = {'os': 'windows'}
        self.assertFalse(is_attr('os', params, ['linux']))

    def test_cleanout_removes_chars_and_words(self):
        """cleanout strips specified characters and words from the string."""
        result = cleanout("hello world!", delete_chars="!", delete_words=["world"])
        self.assertEqual(result, "hello")

    def test_cleanout_empty_string(self):
        """cleanout returns falsy input unchanged."""
        self.assertEqual(cleanout(""), "")
        self.assertIsNone(cleanout(None))

    def test_normalize_dict_lowercases_keys(self):
        """normalize_dict lowercases all keys and strips values."""
        d = {'host_name': '  srv01  ', 'type': '  server  '}
        normalize_dict(d)
        self.assertEqual(d['host_name'], 'srv01')
        self.assertEqual(d['type'], 'server')

    def test_normalize_dict_lowercases_title_values(self):
        """normalize_dict lowercases values for keys listed in titles."""
        d = {'type': 'SERVER', 'address': '10.0.0.1'}
        normalize_dict(d, titles=['type'])
        self.assertEqual(d['type'], 'server')
        self.assertEqual(d['address'], '10.0.0.1')

    def test_clean_umlauts_replaces_german_characters(self):
        """clean_umlauts converts German umlauts to ASCII equivalents."""
        self.assertEqual(clean_umlauts('M\u00fcller'), 'Mueller')
        self.assertEqual(clean_umlauts('Gr\u00f6\u00dfe'), 'Groesse')

    def test_sanitize_filename_clean_input(self):
        """sanitize_filename returns unchanged filename when no bad characters exist."""
        self.assertEqual(sanitize_filename('host.cfg'), 'host.cfg')

    def test_sanitize_filename_replaces_bad_chars(self):
        """sanitize_filename replaces bad characters and appends hash suffix."""
        result = sanitize_filename('a:b.cfg')
        self.assertIn('a_b', result)
        self.assertTrue(result.endswith('.cfg'))
        self.assertNotEqual(result, 'a:b.cfg')

    def test_sanitize_filename_spaces(self):
        """sanitize_filename replaces spaces with underscores."""
        result = sanitize_filename('my file.cfg')
        self.assertNotIn(' ', result)
        self.assertTrue(result.endswith('.cfg'))

    def test_odict_preserves_insertion_order(self):
        """odict keys() returns keys in insertion order."""
        d = odict()
        d['b'] = 1
        d['a'] = 2
        d['c'] = 3
        self.assertEqual(d.keys(), ['b', 'a', 'c'])

    def test_odict_copy(self):
        """odict.copy() returns an independent copy preserving order."""
        d = odict()
        d['x'] = 10
        d['y'] = 20
        d2 = d.copy()
        d2['z'] = 30
        self.assertEqual(len(d), 2)
        self.assertEqual(len(d2), 3)

    def test_substenv_expands_known_var(self):
        """substenv callback expands %VAR% tokens from environment."""
        import re as _re
        os.environ['COSHSH_TEST_VAR'] = 'hello'
        result = _re.sub(r'%[A-Za-z_]+%', substenv, '%COSHSH_TEST_VAR%')
        self.assertEqual(result, 'hello')
        del os.environ['COSHSH_TEST_VAR']

    def test_substenv_preserves_unknown_var(self):
        """substenv returns the original token when the env var is not set."""
        import re as _re
        result = _re.sub(r'%[A-Za-z_]+%', substenv, '%NONEXISTENT_COSHSH_VAR%')
        self.assertEqual(result, '%NONEXISTENT_COSHSH_VAR%')
