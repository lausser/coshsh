"""Unit tests for RenderTally -- the render-error arithmetic, in isolation.

RenderTally is deliberately pure (no I/O, no Jinja2, no Recipe), so the precision
requirement can be tested directly: one failure in a billion attempts must still
abort when the configured tolerance is 0.  Constructing a recipe with a billion
objects to prove that is obviously not an option, which is exactly why the
arithmetic lives in its own class.

Every case below is one row of specs/007-template-render-errors/quickstart.md
Scenario 1.
"""

import sys
import unittest

sys.dont_write_bytecode = True

from coshsh.rendertally import ERROR, MISSING, OK, RenderTally


class RenderTallyTest(unittest.TestCase):

    def tally(self, attempts=0, missing=0, errors=0, max_error_pct=None,
              tolerate_missing=False):
        """Build a tally already in the state under test.

        WHY a helper instead of calling record(): these tests are about the
        arithmetic over a given state, not about how the state was reached.
        Reaching attempts=1_000_000_000 by calling record() a billion times is
        not a test, it is a hang.
        """
        t = RenderTally(max_error_pct=max_error_pct, tolerate_missing=tolerate_missing)
        t.attempts = attempts
        t.missing = missing
        t.errors = errors
        return t

    def test_one_in_a_million_aborts_at_zero_tolerance(self):
        """max_error_pct = 0 aborts on a single failure among a million attempts."""
        t = self.tally(attempts=1000000, errors=1, max_error_pct=0)
        self.assertEqual(t.template_errors, 1)
        self.assertEqual(t.accountable_attempts, 1000000)
        self.assertAlmostEqual(t.error_pct, 0.0001)
        self.assertTrue(t.too_many_errors)

    def test_one_in_a_billion_aborts_at_zero_tolerance(self):
        """The no-rounding guard: 1e-7 percent is still greater than zero.

        This is the regression witness for invariant 1 in data-model.md. If
        anyone ever rounds error_pct before comparing it, round(1e-7, 2) is 0.0
        and this test is the only thing that notices.
        """
        t = self.tally(attempts=1000000000, errors=1, max_error_pct=0)
        self.assertGreater(t.error_pct, 0.0)
        self.assertTrue(t.too_many_errors)

    def test_zero_attempts_does_not_abort_and_does_not_divide_by_zero(self):
        """A recipe that collected nothing is not a failing recipe."""
        t = self.tally(attempts=0, max_error_pct=0)
        self.assertEqual(t.accountable_attempts, 0)
        self.assertEqual(t.error_pct, 0.0)
        self.assertFalse(t.too_many_errors)

    def test_clean_run_at_zero_tolerance_does_not_abort(self):
        """Strict greater-than: 0.0 > 0 is False, so a clean run publishes."""
        t = self.tally(attempts=100, errors=0, max_error_pct=0)
        self.assertEqual(t.error_pct, 0.0)
        self.assertFalse(t.too_many_errors)

    def test_no_tolerance_configured_never_aborts(self):
        """max_error_pct = None preserves today's behaviour: always publish."""
        t = self.tally(attempts=10, errors=10, max_error_pct=None)
        self.assertEqual(t.error_pct, 100.0)
        self.assertFalse(t.too_many_errors)

    def test_hundred_percent_tolerance_never_aborts(self):
        """100 is the ceiling: error_pct cannot exceed it and the test is strict >."""
        t = self.tally(attempts=10, errors=10, max_error_pct=100.0)
        self.assertEqual(t.error_pct, 100.0)
        self.assertFalse(t.too_many_errors)

    def test_tolerated_missing_leaves_numerator_and_denominator(self):
        """9 tolerated missing of 10 attempts leaves 1 accountable attempt, which failed."""
        t = self.tally(attempts=10, missing=9, errors=1, tolerate_missing=True)
        self.assertEqual(t.template_errors, 1)
        self.assertEqual(t.accountable_attempts, 1)
        # The point of the test: 100.0, not 10.0. A tolerated missing template
        # leaves the calculation entirely rather than counting as a success.
        self.assertEqual(t.error_pct, 100.0)

    def test_all_attempts_tolerated_missing_does_not_divide_by_zero(self):
        """Every attempt a tolerated absence: no accountable attempts, no abort."""
        t = self.tally(attempts=10, missing=10, max_error_pct=0, tolerate_missing=True)
        self.assertEqual(t.accountable_attempts, 0)
        self.assertEqual(t.error_pct, 0.0)
        self.assertFalse(t.too_many_errors)

    def test_missing_counts_as_error_by_default(self):
        """Without the tolerate flag a missing template is an ordinary failure."""
        t = self.tally(attempts=10, missing=2, errors=1)
        self.assertEqual(t.template_errors, 3)
        self.assertEqual(t.accountable_attempts, 10)
        self.assertEqual(t.error_pct, 30.0)

    def test_missing_is_counted_whether_or_not_tolerated(self):
        """Invariant 3: the flag governs the percentage, never the raw counter."""
        strict = self.tally(attempts=10, missing=4, tolerate_missing=False)
        lenient = self.tally(attempts=10, missing=4, tolerate_missing=True)
        self.assertEqual(strict.missing, 4)
        self.assertEqual(lenient.missing, 4)

    def test_record_lands_each_outcome_on_the_right_counter(self):
        """Every outcome counts an attempt; only failures count a failure."""
        t = RenderTally()
        t.record(OK)
        t.record(MISSING)
        t.record(ERROR)
        self.assertEqual(t.attempts, 3)
        self.assertEqual(t.missing, 1)
        self.assertEqual(t.errors, 1)

    def test_every_outcome_counts_an_attempt(self):
        """The invariant record() exists to enforce: no failure without an attempt.

        Attempts is the denominator of the abort percentage, so a failure that
        forgot to count its attempt would not raise -- it would quietly shrink
        the denominator and let a recipe publish that should have aborted.
        """
        for outcome in (OK, MISSING, ERROR):
            t = RenderTally()
            t.record(outcome)
            self.assertEqual(t.attempts, 1, "%s did not count an attempt" % outcome)
            # A failure can never outnumber the attempts it happened during.
            self.assertLessEqual(t.missing + t.errors, t.attempts)


    def test_breakdown_splits_missing_from_faulty(self):
        """The log's only remaining source for the split, so it must be right.

        A template that cannot be loaded is reported once per run rather than
        once per affected object, so counting log lines no longer reconstructs
        which kind of failure happened. This does.
        """
        t = self.tally(attempts=10, missing=2, errors=1)
        self.assertEqual(t.breakdown, "2 missing, 1 faulty")

    def test_breakdown_marks_tolerated_absences(self):
        """A tolerated absence still shows up, flagged, because it still happened."""
        t = self.tally(attempts=10, missing=2, errors=1, tolerate_missing=True)
        self.assertEqual(t.breakdown, "2 missing (tolerated), 1 faulty")

    def test_breakdown_names_only_what_occurred(self):
        """No zero-count noise: a clean run says nothing at all."""
        self.assertEqual(self.tally(attempts=10).breakdown, "")
        self.assertEqual(self.tally(attempts=10, missing=3).breakdown, "3 missing")
        self.assertEqual(self.tally(attempts=10, errors=3).breakdown, "3 faulty")


if __name__ == '__main__':
    unittest.main()
