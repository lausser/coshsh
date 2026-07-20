"""Tests for log file creation, log level filtering, and log content after a recipe run."""

import os
import io
import re
import shutil
import logging
from coshsh.util import setup_logging
from tests.common_coshsh_test import CommonCoshshTest


class LoggingTest(CommonCoshshTest):

    def tearDown(self):
        pass

    def test_log(self):
        """Verify log file is created, WARNING and INFO are written, DEBUG is filtered out."""
        shutil.rmtree("./var/log", True)
        os.makedirs("./var/log")
        setup_logging(logfile="zishsh.log", logdir="./var/log", scrnloglevel=logging.DEBUG, txtloglevel=logging.INFO)
        # default, wie im coshsh-cook
        setup_logging(logdir="./var/log", scrnloglevel=logging.INFO)
        logger = logging.getLogger('zishsh')
        logger.warning("i warn you")
        logger.info("i inform you")
        logger.debug("i spam you")
        self.assertTrue(os.path.exists("./var/log/zishsh.log"))
        with io.open('./var/log/zishsh.log') as x:
            zishshlog = x.read()
        self.assertIn("WARNING", zishshlog)
        self.assertIn("INFO", zishshlog)
        self.assertNotIn("DEBUG", zishshlog)

    def test_write(self):
        """Verify recipe run creates host config files and writes entries to the coshsh log."""
        self.setUpConfig("etc/coshsh.cfg", "test4")
        r = self.generator.get_recipe("test4")
        self.generator.run()
        self.assertTrue(hasattr(r.objects['hosts']['test_host_0'], 'config_files'))
        self.assertIn('host.cfg', r.objects['hosts']['test_host_0'].config_files['nagios'])
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg"))
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertIn('os_windows_default_check_unittest', os_windows_default_cfg)
        self.assertTrue(os.path.exists("./var/log/coshsh.log"))
        with io.open('./var/log/coshsh.log') as x:
            coshshlog = x.read()
        self.assertIn("test_host_0", coshshlog)


