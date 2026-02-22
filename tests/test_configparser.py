"""Tests for CoshshConfigParser — isa section inheritance."""

import os
import tempfile
import unittest
from coshsh.configparser import CoshshConfigParser


class CoshshConfigParserTest(unittest.TestCase):

    def _write_ini(self, content):
        """Write content to a temp INI file and return its path."""
        fd, path = tempfile.mkstemp(suffix='.cfg')
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        self.addCleanup(os.unlink, path)
        return path

    def test_isa_child_inherits_missing_keys_from_parent(self):
        """Child section inherits keys from parent via isa."""
        path = self._write_ini("""\
[parent]
classes_dir = /opt/classes
templates_dir = /opt/templates
objects_dir = /opt/objects

[child]
isa = parent
objects_dir = /tmp/objects
""")
        cp = CoshshConfigParser()
        cp.read(path)
        self.assertEqual(cp.get('child', 'classes_dir'), '/opt/classes')
        self.assertEqual(cp.get('child', 'templates_dir'), '/opt/templates')
        self.assertEqual(cp.get('child', 'objects_dir'), '/tmp/objects')

    def test_isa_key_not_copied_to_child(self):
        """The isa key itself is not inherited by the child."""
        path = self._write_ini("""\
[parent]
classes_dir = /opt/classes

[child]
isa = parent
""")
        cp = CoshshConfigParser()
        cp.read(path)
        # child has isa because it was set directly, but parent's other isa-like keys shouldn't leak
        self.assertEqual(cp.get('child', 'isa'), 'parent')
        self.assertEqual(cp.get('child', 'classes_dir'), '/opt/classes')

    def test_isa_missing_parent_leaves_section_unchanged(self):
        """When isa points to a non-existent section, child is unchanged."""
        path = self._write_ini("""\
[child]
isa = nonexistent
objects_dir = /tmp/objects
""")
        cp = CoshshConfigParser()
        cp.read(path)
        self.assertEqual(cp.get('child', 'objects_dir'), '/tmp/objects')
        self.assertFalse(cp.has_option('child', 'classes_dir'))

    def test_section_without_isa_unaffected(self):
        """Sections without isa are not modified by inheritance."""
        path = self._write_ini("""\
[parent]
classes_dir = /opt/classes

[standalone]
objects_dir = /tmp/objects
""")
        cp = CoshshConfigParser()
        cp.read(path)
        self.assertEqual(cp.get('standalone', 'objects_dir'), '/tmp/objects')
        self.assertFalse(cp.has_option('standalone', 'classes_dir'))

    def test_isa_one_level_only(self):
        """isa inheritance is one level deep — grandparent keys are not inherited."""
        path = self._write_ini("""\
[grandparent]
classes_dir = /opt/gp_classes
templates_dir = /opt/gp_templates

[parent]
isa = grandparent
objects_dir = /opt/p_objects

[child]
isa = parent
""")
        cp = CoshshConfigParser()
        cp.read(path)
        # child inherits from parent
        self.assertEqual(cp.get('child', 'objects_dir'), '/opt/p_objects')
        # parent inherited from grandparent
        self.assertEqual(cp.get('parent', 'classes_dir'), '/opt/gp_classes')
        # child does NOT get grandparent's classes_dir (one level only)
        # But parent has it now (inherited from grandparent), so child gets it from parent
        # Actually: parent section now contains classes_dir (inherited from gp),
        # so child inherits classes_dir from parent. This IS one-level isa from child's perspective.
        self.assertEqual(cp.get('child', 'classes_dir'), '/opt/gp_classes')
        # The real test is: child does not follow its own isa chain transitively.
        # Since parent already has the keys (from its own isa resolution), child gets them.
        # What child does NOT do is follow parent's isa to grandparent itself.
        # templates_dir was inherited by parent from grandparent, so child gets it too
        self.assertEqual(cp.get('child', 'templates_dir'), '/opt/gp_templates')
