"""Tests for recipe attribute hand-down to datasources and datarecipients."""
import os
import io
import urllib
from coshsh.host import Host
from coshsh.application import Application
from tests.common_coshsh_test import CommonCoshshTest


class RecipeAttrsTest(CommonCoshshTest):

    def test_create_recipe_hand_down(self):
        """Datarecipients inherit their objects_dir from recipe config and explicit override."""
        self.setUpConfig("etc/coshsh.cfg", "test12")
        r = self.generator.get_recipe("test12")

        dr_simplesample = r.get_datarecipient('simplesample')
        self.assertEqual(dr_simplesample.objects_dir, "/tmp")
        self.assertEqual(dr_simplesample.recipe_objects_dir, r.objects_dir)
        dr_simplesample2 = r.get_datarecipient('simplesample2')
        self.assertEqual(dr_simplesample2.objects_dir, "./var/objects/test1")
        self.assertEqual(dr_simplesample2.recipe_objects_dir, r.objects_dir)
        dr_default = r.get_datarecipient('default')
        self.assertEqual(dr_default.objects_dir, "./var/objects/test12")
        self.assertEqual(dr_default.recipe_objects_dir, r.objects_dir)

        r.collect()
        r.assemble()
        r.render()
        r.output()
        # written by datarecipient_coshsh_default
        self.assertTrue(os.path.exists("var/objects/test12/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test12/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test12/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test12/dynamic/hosts/test_host_1/os_windows_default.cfg"))
        with io.open("var/objects/test12/dynamic/hosts/test_host_1/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertIn('os_windows_default_check_unittest', os_windows_default_cfg)
        # written by simplesample2 which has its own objects_dir
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_1/os_windows_default.cfg"))

    def test_create_recipe_hand_down_implicit_default_dr(self):
        """Implicit default datarecipient is created when no explicit one is configured."""
        self.setUpConfig("etc/coshsh.cfg", "test12a")
        r = self.generator.get_recipe("test12a")
        ds1 = r.get_datasource('csv10.1')
        ds2 = r.get_datasource('csv10.2')
        ds3 = r.get_datasource('csv10.3')
        ds1.objects = r.objects
        ds2.objects = r.objects
        ds3.objects = r.objects

        dr_simplesample = r.get_datarecipient("simplesample")
        self.assertEqual(dr_simplesample.objects_dir, "/tmp")
        self.assertEqual(dr_simplesample.recipe_objects_dir, self.generator.recipes['test12a'].objects_dir)
        dr_simplesample2 = r.get_datarecipient("simplesample2")
        self.assertEqual(dr_simplesample2.objects_dir, "./var/objects/test1")
        self.assertEqual(dr_simplesample2.recipe_objects_dir, self.generator.recipes['test12a'].objects_dir)
        dr_default = r.get_datarecipient("datarecipient_coshsh_default")
        self.assertEqual(dr_default.objects_dir, "./var/objects/test12")
        self.assertEqual(dr_default.recipe_objects_dir, self.generator.recipes['test12a'].objects_dir)

        r.collect()
        r.assemble()
        r.render()
        r.output()
        # written by datarecipient_coshsh_default
        self.assertTrue(os.path.exists("var/objects/test12/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test12/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test12/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test12/dynamic/hosts/test_host_1/os_windows_default.cfg"))
        with io.open("var/objects/test12/dynamic/hosts/test_host_1/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
            self.assertIn('os_windows_default_check_unittest', os_windows_default_cfg)
        # written by simplesample2 which has its own objects_dir
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_1/os_windows_default.cfg"))

    def test_datasource_attributes_in_tpl(self):
        """Datasource attributes (password) are URL-encoded before injection into rendered templates."""
        self.setUpConfig("etc/coshsh.cfg", "oracleds2tpl")
        r = self.generator.get_recipe("oracleds2tpl")
        ds = r.get_datasource('csv10.1')
        ds.objects = r.objects
        bash_breaker = u"*(;!&haha,friss!das!du!blöde!shell!"
        bash_breaker_encoded = 'rfc3986://' + urllib.request.pathname2url(bash_breaker)
        setattr(ds, "sid", "ORCL1234")
        setattr(ds, "username", "zosch")
        setattr(ds, "password", bash_breaker)

        host = Host({
            'host_name': 'testhost',
            'address': '127.0.0.1',
            'alias': 'hosttest',
        })
        app = Application({
            'host_name': 'testhost',
            'name': 'eventhandlerdb',
            'type': 'oraappindsdb',
        })
        r.collect()
        ds.add('hosts', host)
        ds.add('applications', app)
        r.assemble()
        r.render()
        self.assertEqual(len(self.generator.recipes['oracleds2tpl'].objects['applications']), 3)
        self.generator.recipes['oracleds2tpl'].output()
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/testhost/app_oraappindsdb_default.cfg"))
        with io.open("var/objects/test1/dynamic/hosts/testhost/app_oraappindsdb_default.cfg") as f:
            app_oraappindsdb_default_cfg = f.read()
        self.assertIn("!" + bash_breaker_encoded + " --sql", app_oraappindsdb_default_cfg)


class RunSafetySettingValidationTest(CommonCoshshTest):
    """Cookbook values that must refuse the run rather than degrade it (spec 007).

    These three settings share a property that most cookbook keys do not: a
    value coshsh cannot interpret means the operator's intent for a *safety*
    control is unknown. Guessing a default there is how a recipe ends up
    silently dropped, which is the failure mode FR-016 forbids.
    """

    def make(self, name, **overrides):
        """Construct one recipe directly, bypassing the cookbook file."""
        recipe = {
            'classes_dir': '/tmp', 'objects_dir': '/tmp', 'templates_dir': '/tmp',
            'datasources': 'datasource',
        }
        recipe.update(overrides)
        self.generator.add_recipe(name=name, **recipe)
        return self.generator.get_recipe(name)

    def assert_refused(self, **overrides):
        """Assert this config raises RecipeInvalidConfig naming the offending key."""
        from coshsh.recipe import RecipeInvalidConfig
        with self.assertRaises(RecipeInvalidConfig) as caught:
            self.make('refused', **overrides)
        message = str(caught.exception)
        for key in overrides:
            self.assertIn(key, message,
                          "the message must name the setting, got: %s" % message)

    # --- max_render_error_pct (new setting) ----------------------------------

    def test_max_render_error_pct_rejects_uninterpretable_values(self):
        """Non-numeric, empty, negative, and above-100 values all refuse the run."""
        self.setUpConfig("etc/coshsh.cfg", "test10")
        for bad in ["abc", "", "-5", "250", "100.1"]:
            self.assert_refused(max_render_error_pct=bad)

    def test_max_render_error_pct_accepts_its_domain(self):
        """Absent is None; 0, 12.5 and 100 are the floats they look like."""
        self.setUpConfig("etc/coshsh.cfg", "test10")
        self.assertIsNone(self.make('none').render_tally.max_error_pct)
        self.assertEqual(self.make('zero', max_render_error_pct="0").render_tally.max_error_pct, 0.0)
        self.assertEqual(self.make('half', max_render_error_pct="12.5").render_tally.max_error_pct, 12.5)
        self.assertEqual(self.make('full', max_render_error_pct="100").render_tally.max_error_pct, 100.0)

    def test_hundred_percent_never_aborts_even_when_everything_fails(self):
        """100 is the ceiling and the comparison is strict >, so it cannot abort.

        Distinguished from 250 (which is rejected) deliberately: they behave
        identically at runtime, but 250 is a typo rather than a permissive
        policy, and silently accepting it would accept a value the cookbook
        author plainly did not mean.
        """
        self.setUpConfig("etc/coshsh.cfg", "test10")
        r = self.make('ceiling', max_render_error_pct="100")
        r.render_tally.attempts = 10
        r.render_tally.errors = 10
        self.assertEqual(r.render_tally.error_pct, 100.0)
        self.assertFalse(r.render_tally.too_many_errors)

    # --- tolerate_missing_templates (new setting) ----------------------------

    def test_tolerate_missing_templates_rejects_anything_but_yes_or_no(self):
        """Following the git_init idiom means yes/no, not "anything not 'yes'"."""
        self.setUpConfig("etc/coshsh.cfg", "test10")
        for bad in ["maybe", "true", "1", ""]:
            self.assert_refused(tolerate_missing_templates=bad)

    def test_tolerate_missing_templates_accepts_yes_and_no(self):
        """Absent defaults to no; the two documented values parse to bools."""
        self.setUpConfig("etc/coshsh.cfg", "test10")
        self.assertFalse(self.make('tmt_absent').tolerate_missing_templates)
        self.assertFalse(self.make('tmt_no', tolerate_missing_templates="no").tolerate_missing_templates)
        self.assertTrue(self.make('tmt_yes', tolerate_missing_templates="yes").tolerate_missing_templates)

    # --- max_delta (existing setting, stricter reaction only) ----------------

    def test_max_delta_rejects_malformed_values(self):
        """FR-016a: a malformed max_delta refuses the run instead of dropping the recipe."""
        self.setUpConfig("etc/coshsh.cfg", "test10")
        for bad in ["abc", "10:abc", "10:20:30"]:
            self.assert_refused(max_delta=bad)

    def test_max_delta_accepted_values_are_unchanged(self):
        """The point of the change is the reaction, not the domain.

        Every value that parses today must still parse to exactly the same
        tuple, or this stops being a bugfix and becomes a breaking change.
        """
        self.setUpConfig("etc/coshsh.cfg", "test10")
        self.assertEqual(self.make('md_absent').max_delta, ())
        self.assertEqual(self.make('md_single', max_delta="10").max_delta, (10, 10))
        self.assertEqual(self.make('md_pair', max_delta="10:20").max_delta, (10, 20))
