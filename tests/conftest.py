#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

# Activate the legacy-Python (<3.8) compatibility layer before pytest collects any
# coshsh-importing test module. On Python >= 3.8 this is inert: the gate inside
# coshsh_pycompat short-circuits and the import has no side effect. The compat module
# lives at the source-tree root (the parent of this tests/ directory), so put that on
# sys.path before importing it. See specs/006-legacy-python-compat/.
import sys
import os

if sys.version_info < (3, 8):
    _pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _pkg_root not in sys.path:
        sys.path.insert(0, _pkg_root)
    import coshsh_pycompat  # noqa: F401  (import for its install side effect)


def pytest_configure(config):
    """Register the markers this suite uses so -m never warns about a typo."""
    # WHY "benchmark" exists: tests/test_performance.py measures the
    # constitutional 60,000-services-in-10-seconds bound (Principle IV). It is a
    # gate that is run deliberately, not part of an ordinary suite run, so it
    # carries a marker the normal invocation deselects with -m "not benchmark".
    config.addinivalue_line(
        "markers",
        "benchmark: long-running performance gate, excluded from normal runs",
    )
