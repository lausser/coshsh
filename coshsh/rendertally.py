#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""
RenderTally: the render-attempt counters for one recipe run, and the verdict
derived from them.

Sole responsibility: count template render attempts and their outcomes, and
answer one question -- did this run fail badly enough that it must publish
nothing?

What this module does NOT do:
    - It does NOT render anything, read the filesystem, or log. It is pure.
    - It does NOT decide what happens on abort; Generator.run() does that.
    - It does NOT parse cookbook values; Recipe.__init__ does that and hands
      the already-validated results to the constructor.

WHY it is a separate, dependency-free class: the correctness requirement is a
precision one -- one failed rendering in a billion attempts must still abort a
recipe configured with max_error_pct = 0. Proving that against a real Recipe
would mean building a billion objects. Proving it against this class is three
lines (see tests/test_rendertally.py). Keeping the arithmetic away from Jinja2
and the filesystem is what makes the guarantee testable at all.

Ownership: one instance per Recipe, created in Recipe.__init__, mutated in place
by coshsh.item during Recipe.render(), read by Generator.run() between render()
and output().
"""

from __future__ import annotations

# The three ways one render attempt can turn out. coshsh.item produces these and
# RenderTally.record() consumes them; they are plain strings so that a value
# showing up in a log or a traceback reads for itself.
OK = "ok"
MISSING = "missing"
ERROR = "error"


class RenderTally:
    """Counters for one recipe's render pass, plus the abort verdict.

    Attributes:
        attempts    -- every render attempt, success or failure, counted once
                       per matched template rule per object.
        missing     -- attempts that failed because the template file was not
                       found anywhere on the recipe's templates_path.
        errors      -- attempts that failed for any other reason: a Jinja2
                       syntax error, an exception while loading the template,
                       an exception raised while rendering it, or a failure
                       evaluating a template rule's conditions.
        max_error_pct    -- the configured tolerance, or None for "never abort".
        tolerate_missing -- when True, missing templates leave the percentage
                       calculation entirely (both numerator and denominator).
    """

    def __init__(self, max_error_pct: float | None = None,
                 tolerate_missing: bool = False) -> None:
        self.attempts = 0
        self.missing = 0
        self.errors = 0
        self.max_error_pct = max_error_pct
        self.tolerate_missing = tolerate_missing

    # --- recording -----------------------------------------------------------

    def record(self, outcome: str) -> None:
        """Count one render attempt together with how it turned out.

        *outcome* is OK, MISSING or ERROR.

        WHY a single call and not an attempt-then-outcome pair: the attempt and
        its outcome are one event, and splitting them across two calls makes it
        possible to record either without the other. That mistake is silent --
        a missed attempt never raises, it just shrinks the denominator, and a
        flattered percentage means a recipe that should have aborted publishes
        instead. Counting both here makes the pairing unbreakable.
        """
        self.attempts += 1
        if outcome == MISSING:
            self.missing += 1
        elif outcome == ERROR:
            self.errors += 1

    # --- derived values ------------------------------------------------------

    @property
    def template_errors(self) -> int:
        """Failures that count against the tolerance.

        This is the value Recipe.render_errors exposes and the value the
        coshsh_recipe_render_errors gauge carries.

        Missing templates count by default: a rule that fired against a
        template which is not there produced no output, and from the point of
        view of the configuration that is being generated, an absent template
        and a broken one are the same failure. Only a recipe that declares
        tolerate_missing_templates says otherwise.
        """
        if self.tolerate_missing:
            return self.errors
        return self.missing + self.errors

    @property
    def accountable_attempts(self) -> int:
        """The denominator: attempts the tolerance is measured against.

        WHY the denominator shrinks under tolerate_missing: a tolerated missing
        template is not a success. If it stayed in the denominator it would
        quietly dilute the percentage -- a recipe with 9 absent templates and 1
        genuinely broken one would read as 10% failed, and a tolerance of 5%
        would let it publish. Removing it from both sides instead reports 100%
        of what was actually accountable, which is the truth: of the renderings
        this recipe was willing to judge, all of them failed.
        """
        if self.tolerate_missing:
            return self.attempts - self.missing
        return self.attempts

    @property
    def error_pct(self) -> float:
        """Percentage of accountable attempts that failed.

        Returns 0.0 when nothing was accountable -- a recipe that collected no
        objects, or one where every attempt was a tolerated absence. Such a run
        has not demonstrated a failure, so it must not be treated as one (and
        must not raise ZeroDivisionError on the way to finding that out).
        """
        accountable = self.accountable_attempts
        if not accountable:
            return 0.0
        return 100.0 * self.template_errors / accountable

    @property
    def breakdown(self) -> str:
        """Human-readable split of the failures, or "" when there were none.

        WHY this exists rather than leaving operators to count log lines: a
        template that cannot be loaded is reported once per run, not once per
        object that referenced it (see coshsh.item._TemplateFailure), so the
        number of log lines no longer reflects the number of failures. This is
        where the split comes from instead, and it belongs in the log rather
        than only in the metrics -- whoever is reading a log file at 3am may
        not have Prometheus in front of them.
        """
        if not (self.missing or self.errors):
            return ""
        parts = []
        if self.missing:
            parts.append("%d missing%s" % (
                self.missing, " (tolerated)" if self.tolerate_missing else ""))
        if self.errors:
            parts.append("%d faulty" % self.errors)
        return ", ".join(parts)

    @property
    def too_many_errors(self) -> bool:
        """True when this run exceeded its configured tolerance and must abort."""
        if self.max_error_pct is None:
            # Abort protection is opt-in per recipe: a recipe that declares no
            # tolerance publishes whatever it managed to render, however much
            # failed. Silence here is not "no failures", it is "this recipe's
            # owner has not said what an unacceptable failure rate would be",
            # and guessing on their behalf would turn working unattended runs
            # into refusals overnight.
            return False
        # WHY the raw float and a strict '>': rounding here would silently
        # defeat max_error_pct = 0, because round(0.0001, 2) > 0 is False and a
        # single failure among a million renderings would publish anyway. Round
        # for display if you like; never round on the way into this comparison.
        # The strict '>' is what lets a clean run at exactly 0.0 publish while
        # any accountable failure at all does not.
        return self.error_pct > self.max_error_pct

    def __repr__(self) -> str:
        return ("RenderTally(attempts=%d, missing=%d, errors=%d, "
                "max_error_pct=%s, tolerate_missing=%s)" % (
                    self.attempts, self.missing, self.errors,
                    self.max_error_pct, self.tolerate_missing))
