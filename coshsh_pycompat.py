#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Additive, version-gated compatibility layer that lets the *unmodified* coshsh
sources import and run on Python < 3.8 (CentOS 7 / Python 3.6, 3.7).

WHY THIS MODULE EXISTS
======================
The ``coshsh/`` package is authored for Python 3.12 and uses constructs that fail
on 3.6/3.7. Some of them fail at *compile time*, so no ordinary runtime shim can
rescue an unmodified module -- the module never compiles. This layer rewrites the
coshsh source AST *before* compilation and injects a couple of small stdlib shims:

  * ``from __future__ import annotations`` (PEP 563) -- a compile-time
    ``SyntaxError`` on Python 3.6 ("future feature annotations is not defined").
    We drop that statement from the AST.  [targets: < 3.7]
  * PEP 585 (``list[str]``) / PEP 604 (``X | None``) annotation syntax -- would
    raise at runtime if the annotation were evaluated on 3.6. Because upstream uses
    ``from __future__ import annotations`` the annotations are never evaluated on
    modern Python either, so stripping every annotation here preserves identical
    runtime behavior while making the source compile.  [targets: < 3.9 / < 3.10]
  * ``typing.Protocol`` / ``typing.runtime_checkable`` (added in 3.8) -- imported by
    ``coshsh/datainterface.py``. We inject no-op stand-ins when absent.  [targets: < 3.8]
  * ``subprocess.run(capture_output=...)`` (added in 3.7) -- used by
    ``tests/test_delta.py``. We translate it to ``stdout=PIPE, stderr=PIPE``.  [targets: < 3.7]

DESIGN CONSTRAINTS
==================
  * The ``coshsh/`` package stays byte-for-byte identical to upstream -- all logic
    lives here, in this NEW top-level module (a sibling of ``coshsh/``). It must sit
    OUTSIDE the package because it has to run *before* ``coshsh/__init__.py`` is
    compiled (that file is exactly the one that fails on 3.6).
  * Fully version-gated: on Python >= 3.8 importing this module is a no-op with NO
    observable side effect -- no ``sys.meta_path`` change, no attribute added to
    ``typing`` / ``subprocess`` (contract C1).
  * Scope-limited: the import hook transforms ONLY ``coshsh`` / ``coshsh.*`` modules;
    stdlib, third-party (Jinja2) and dynamically-loaded recipe class files are never
    touched (FR-013 / contract C3).
  * Idempotent: importing this module repeatedly installs the finder at most once and
    applies each shim at most once (FR-010 / contract C1).
