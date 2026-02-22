"""Tests for Host construction, attribute normalisation, and is_correct() validation."""

import unittest
from coshsh.host import Host
from tests.common_coshsh_test import CommonCoshshTest


class HostTest(CommonCoshshTest):

    def test_lower_columns_normalised_on_construction(self):
        """Host lower_columns are normalised to lowercase."""
        host = Host({'host_name': 'srv01', 'os': 'LINUX', 'hardware': 'X86', 'type': 'SERVER'})
        self.assertEqual(host.os, 'linux')
        self.assertEqual(host.hardware, 'x86')
        self.assertEqual(host.type, 'server')

    def test_lower_columns_non_string_set_to_none(self):
        """Non-string value for a lower_column is set to None."""
        host = Host({'host_name': 'srv01', 'os': 42})
        self.assertIsNone(host.os)

    def test_alias_defaults_to_host_name(self):
        """Host alias defaults to host_name when not supplied."""
        host = Host({'host_name': 'srv01'})
        self.assertEqual(host.alias, 'srv01')

    def test_alias_preserved_when_supplied(self):
        """Host alias is preserved when explicitly supplied."""
        host = Host({'host_name': 'srv01', 'alias': 'my-server'})
        self.assertEqual(host.alias, 'my-server')

    def test_default_ports_is_ssh(self):
        """Host default ports list contains SSH port 22."""
        host = Host({'host_name': 'srv01'})
        self.assertEqual(host.ports, [22])

    def test_is_correct_raises_typeerror(self):
        """[BUG-1] is_correct() raises TypeError due to hasattr() called with one argument."""
        host = Host({'host_name': 'srv01'})
        with self.assertRaises(TypeError):
            host.is_correct()

    def test_fingerprint_returns_host_name(self):
        """Host.fingerprint() returns the host_name value."""
        self.assertEqual(Host.fingerprint({'host_name': 'srv01'}), 'srv01')

    def test_default_empty_collections(self):
        """Host initialises with empty lists for hostgroups, contacts, contact_groups, templates."""
        host = Host({'host_name': 'srv01'})
        self.assertEqual(host.hostgroups, [])
        self.assertEqual(host.contacts, [])
        self.assertEqual(host.contact_groups, [])
        self.assertEqual(host.templates, [])

    def test_macros_default_empty_dict(self):
        """Host macros defaults to an empty dict."""
        host = Host({'host_name': 'srv01'})
        self.assertEqual(host.macros, {})
