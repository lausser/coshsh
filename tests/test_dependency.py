"""Tests for Dependency object construction and attribute access."""

import unittest
from coshsh.dependency import Dependency
from coshsh.item import Item


class DependencyTest(unittest.TestCase):

    def test_dependency_stores_host_and_parent(self):
        """Dependency stores host_name and parent_host_name from params."""
        dep = Dependency({'host_name': 'child01', 'parent_host_name': 'router01'})
        self.assertEqual(dep.host_name, 'child01')
        self.assertEqual(dep.parent_host_name, 'router01')

    def test_dependency_is_not_item_subclass(self):
        """Dependency does not inherit from Item."""
        self.assertFalse(issubclass(Dependency, Item))

    def test_dependency_missing_key_raises(self):
        """Dependency raises KeyError when required key is missing."""
        with self.assertRaises(KeyError):
            Dependency({'host_name': 'child01'})
