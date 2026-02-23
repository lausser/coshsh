"""
Extended INI config parser that adds single-level section inheritance via
the ``isa`` key.

Does NOT: perform variable substitution (%ENV_VAR%, @VAULT[key]).  Those
tokens are left as literal strings at parse time and are resolved later:
  - %ENV_VAR% tokens are expanded by coshsh.util.substenv at the point
    where each config value is consumed (Recipe.__init__, add_vault,
    add_datasource, add_datarecipient, etc.).
  - @VAULT[key] tokens are expanded by recipe.substsecret() during
    add_datasource / add_datarecipient, *after* vaults have been opened
    and their secrets read.
This two-phase approach allows environment variables to be resolved early
(they are available in the process environment) while vault secrets are
resolved only once the vault backends have been initialised.

Key classes:
    CoshshConfigParser -- RawConfigParser subclass that copies missing keys
        from a parent section designated by ``isa``.

Inheritance mechanism (``isa``):
    If a section contains ``isa = <other_section_name>``, then after the
    standard INI file is parsed, every key present in <other_section_name>
    but absent in the current section is copied over.  This is one-level
    deep only: if the parent section itself has an ``isa`` key, that
    grandparent is NOT followed.  There is no cycle detection because the
    single-level constraint makes cycles impossible to trigger.

AI agent note:
    The ``isa`` key itself is never copied to the child section (the
    ``not key == "isa"`` guard).  Inheritance is evaluated once at read()
    time against the internal _sections dict, so dynamic modifications
    after read() are not retroactively inherited.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from configparser import RawConfigParser


class CoshshConfigParser(RawConfigParser, object):
    """RawConfigParser with single-level ``isa`` section inheritance.

    Extends the standard library RawConfigParser (which does NOT perform
    ``%()s`` interpolation, unlike SafeConfigParser) to support a simple
    inheritance model: a section may declare ``isa = <parent_section>``
    and will inherit all keys from the parent that are not already
    defined locally.
    """

    def read(
        self,
        files: str | os.PathLike[str] | Iterable[str | os.PathLike[str]],
        encoding: str | None = None,
    ) -> list[str]:
        """Read and parse INI file(s), then apply ``isa`` inheritance.

        After the standard RawConfigParser.read() populates self._sections,
        this method iterates all sections.  For any section containing an
        ``isa`` key whose value names another existing section, missing keys
        are copied from the parent section into the child.

        Args:
            files: A filename string or list of filename strings to read.
            encoding: Encoding to use when opening files.

        Returns:
            List of successfully read filenames.

        Side effects:
            - Populates self._sections via the parent class read().
            - Modifies child sections in-place by adding inherited keys.

        Note:
            Inheritance is one-level deep.  The ``isa`` key is NOT copied
            from parent to child, preventing accidental transitive
            inheritance.
        """
        # WHY: super() is called with self.__class__ explicitly to work
        # around Python 2/3 compatibility in older coshsh versions.  The
        # ``object`` in the class bases was originally required for
        # new-style class behaviour under Python 2.
        result = super(self.__class__, self).read(files, encoding=encoding)
        # WHY: Inheritance is implemented by direct dict manipulation on
        # _sections rather than using the public ConfigParser API.  This
        # avoids triggering interpolation logic (even though RawConfigParser
        # doesn't interpolate, subclasses might) and is the most efficient
        # way to bulk-copy keys at parse time.
        for section in self._sections.values():
            if "isa" in section.keys() and section["isa"] in self._sections:
                for key in self._sections[section["isa"]]:
                    if not key in section and not key == "isa":
                        section[key] = self._sections[section["isa"]][key]
        return result
