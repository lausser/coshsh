"""Tests for the coshsh-cook CLI entry point with various cookbook configurations."""

import os
import io
import shutil
import subprocess
from tests.common_coshsh_test import CommonCoshshTest


class BinTest(CommonCoshshTest):

    def tearDown(self):
        shutil.rmtree("./var/objects/test1", True)
        shutil.rmtree("./var/objects/test1_mod", True)

    def test_coshsh_cook(self):
        """Verify that coshsh-cook generates expected host and service config files for the test4 recipe."""
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh.cfg --recipe test4", shell=True)
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg"))
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertIn('os_windows_default_check_unittest', os_windows_default_cfg)

    def test_create_template_tree(self):
        """Verify that coshsh-create-template-tree generates static service template files from a recipe."""
        os.makedirs("./var/objects/test1/static")
        self.assertTrue(os.path.exists("var/objects/test1/static"))
        self.assertTrue(os.path.exists("../bin/coshsh-create-template-tree"))
        subprocess.call("../bin/coshsh-create-template-tree --cookbook etc/coshsh.cfg --recipe test4 --template os_windows_fs", shell=True)
        self.assertTrue(os.path.exists("var/objects/test1/static/service_templates"))
        self.assertTrue(os.path.exists("var/objects/test1/static/service_templates/os_windows_fs.cfg"))
        self.assertTrue(os.path.exists("var/objects/test1/static/service_templates/os_windows.cfg"))

    def test_multiple_cookbooks(self):
        """Verify that passing multiple --cookbook flags generates output in each recipe output directory."""
        os.makedirs("./var/objects/test1/static")
        os.makedirs("./var/objects/test1_mod/static")
        self.assertTrue(os.path.exists("var/objects/test1/static"))
        self.assertTrue(os.path.exists("var/objects/test1_mod/static"))
        self.assertTrue(os.path.exists("../bin/coshsh-create-template-tree"))
        subprocess.call("../bin/coshsh-create-template-tree --cookbook etc/coshsh.cfg --cookbook etc/coshsh6.cfg --recipe test4 --template os_windows_fs", shell=True)
        self.assertTrue(os.path.exists("var/objects/test1_mod/static/service_templates"))
        self.assertTrue(os.path.exists("var/objects/test1_mod/static/service_templates/os_windows_fs.cfg"))
        self.assertTrue(os.path.exists("var/objects/test1_mod/static/service_templates/os_windows.cfg"))


class BinExitCodeTest(CommonCoshshTest):
    """Process exit codes for aborted runs and refused configs (spec 007).

    These matter because coshsh runs unattended from a scheduler. The scheduler
    only ever sees the exit code, so "templates broke, previous config
    preserved" (4) has to be distinguishable from "coshsh could not start" (2).
    """

    def tearDown(self):
        for leftover in ["renderr_abort", "renderr_badpct", "renderr_badpct_innocent",
                         "renderr_baddelta", "renderr_baddelta_innocent"]:
            shutil.rmtree("./var/objects/" + leftover, True)

    def cook(self, *args):
        return subprocess.call("../bin/coshsh-cook " + " ".join(args), shell=True)

    def test_aborted_recipe_exits_4(self):
        """FR-014a / SC-001a: an abort is a distinct, non-zero outcome."""
        rc = self.cook("--cookbook etc/coshsh_renderr.cfg --recipe RENDERR_ABORT")
        self.assertEqual(rc, 4)
        # Exit 4 means "nothing was published", so there must be nothing there.
        self.assertFalse(os.path.exists("var/objects/renderr_abort/dynamic/hosts"))

    def test_malformed_max_render_error_pct_exits_2_with_no_recipe_processed(self):
        """FR-016: the run refuses to start rather than dropping the bad recipe.

        The second assertion is the one that matters: the *other*, entirely
        valid recipe in the cookbook must not publish either. Letting it run
        would mean a successful-looking run whose output silently lacks every
        object the refused recipe owns -- the failure this exit code exists to
        prevent.
        """
        rc = self.cook("--cookbook etc/coshsh_renderr_badpct.cfg")
        self.assertEqual(rc, 2)
        self.assertFalse(os.path.exists("var/objects/renderr_badpct/dynamic/hosts"))
        self.assertFalse(os.path.exists("var/objects/renderr_badpct_innocent/dynamic/hosts"))

    def test_malformed_max_delta_exits_2_with_no_recipe_processed(self):
        """FR-016a: max_delta is a run-safety setting and refuses the run too.

        Same contract as max_render_error_pct above. Only structure is checked
        (one integer, or two separated by a colon) -- any integer value is
        meaningful, so an unparseable one is the only thing that can be wrong.
        """
        rc = self.cook("--cookbook etc/coshsh_renderr_baddelta.cfg")
        self.assertEqual(rc, 2)
        self.assertFalse(os.path.exists("var/objects/renderr_baddelta/dynamic/hosts"))
        self.assertFalse(os.path.exists("var/objects/renderr_baddelta_innocent/dynamic/hosts"))