"""

import sys

# Importing these stdlib modules is side-effect free and therefore safe on every
# interpreter. Nothing below the imports *runs* on Python >= 3.8: the sole entry point
# is ``_install()``, gated by ``sys.version_info < (3, 8)`` at the bottom of the file.
import ast
import subprocess
import typing
import importlib.abc
import importlib.machinery


class _AnnotationStripper(ast.NodeTransformer):
    """Rewrite a coshsh module's AST so it compiles on Python 3.6/3.7.

    WHY: ``from __future__ import annotations`` is a compile-time ``SyntaxError`` on
    3.6, and PEP 585/604 annotation *syntax* would raise if evaluated. Upstream already
    imports ``annotations`` from ``__future__`` so its annotations are never evaluated at
    runtime on modern Python -- removing the future-import and stripping every annotation
    here yields identical runtime behavior while making the source compile.
    """

    def _strip_args(self, args):
        # Null the annotation on every parameter form (positional, kw-only, *args, **kw,
        # and positional-only where present on newer grammars parsed by an older ast).
        for a in (list(args.args) + list(args.kwonlyargs) +
                  list(getattr(args, "posonlyargs", []))):
            a.annotation = None
        if args.vararg:
            args.vararg.annotation = None
        if args.kwarg:
            args.kwarg.annotation = None

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        self._strip_args(node.args)
        node.returns = None  # drop the "-> T" return annotation
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_AnnAssign(self, node):
        # "x: T = value" -> "x = value"; a bare "x: T" (annotation only) is dropped.
        self.generic_visit(node)
        if node.value is None:
            return None
        return ast.copy_location(
            ast.Assign(targets=[node.target], value=node.value), node)

    def visit_ImportFrom(self, node):
        # Remove the "annotations" name from a "from __future__ import ..." statement,
        # dropping the whole statement if nothing else was imported alongside it.
        if node.module == "__future__":
            node.names = [n for n in node.names if n.name != "annotations"]
            if not node.names:
                return None
        return node


def _repair_empty_blocks(tree):
    """Insert a ``pass`` into any block emptied by dropping annotation-only statements.

    A class/function/if/for/while/with/try block that contained *only* bare annotations
    becomes an empty statement list after the transform, which ``compile()`` rejects.
    """
    for node in ast.walk(tree):
        for field in ("body", "orelse", "finalbody"):
            block = getattr(node, field, None)
            if isinstance(block, list) and not block:
                block.append(ast.Pass())
    return tree


class _StripLoader(importlib.machinery.SourceFileLoader):
    """A ``SourceFileLoader`` that AST-strips annotations before compiling and never
    reads or writes a bytecode cache for the transformed module.

    WHY no ``.pyc`` cache: a cached bytecode file for a coshsh module is dangerous on
    <3.8 -- either it persists our transformed bytecode, or (worse) a ``.pyc`` compiled
    from the *untransformed* source by some other tool shadows the transform and
    reintroduces the SyntaxError path. We bypass the cache entirely: ``get_code`` always
    recompiles from source and ``set_data`` refuses to write (FR-006 / contract C2).
    """

    def source_to_code(self, data, path, *, _optimize=-1):
        tree = _AnnotationStripper().visit(ast.parse(data))
        _repair_empty_blocks(tree)
        ast.fix_missing_locations(tree)
        return compile(tree, path, "exec", dont_inherit=True, optimize=_optimize)

    def get_code(self, fullname):
        # Skip the bytecode-cache read path; always transform + compile from source.
        source_path = self.get_filename(fullname)
        source_bytes = self.get_data(source_path)
        return self.source_to_code(source_bytes, source_path)

    def set_data(self, path, data, *, _mode=0o666):
        # Never emit a .pyc for a transformed module.
        return


class _CoshshFinder(importlib.abc.MetaPathFinder):
    """Meta-path finder scoped to the ``coshsh`` namespace.

    For ``coshsh`` / ``coshsh.*`` it returns the ordinary spec (from the default
    ``PathFinder``) with the strip loader swapped in; for every other module it returns
    ``None`` so the normal import machinery handles it untouched (FR-013 / contract C3).
    """

    def find_spec(self, fullname, path=None, target=None):
        if fullname != "coshsh" and not fullname.startswith("coshsh."):
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path, target)
        if not spec or not spec.origin or not spec.origin.endswith(".py"):
            return None
        spec.loader = _StripLoader(fullname, spec.origin)
        return spec


def _install_protocol_shim():
    # WHY: typing.Protocol / runtime_checkable were added in 3.8; coshsh/datainterface.py
    # does "from typing import ... Protocol" and uses it only as a plain base class (no
    # structural-typing enforcement), so no-op stand-ins are sufficient (contract C4).
    if not hasattr(typing, "Protocol"):
        class Protocol(object):
            pass
        typing.Protocol = Protocol
    if not hasattr(typing, "runtime_checkable"):
        typing.runtime_checkable = lambda cls: cls


def _install_subprocess_shim():
    # WHY: subprocess.run(capture_output=...) is a 3.7+ kwarg (TypeError on 3.6);
    # tests/test_delta.py relies on it. Translate to stdout=PIPE, stderr=PIPE (contract C4).
    if sys.version_info >= (3, 7):
        return
    if getattr(subprocess.run, "_coshsh_capture_shim", False):
        return
    _orig_run = subprocess.run

    def run(*args, **kwargs):
        if kwargs.pop("capture_output", False):
            kwargs.setdefault("stdout", subprocess.PIPE)
            kwargs.setdefault("stderr", subprocess.PIPE)
        return _orig_run(*args, **kwargs)

    run._coshsh_capture_shim = True
    subprocess.run = run


def _install():
    """Install the coshsh import hook and the typing/subprocess shims, idempotently.

    Only ever called on Python < 3.8 (see the gate at module bottom).
    """
    if not any(isinstance(f, _CoshshFinder) for f in sys.meta_path):
        sys.meta_path.insert(0, _CoshshFinder())
    _install_protocol_shim()
    _install_subprocess_shim()


# --- Version gate (contract C1) ---------------------------------------------------------
# The layer installs itself iff the interpreter is older than 3.8. On >= 3.8 this import
# is completely inert: nothing is added to sys.meta_path, typing or subprocess.
if sys.version_info < (3, 8):
    _install()
