"""Integration tests for template render error counting and the abort gate (spec 007).

The fixture is tests/recipes/renderr/ driven by tests/etc/coshsh_renderr.cfg.
Every host it emits contributes exactly one render attempt with one known
outcome, so the counts and percentages asserted here are exact rather than
approximate -- see the module docstring of
tests/recipes/renderr/classes/datasource_renderr.py for why.
"""

import hashlib
import os
import shutil

from tests.common_coshsh_test import CommonCoshshTest


def checksum_tree(path):
    """Return a digest covering every file's path and content under *path*.

    WHY path-and-content rather than a directory mtime: the requirement is that
    an aborted run adds, changes, and deletes nothing. An mtime check would miss
    a file rewritten with identical content, and a file count would miss a
    changed one. Hashing the sorted (relpath, bytes) pairs catches all three.
    """
    digest = hashlib.sha256()
    if not os.path.exists(path):
        return "MISSING"
    for root, dirs, files in os.walk(path):
        dirs.sort()
        for name in sorted(files):
            full = os.path.join(root, name)
            digest.update(os.path.relpath(full, path).encode())
            with open(full, "rb") as f:
                digest.update(f.read())
    return digest.hexdigest()


class RenderErrorsTest(CommonCoshshTest):

    COOKBOOK = "etc/coshsh_renderr.cfg"

    def load(self, name, cookbook=None):
        """Build one named recipe from a cookbook and return it.

        Loaded per test rather than in setUp because the cookbook holds a dozen
        recipes with deliberately different tolerances, and a test should build
        only the one it is about.
        """
        self.setUpConfig(cookbook or self.COOKBOOK, name)
        r = self.generator.get_recipe(name)
        self.assertIsNotNone(r, "recipe %s was not created" % name)
        return r

    def render_only(self, name, cookbook=None):
        """Run collect/assemble/render but not output -- for pure counting checks."""
        r = self.load(name, cookbook)
        r.collect()
        r.assemble()
        r.render()
        return r

    # --- US1: a missing template is counted as a failure ----------------------

    def test_missing_template_counts_as_a_render_error(self):
        """US1-1: a template rule pointing at a non-existent file is a failure.

        A rule that fires against an absent template produced no output, which
        is a failed rendering whatever the cause. Guards against the absence
        being treated as a non-event just because nothing threw.
        """
        r = self.render_only("renderr_missing")
        # 1 good host + 1 host whose template does not exist
        self.assertEqual(r.render_tally.attempts, 2)
        self.assertEqual(r.render_tally.missing, 1)
        self.assertEqual(r.render_tally.errors, 0)
        self.assertEqual(r.render_errors, 1)

    def test_missing_template_counts_once_per_affected_object(self):
        """US1-3: the count follows renderings, not distinct template names."""
        r = self.render_only("renderr_missing_many")
        # 2 good + 5 hosts sharing the one absent template
        self.assertEqual(r.render_tally.attempts, 7)
        # Not deduplicated to 1: five objects failed to be rendered.
        self.assertEqual(r.render_tally.missing, 5)
        self.assertEqual(r.render_errors, 5)

    def test_tolerate_missing_templates_keeps_the_count_but_drops_the_percentage(self):
        """US1-2 / FR-001b / FR-001c: tolerated absences stay visible, stop counting."""
        r = self.render_only("renderr_tolerate")
        # Same fixture as the test above, only the recipe flag differs.
        self.assertEqual(r.render_tally.attempts, 7)
        # Still counted and still logged -- the flag governs the percentage only.
        self.assertEqual(r.render_tally.missing, 5)
        # ... but excluded from the failure count ...
        self.assertEqual(r.render_errors, 0)
        # ... and from the denominator, leaving only the 2 good renderings.
        self.assertEqual(r.render_tally.accountable_attempts, 2)
        self.assertEqual(r.render_tally.error_pct, 0.0)

    # --- US2: abort the run when too many renderings fail ---------------------

    def test_abort_leaves_the_previous_output_byte_for_byte_intact(self):
        """US2-1/US2-2, FR-008, SC-003: the requirement the feature exists for.

        Publishing a half-rendered configuration is worse than publishing
        nothing: a monitoring system silently stops checking whatever failed to
        render. So an aborted run must not add, change, or delete a single byte
        of what the last good run produced.
        """
        objects_dir = "var/objects/renderr_preserve"

        # 1. A clean run publishes.
        self.setUpConfig(self.COOKBOOK, "renderr_preserve")
        self.generator.run()
        before = checksum_tree(objects_dir)
        self.assertNotEqual(before, "MISSING", "the good run published nothing")

        # 2. The same recipe, same objects_dir, now with failing renderings.
        self.clean_generator()
        self.setUpConfig("etc/coshsh_renderr_broken.cfg", "renderr_preserve")
        self.generator.run()
        r = self.generator.get_recipe("renderr_preserve")
        self.assertTrue(r.render_tally.too_many_errors, "the run should have aborted")

        # 3. Nothing was touched.
        self.assertEqual(before, checksum_tree(objects_dir))

    def test_failures_within_tolerance_publish_normally(self):
        """US2-3 / FR-007: 2% failures against a 5% tolerance is not an abort."""
        self.setUpConfig(self.COOKBOOK, "renderr_within_tolerance")
        self.generator.run()
        r = self.generator.get_recipe("renderr_within_tolerance")
        self.assertEqual(r.render_tally.attempts, 100)
        self.assertEqual(r.render_tally.errors, 2)
        self.assertEqual(r.render_tally.error_pct, 2.0)
        self.assertFalse(r.render_tally.too_many_errors)
        self.assertTrue(os.path.exists("var/objects/renderr_within/dynamic/hosts"))

    def test_no_tolerance_configured_publishes_exactly_as_before(self):
        """US2-4 / FR-007: protection is opt-in; an unconfigured recipe is untouched.

        A recipe that declares no tolerance publishes whatever it managed to
        render, however much failed -- silence means "nobody has said what an
        unacceptable failure rate is here", not "abort on anything". Guessing
        on the operator's behalf would turn working unattended runs into
        refusals without warning.
        """
        self.setUpConfig(self.COOKBOOK, "renderr_no_tolerance")
        self.generator.run()
        r = self.generator.get_recipe("renderr_no_tolerance")
        self.assertIsNone(r.render_tally.max_error_pct)
        self.assertEqual(r.render_tally.errors, 5)
        self.assertEqual(r.render_tally.error_pct, 50.0)
        self.assertFalse(r.render_tally.too_many_errors)
        # Half its renderings failed and it still published -- as it does today.
        self.assertTrue(os.path.exists("var/objects/renderr_notol/dynamic/hosts"))

    def test_zero_objects_does_not_abort_and_does_not_divide_by_zero(self):
        """US2-5 / FR-015: an empty recipe has not demonstrated a failure."""
        self.setUpConfig(self.COOKBOOK, "renderr_empty")
        self.generator.run()
        r = self.generator.get_recipe("renderr_empty")
        self.assertEqual(r.render_tally.attempts, 0)
        self.assertEqual(r.render_tally.max_error_pct, 0.0)
        # The tolerance is zero and nothing failed, because nothing was tried.
        self.assertEqual(r.render_tally.error_pct, 0.0)
        self.assertFalse(r.render_tally.too_many_errors)

    # --- US3: an aborted run leaves the system ready for the next attempt -----

    def test_a_fixed_recipe_runs_again_after_an_abort_with_no_manual_cleanup(self):
        """US3-1 / FR-010 / SC-004: the abort releases the pid lock.

        An abort that left the lock behind would turn one broken template into a
        permanently stuck recipe -- every subsequent scheduled run would skip it
        with "already running" until someone logged in and deleted a file. The
        third run below is the proof that this does not happen; it uses the same
        recipe name, hence the same pid file, as the run that aborted.
        """
        objects_dir = "var/objects/renderr_preserve"

        self.setUpConfig(self.COOKBOOK, "renderr_preserve")
        self.generator.run()
        published = checksum_tree(objects_dir)

        self.clean_generator()
        self.setUpConfig("etc/coshsh_renderr_broken.cfg", "renderr_preserve")
        self.assertEqual(self.generator.run(), 1, "expected exactly one aborted recipe")

        # The template is "fixed" -- same recipe name, renderings succeed again.
        self.clean_generator()
        self.setUpConfig(self.COOKBOOK, "renderr_preserve")
        self.assertEqual(self.generator.run(), 0)
        r = self.generator.get_recipe("renderr_preserve")
        self.assertFalse(r.render_tally.too_many_errors)
        self.assertEqual(published, checksum_tree(objects_dir))
        self.assertFalse(os.path.exists(r.pid_file), "the pid lock was not released")

    def test_one_aborting_recipe_does_not_stop_the_others(self):
        """US3-3 / FR-014: an abort is scoped to its own recipe.

        A cookbook is often one file for a whole site. If a broken template in
        one recipe stopped the rest, a small local failure would become a
        site-wide outage -- strictly worse than the partial output the abort
        exists to prevent.
        """
        self.setUpConfig(self.COOKBOOK, "renderr_multi_bad,renderr_multi_good")
        aborted = self.generator.run()

        self.assertEqual(aborted, 1)
        bad = self.generator.get_recipe("renderr_multi_bad")
        good = self.generator.get_recipe("renderr_multi_good")
        self.assertTrue(bad.render_tally.too_many_errors)
        self.assertFalse(good.render_tally.too_many_errors)
        # The healthy recipe published exactly as it would have on its own.
        self.assertTrue(os.path.exists("var/objects/renderr_multi_good/dynamic/hosts"))
        self.assertEqual(checksum_tree("var/objects/renderr_multi_bad"), "MISSING")