class RenderErrorLoggingTest(CommonCoshshTest):
    """What the log must say about failed renderings and aborted runs (spec 007).

    The counters answer "how bad is it"; the log is the only place that answers
    "which template, on which object, and why". Only two kinds are *counted*
    (missing and everything else), so if the log did not keep the individual
    failures distinguishable the finer detail would be lost entirely.
    """

    # WHY its own log dir and not ./var/log: LoggingTest above leaves logging
    # pointed at ./var/log and reads accumulated content back out of it, so a
    # class that wiped that directory would break a neighbour. coshsh_renderr.cfg
    # declares log_dir = ./var/log_renderr for exactly this reason.
    LOG_DIR = "./var/log_renderr"

    def tearDown(self):
        for leftover in ("renderr_all_kinds", "renderr_all_kinds_abort",
                         "renderr_multi_good", "renderr_notol"):
            shutil.rmtree("./var/objects/" + leftover, True)
        shutil.rmtree(self.LOG_DIR, True)

    def run_and_capture(self, recipe_name):
        """Run one recipe with a clean log and return (recipe, log text)."""
        shutil.rmtree(self.LOG_DIR, True)
        os.makedirs(self.LOG_DIR)
        self.setUpConfig("etc/coshsh_renderr.cfg", recipe_name)
        self.generator.run()
        with io.open(self.LOG_DIR + "/coshsh.log") as f:
            return self.generator.get_recipe(recipe_name), f.read()

    def test_each_failure_kind_is_individually_identifiable(self):
        """US4-1 / US4-2 / FR-012: three failures, three distinguishable messages."""
        r, log = self.run_and_capture("renderr_all_kinds")

        # One of each: good, broken (syntax), absent, and raising-at-render.
        self.assertEqual(r.render_tally.attempts, 4)
        self.assertEqual(r.render_tally.missing, 1)
        self.assertEqual(r.render_tally.errors, 2)

        # Missing: named as absent, and the template is named.
        self.assertIn("cannot find template renderr_gone", log)
        # Broken at load: named as a template error with a line number.
        self.assertIn("renderr_broken", log)
        self.assertIn("has an error in line", log)
        # Broken at render: names the template AND the object being rendered.
        self.assertIn("render exception in template renderr_raise", log)
        self.assertIn("renderr_raise_0", log)

    def test_summary_line_reports_failures_and_attempts(self):
        """US4-3 / FR-013: 'N problems' is unreadable without the denominator.

        Three failed renderings out of four is an emergency; three out of forty
        thousand is a note for the morning. The summary line has to carry both.
        """
        r, log = self.run_and_capture("renderr_all_kinds")
        self.assertIn("recipe renderr_all_kinds completed with 3 problems out of 4 rendering attempts", log)
        # ... and which kind they were. Since a template that fails to load is
        # reported once per run rather than once per object, this line is the
        # only place in the log the split survives.
        self.assertIn("[1 missing, 2 faulty]", log)

    def test_abort_line_reports_the_numbers_it_decided_on(self):
        """US2-1 / FR-011: the abort must show its work.

        An operator reading "aborted" needs to know whether the tolerance was
        far exceeded or only just, without re-running anything.
        """
        r, log = self.run_and_capture("renderr_all_kinds_abort")
        self.assertTrue(r.render_tally.too_many_errors)
        self.assertIn("recipe renderr_all_kinds_abort aborted", log)
        self.assertIn("3 of 4 renderings failed", log)   # failures and attempts
        self.assertIn("[1 missing, 2 faulty]", log)      # and of which kind
        self.assertIn("75.0000%", log)                    # the resulting percentage
        self.assertIn("maximum is 0.0%", log)             # the configured maximum

    def test_an_aborted_recipe_is_not_logged_as_completed(self):
        """FR-009 / US3-2: 'completed with N problems' reads as success-with-caveats.

        Both to an operator skimming a log and to anything scraping it. An
        aborted run published nothing, so claiming completion is simply false.
        """
        r, log = self.run_and_capture("renderr_all_kinds_abort")
        self.assertTrue(r.render_tally.too_many_errors)
        self.assertNotIn("recipe renderr_all_kinds_abort completed", log)
        self.assertIn("recipe renderr_all_kinds_abort aborted", log)

    def test_a_broken_template_is_reported_once_not_once_per_object(self):
        """A shared broken template is parsed and reported once; counts are per object.

        Five hosts reference one template with a syntax error. Reporting it five
        times would be five identical tracebacks -- at real scale, one broken
        template in a 60,000-object recipe would bury every other line in the
        log and re-parse the file 60,000 times. The failure *count* must stay
        per-object regardless, because five objects did fail to render.
        """
        r, log = self.run_and_capture("renderr_no_tolerance")

        # 5 good + 5 broken hosts, all five broken ones sharing one template
        self.assertEqual(r.render_tally.attempts, 10)
        self.assertEqual(r.render_errors, 5)
        # ... but the parse failure is reported exactly once
        self.assertEqual(log.count("has an error in line"), 1)
        # The other four are noted at DEBUG, which the file handler filters out
        # (it is pinned at INFO), so they appear on the console under --debug
        # and never here. That is what keeps the log file readable at scale.
        self.assertNotIn("renderr_broken_4", log)

    # The pattern an unattended-run log scraper is expected to match. Pinned
    # here so it cannot be reworded by accident: the wording predates this
    # feature and deployments already grep for it.
    SUCCESS_PATTERN = re.compile(r"recipe \S+ completed with 0 problems")

    def test_a_clean_run_logs_a_matchable_success_line(self):
        """"Everything is fine" must be a positive statement, not an absence.

        coshsh runs unattended, so a scraper cannot conclude success from the
        lack of error lines -- no output at all looks exactly the same as coshsh
        never having started. There has to be a line that says so.
        """
        r, log = self.run_and_capture("renderr_multi_good")
        self.assertEqual(r.render_errors, 0)
        self.assertTrue(self.SUCCESS_PATTERN.search(log),
                        "no success line a scraper could match in:\n%s" % log)

    def test_the_success_pattern_does_not_match_a_run_that_failed(self):
        """The other half of the contract: it must not fire when things went wrong.

        A pattern that matches a clean run is only useful if it stays silent for
        an aborted one and for a run that published with failures. Both are
        checked here, because either false positive would report a broken
        configuration as healthy.
        """
        r, log = self.run_and_capture("renderr_all_kinds_abort")
        self.assertTrue(r.render_tally.too_many_errors)
        self.assertIsNone(self.SUCCESS_PATTERN.search(log))

        self.clean_generator()
        r, log = self.run_and_capture("renderr_all_kinds")
        self.assertEqual(r.render_errors, 3)
        self.assertIsNone(self.SUCCESS_PATTERN.search(log))
