#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Legacy-only regression guard for the coshsh_pycompat compatibility layer.

The whole module is skipped on Python >= 3.8 -- the layer is inert there, so there is
nothing to exercise and the project's tests/ suite stays single-version-agnostic. On the
legacy (<3.8) CI matrix job the layer is active (installed via tests/conftest.py) and this
file actively asserts its behavior. See specs/006-legacy-python-compat/contracts/.
"""

import subprocess
import sys

import pytest

pytestmark = pytest.mark.skipif(
    sys.version_info >= (3, 8),
    reason="compat layer is inert on Python >= 3.8")


def test_coshsh_package_imports():
    # C2: the package compiles/imports despite the future-import + PEP 585/604 syntax.
    import coshsh
    assert coshsh is not None


def test_coshsh_submodule_imports():
    # C2: a representative submodule (uses typing.Protocol, annotated ClassVar) imports.
    import coshsh.datainterface
    assert hasattr(coshsh.datainterface, "CoshshDatainterface")


def test_typing_protocol_shim_usable():
    # C4: typing.Protocol / runtime_checkable are importable and usable as a base class.
    from typing import Protocol, runtime_checkable

    @runtime_checkable
    class _Fn(Protocol):
        pass

    assert _Fn is not None


def test_subprocess_capture_output_shim():
    # C4: subprocess.run(capture_output=True) returns captured stdout/stderr on <3.7
    # (and is a genuine passthrough on 3.7+, where the kwarg is native).
    result = subprocess.run(
        [sys.executable, "-c", "import sys; sys.stdout.write('hello')"],
        capture_output=True)
    assert result.stdout == b"hello"


def test_finder_scope_is_limited():
    # C3: the finder must NOT intercept non-coshsh modules. Importing a fresh stdlib
    # module goes through the normal machinery, not our _StripLoader.
    import importlib

    mod = importlib.import_module("difflib")
    loader = getattr(mod, "__loader__", None)
    assert type(loader).__name__ != "_StripLoader"


def test_install_is_idempotent():
    # C1: re-importing / re-installing must not add a second finder to sys.meta_path.
    import coshsh_pycompat

    before = [f for f in sys.meta_path
              if type(f).__name__ == "_CoshshFinder"]
    assert len(before) == 1
    coshsh_pycompat._install()
    after = [f for f in sys.meta_path
             if type(f).__name__ == "_CoshshFinder"]
    assert len(after) == 1
