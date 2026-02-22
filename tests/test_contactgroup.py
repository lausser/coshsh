"""Tests for ContactGroup construction and fingerprint."""

import os
import sys
import unittest

# Ensure we can import coshsh modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from coshsh.contactgroup import ContactGroup


class ContactGroupTest(unittest.TestCase):

    def test_construction_and_fingerprint(self):
        """ContactGroup stores name, has fingerprint, and defaults members to empty list."""
        cg = ContactGroup({'contactgroup_name': 'admins'})
        self.assertEqual(cg.contactgroup_name, 'admins')
        self.assertEqual(cg.fingerprint(), 'admins')
        self.assertEqual(cg.members, [])

    def test_str_representation(self):
        """str(contactgroup) contains the group name."""
        cg = ContactGroup({'contactgroup_name': 'admins'})
        self.assertIn('admins', str(cg))
