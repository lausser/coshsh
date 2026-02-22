"""Tests for TemplateRule construction and default attributes."""

import unittest
from coshsh.templaterule import TemplateRule


class TemplateRuleTest(unittest.TestCase):

    def test_default_attributes(self):
        """TemplateRule with only template= has correct defaults."""
        rule = TemplateRule(template='mytemplate')
        self.assertIsNone(rule.needsattr)
        self.assertIsNone(rule.isattr)
        self.assertEqual(rule.suffix, 'cfg')
        self.assertEqual(rule.for_tool, 'nagios')
        self.assertEqual(rule.self_name, 'application')
        self.assertEqual(rule.unique_attr, 'name')
        self.assertIsNone(rule.unique_config)
        self.assertEqual(rule.template, 'mytemplate')

    def test_custom_attributes(self):
        """TemplateRule stores all custom constructor arguments."""
        rule = TemplateRule(
            needsattr='os', isattr='linux', template='os_linux',
            for_tool='prometheus', suffix='yml',
        )
        self.assertEqual(rule.needsattr, 'os')
        self.assertEqual(rule.isattr, 'linux')
        self.assertEqual(rule.template, 'os_linux')
        self.assertEqual(rule.for_tool, 'prometheus')
        self.assertEqual(rule.suffix, 'yml')

    def test_str_representation(self):
        """str(rule) contains needsattr and template fields."""
        rule = TemplateRule(needsattr='os', template='os_linux')
        s = str(rule)
        self.assertIn('needsattr=', s)
        self.assertIn('template=', s)
        self.assertIn('os', s)
        self.assertIn('os_linux', s)
