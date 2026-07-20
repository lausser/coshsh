"""Tests for Pushgateway datarecipient output (requires running pushgateway; may be slow)."""

import os
import time
import subprocess
import shutil
from tests.common_coshsh_test import CommonCoshshTest


class PushgatewayTest(CommonCoshshTest):

    def tearDown(self):
        shutil.rmtree("var/objects/test16")

    def test_pushgateway(self):
        """Verify that coshsh-cook with the PUSH recipe creates the expected dynamic output directory."""
        self.assertTrue(os.path.exists("../bin/coshsh-cook"))
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh.cfg --recipe PUSH", shell=True)
        self.assertTrue(os.path.exists("var/objects/test16/dynamic"))

    def test_pushgateway2(self):
        """Verify that PUSH2 recipe output appears after a delay (simulates slow pushgateway upload)."""
        time.sleep(19)
        subprocess.call("../bin/coshsh-cook --cookbook etc/coshsh.cfg --recipe PUSH2", shell=True)
        self.assertTrue(os.path.exists("var/objects/test16/dynamic"))


class RenderErrorMetricsTest(CommonCoshshTest):
    """The render counters as an observability signal (spec 007, US5).

    Reads the values out of the CollectorRegistry coshsh assembles, by standing
    in for pushadd_to_gateway. That needs no gateway process and asserts on
    exactly what would have been pushed -- including, crucially, which metrics
    were *absent* from a push, which is what "last_success does not advance"
    actually means given that pushadd only replaces the metrics it carries.
    """

    def tearDown(self):
        for leftover in ["renderr_push_all", "renderr_push_tolerate",
                         "renderr_push_abort", "renderr_push_publishes"]:
            shutil.rmtree("./var/objects/" + leftover, True)
        shutil.rmtree("./var/log_renderr", True)

    def run_capturing_metrics(self, recipe_name):
        """Run one recipe and return {metric_name: value} as it would be pushed."""
        import prometheus_client

        captured = {}

        def capture(address, grouping_key=None, job=None, registry=None, handler=None):
            for metric in registry.collect():
                for sample in metric.samples:
                    captured[sample.name] = sample.value

        original = prometheus_client.pushadd_to_gateway
        prometheus_client.pushadd_to_gateway = capture
        try:
            self.setUpConfig("etc/coshsh_renderr_push.cfg", recipe_name)
            self.generator.run()
        finally:
            prometheus_client.pushadd_to_gateway = original
        return self.generator.get_recipe(recipe_name), captured

    def test_raw_counts_and_attempts_are_exported_separately(self):
        """US5-1 / US5-2 / FR-017a / FR-017b: enough to compute the rate.

        Separate raw counts rather than a single blended number, so a consumer
        can tell "the template pack is half-deployed" from "somebody broke a
        template" without reading a log line.
        """
        r, m = self.run_capturing_metrics("push_all_kinds")
        # 1 good + 1 broken + 2 missing
        self.assertEqual(m["coshsh_recipe_render_attempts"], 4)
        self.assertEqual(m["coshsh_recipe_missing_templates"], 2)
        # render_errors keeps its name and now includes the missing ones
        self.assertEqual(m["coshsh_recipe_render_errors"], 3)
        self.assertEqual(m["coshsh_recipe_render_error_pct"], 75.0)

    def test_the_tolerate_flag_distinguishes_a_tolerated_absence_from_a_failure(self):
        """US5-3 / FR-017c: the missing count alone cannot express this.

        Both runs below see the same two absent templates and export the same
        missing_templates value. Only the flag says whether those two were
        counted as failures.
        """
        r_strict, strict = self.run_capturing_metrics("push_all_kinds")
        self.clean_generator()
        r_lenient, lenient = self.run_capturing_metrics("push_tolerate")

        self.assertEqual(strict["coshsh_recipe_missing_templates"],
                         lenient["coshsh_recipe_missing_templates"])
        self.assertEqual(strict["coshsh_recipe_tolerate_missing_templates"], 0)
        self.assertEqual(lenient["coshsh_recipe_tolerate_missing_templates"], 1)
        # and the flag is what changed the failure count and the percentage
        self.assertEqual(strict["coshsh_recipe_render_errors"], 3)
        self.assertEqual(lenient["coshsh_recipe_render_errors"], 1)
        self.assertEqual(lenient["coshsh_recipe_render_error_pct"], 50.0)

    def test_an_aborted_run_exports_its_own_numbers(self):
        """US5-4 / FR-017d / FR-017e / SC-009: the run that matters most.

        pushadd_to_gateway only replaces the metrics it carries, so a metric
        omitted from an aborted run's push would leave the last *good* run's
        value standing -- a failing recipe reporting zero errors indefinitely.
        """
        r, m = self.run_capturing_metrics("push_abort")
        self.assertTrue(r.render_tally.too_many_errors)
        self.assertEqual(m["coshsh_recipe_aborted"], 1)
        self.assertEqual(m["coshsh_recipe_render_errors"], 3)
        self.assertEqual(m["coshsh_recipe_render_attempts"], 4)

    def test_last_success_advances_only_for_runs_that_published(self):
        """US5-7 / FR-017g / SC-011: the liveness alarm finally works.

        This timestamp is what the standard liveness alarm subtracts from, so
        it may only be refreshed by a run that actually published. A run that
        collected and rendered but wrote nothing must let it age, or the alarm
        stays silent exactly when it should fire. Absent from the push is how
        that is expressed: pushadd leaves a metric it does not carry at its
        stored value, so omission *is* "does not advance".
        """
        r_ok, published = self.run_capturing_metrics("push_publishes")
        self.assertFalse(r_ok.render_tally.too_many_errors)
        self.assertIn("coshsh_recipe_last_success", published)
        self.assertEqual(published["coshsh_recipe_aborted"], 0)

        self.clean_generator()
        r_bad, aborted = self.run_capturing_metrics("push_abort")
        self.assertTrue(r_bad.render_tally.too_many_errors)
        self.assertNotIn("coshsh_recipe_last_success", aborted)
        # ... and nothing claims a configuration was generated either
        self.assertNotIn("coshsh_recipe_last_generated", aborted)
