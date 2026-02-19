#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""
Shared utility helpers for coshsh: attribute comparison, environment
substitution, filename sanitisation, ordered dicts, and logging setup.

Does NOT: contain any Nagios/monitoring domain logic -- that lives in
the model and datasource modules.

Key contents:
    odict           -- Insertion-ordered dict (preserves recipe processing order).
    compare_attr    -- Regex-based attribute matching for recipe class resolution.
    is_attr         -- Exact (case-insensitive) attribute matching.
    substenv        -- re.sub callback that expands %ENV_VAR% tokens.
    cleanout        -- Strip unwanted characters/words from strings.
    normalize_dict  -- Lower-case keys and optionally values in a dict.
    clean_umlauts   -- Replace German umlauts with ASCII equivalents.
    sanitize_filename -- Make a filename filesystem-safe, appending an MD5
                         fragment when characters had to be replaced.
    setup_logging   -- Initialise the coshsh rotating-file + console logger.
    switch_logging  -- Redirect the file handler to a different log file.
    restore_logging -- Switch back to the original log file.

AI-agent note: This is a pure-utility module.  Every function is
stateless except the logging helpers which store state as function
attributes on ``setup_logging``.
"""

import time
import sys
import re
import hashlib
import copy
import os
import logging
from logging.handlers import RotatingFileHandler
from collections.abc import MutableMapping


# WHY: odict exists to preserve the insertion order of recipes in
# generator.recipes.  Recipe processing order matters because later
# recipes can depend on objects created by earlier ones.  Python 3.7+
# guarantees dict ordering, but this codebase pre-dates that guarantee
# and the explicit ordered-dict makes the intent unmistakable.
class odict(MutableMapping):
    """Insertion-order-preserving dictionary used for ``generator.recipes``.

    Recipes must be processed in the order they were declared in the
    configuration file so that inter-recipe dependencies (e.g. a host
    recipe feeding an application recipe) are satisfied.  This class
    keeps a separate ``_keys`` list to record that order.

    Copied from
    http://code.activestate.com/recipes/496761-a-more-clean-implementation-for-ordered-dictionary/
    Thanks! I use the odict class for generator.recipes
    """
    def __init__(self):
        self._keys = []
        self._data = {}

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        for i in self._data:
            yield i

    def __setitem__(self, key, value):
        if key not in self._data:
            self._keys.append(key)
        self._data[key] = value

    def __getitem__(self, key):
        return self._data[key]

    def __delitem__(self, key):
        del self._data[key]
        self._keys.remove(key)

    def keys(self):
        return list(self._keys)

    def copy(self):
        copyDict = odict()
        copyDict._data = self._data.copy()
        copyDict._keys = self._keys[:]
        return copyDict


# WHY: compare_attr uses re.match (anchored at start) rather than
# re.search so that each pattern in *strings* acts like a prefix /
# anchored match.  Callers (recipe __mi_ident__ methods) rely on this
# to say "type starts with 'linux'" without accidentally matching
# "solarislinux".  The IGNORECASE flag is deliberate -- CMDB / CSV
# data often has inconsistent casing.
def compare_attr(key, params, strings):
    """Check whether ``params[key]`` matches any regex in *strings*.

    Each element of *strings* is compiled as a regex and tested with
    ``re.match`` (anchored at the start of the value, case-insensitive).
    Returns ``True`` on the first hit, ``False`` if the key is missing,
    ``None``, or nothing matches.

    This is the primary mechanism recipes use in their ``__mi_ident__``
    methods to claim responsibility for a host or application.
    """
    if not isinstance(strings, list):
        strings = [strings]
    if key in params:
        if params[key] == None:
            return False
        # WHY: re.match anchors at the start -- patterns like "linux.*"
        # will match "linux_server" but not "not_linux_server".
        elif [str1 for str1 in strings if re.match(str1, params[key], re.IGNORECASE)]:
            return True
    return False

def is_attr(key, params, strings):
    """Check whether ``params[key]`` exactly equals any element in *strings*.

    Comparison is case-insensitive but, unlike :func:`compare_attr`, no
    regex interpretation is performed -- this is a strict equality test.
    """
    if not isinstance(strings, list):
        strings = [strings]
    if key in params:
        if [str1 for str1 in strings if str1.lower() == params[key].lower()]:
            return True
    return False

def cleanout(dirty_string, delete_chars="", delete_words=[]):
    """Remove unwanted characters and substrings from *dirty_string*.

    *delete_chars* is iterated character-by-character; *delete_words* are
    removed as whole substrings.  The result is also stripped of leading
    and trailing whitespace.
    """
    if not dirty_string:
        return dirty_string
    for dirt in delete_words + list(delete_chars):
        dirty_string = dirty_string.replace(dirt, "")
    return dirty_string.strip()

# WHY: substenv is designed as a callback for re.sub.  The caller runs
# something like ``re.sub(r'%[A-Za-z_]+%', substenv, text)`` so that
# every ``%VAR%`` token in config strings is expanded to the matching
# environment variable.  The ``%``-delimited pattern follows the
# Windows-style convention (``%HOME%``) because coshsh configuration
# files historically used that syntax.  If the variable is not set the
# original ``%VAR%`` token is returned unchanged -- this is intentional
# so that unexpanded tokens are visible in the output for debugging.
def substenv(matchobj):
    """``re.sub`` callback: expand a ``%VAR%`` token from the environment.

    Strips the surrounding ``%`` characters, looks the result up in
    ``os.environ``, and returns the value.  If the variable is not set
    the original token (including ``%`` delimiters) is returned verbatim.
    """
    if matchobj.group(0).replace('%', '') in os.environ.keys():
        return os.environ[matchobj.group(0).replace('%', '')]
    else:
        return matchobj.group(0)

def normalize_dict(the_dict, titles=[]):
    """Normalise a dictionary that came from a CSV or CMDB data source.

    All keys are lower-cased and values are stripped of surrounding
    whitespace.  Keys listed in *titles* additionally have their values
    lower-cased -- this is used for fields like ``hostname`` or ``type``
    where case-insensitive comparison is the norm.
    """
    for k in the_dict.keys():
        try:
            if k != k.lower():
                the_dict[k.lower()] = the_dict[k].strip()
                del the_dict[k]
            else:
                the_dict[k] = the_dict[k].strip()
        except Exception:
            pass
    for attr in [k for k in the_dict.keys() if k in titles]:
        try:
            the_dict[attr] = the_dict[attr].lower()
        except Exception:
            pass

def clean_umlauts(text):
    """Replace German umlauts and sharp-s with their ASCII equivalents.

    This is used when generating filenames or Nagios object names from
    host/service descriptions that may contain German characters.
    """
    translations = (
        ('\N{LATIN SMALL LETTER SHARP S}', 'ss'),
        ('\N{LATIN SMALL LETTER O WITH DIAERESIS}', 'oe'),
        ('\N{LATIN SMALL LETTER U WITH DIAERESIS}', 'ue'),
        ('\N{LATIN CAPITAL LETTER A WITH DIAERESIS}', 'Ae'),
        ('\N{LATIN CAPITAL LETTER O WITH DIAERESIS}', 'Oe'),
        ('\N{LATIN CAPITAL LETTER U WITH DIAERESIS}', 'Ue'),
        # et cetera
    )
    for from_str, to_str in translations:
        text = text.replace(from_str, to_str)
    return text


# WHY: sanitize_filename appends a short MD5 fragment when it has to
# replace characters.  This prevents collisions: two different original
# filenames that sanitise to the same string (e.g. "a:b.cfg" and
# "a*b.cfg" both become "a_b.cfg") will get distinct suffixes because
# the hash is computed from the *original* unsanitised name.  Only four
# hex digits are used to keep filenames short while still making
# accidental collisions extremely unlikely within a single host's
# config directory.  When no characters needed replacing the original
# name is returned unchanged, so existing clean filenames are stable.
def sanitize_filename(filename):
    """Return a filesystem-safe version of *filename*.

    Characters that are illegal or problematic on common filesystems
    (``\\ / * ? : " < > |`` and space) are replaced with underscores.
    If any replacement was made, a 4-character MD5 suffix derived from
    the *original* filename is appended before the extension to avoid
    collisions between different names that would otherwise sanitise to
    the same string.

    If no replacement is needed the original filename is returned as-is.
    """
    name, ext = os.path.splitext(filename)
    sanitized = re.sub(r'[\\/*?:"<>| ]+', '_', name)
    if sanitized == name:
        return filename
    # WHY: The MD5 suffix is only 4 hex chars -- enough to disambiguate
    # within a single host's directory while keeping names readable.
    hash_suffix = hashlib.md5(filename.encode()).hexdigest()[:4]
    sanitized_with_hash = "{}_{}{}".format(sanitized, hash_suffix, ext)
    return sanitized_with_hash


# NOTE: setup_logging stores its configuration as function attributes
# (e.g. setup_logging.logdir) so that switch_logging / restore_logging
# can access and restore the original settings without module-level globals.
def setup_logging(logdir=".", logfile="coshsh.log", scrnloglevel=logging.INFO, txtloglevel=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", backup_count=2):
    """Initialise the coshsh logger with a rotating file handler and a
    console (stderr) handler.

    The logger name is derived from the log filename (minus the ``.log``
    extension).  Configuration is stored as attributes on this function
    object so that :func:`switch_logging` and :func:`restore_logging`
    can inspect and restore the original state.

    Returns the configured :class:`logging.Logger` instance.
    """
    logdir = os.path.abspath(logdir)
    abs_logfile = logfile if os.path.isabs(logfile) else os.path.join(logdir, logfile)
    if not os.path.exists(os.path.dirname(abs_logfile)):
        os.makedirs(os.path.dirname(abs_logfile), 0o755)
   
    setup_logging.logger_name = os.path.basename(abs_logfile).replace(".log", "")
    logger = logging.getLogger(setup_logging.logger_name)

    if logger.hasHandlers():
        # this method can be called multiple times in the unittests
        for handler in [h for h in logger.handlers]:
            handler.close()
            logger.removeHandler(handler)

    logger.setLevel(logging.DEBUG)
    log_formatter = logging.Formatter(format)

    txt_handler = RotatingFileHandler(abs_logfile, backupCount=backup_count, maxBytes=20*1024*1024, delay=True)
    txt_handler.setFormatter(log_formatter)
    txt_handler.setLevel(txtloglevel)
    logger.addHandler(txt_handler)
    logger.debug("Logger initialized.")

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(scrnloglevel)
    logger.addHandler(console_handler)

    setup_logging.logdir = logdir
    setup_logging.logfile = logfile
    setup_logging.scrnloglevel = scrnloglevel
    setup_logging.txtloglevel = txtloglevel
    setup_logging.abs_logfile = abs_logfile
    setup_logging.log_formatter = log_formatter
    setup_logging.txt_handler = txt_handler
    setup_logging.console_handler = console_handler
    setup_logging.backup_count = backup_count
    return logger


def switch_logging(**kwargs):
    """Redirect the file log handler to a different log file.

    Accepts optional *logdir*, *logfile*, and *backup_count* keyword
    arguments.  If the computed absolute path is the same as the current
    one, the call is a no-op.  This is used when the generator begins
    processing a new recipe that has its own log directory.
    """
    logdir = kwargs.get("logdir", setup_logging.logdir)
    logfile = kwargs.get("logfile", setup_logging.logfile)
    backup_count = kwargs.get("backup_count", setup_logging.backup_count)
    logdir = setup_logging.logdir if logdir == None else logdir
    logfile = setup_logging.logfile if logfile == None else logfile
    backup_count = setup_logging.backup_count if backup_count == None else backup_count
    abs_logfile = logfile if os.path.isabs(logfile) else os.path.join(logdir, logfile)
    if abs_logfile == setup_logging.abs_logfile:
        return
    if not os.path.exists(os.path.dirname(abs_logfile)):
        os.mkdir(os.path.dirname(abs_logfile))
    logger = logging.getLogger(setup_logging.logger_name)
    logger.debug("Logger switches to " + abs_logfile)
    # remove the txt_handler
    logger.removeHandler(setup_logging.txt_handler)
    for handler in [h for h in logger.handlers]:
        if hasattr(handler, "baseFilename"):
            logger.removeHandler(handler)
    txt_handler = RotatingFileHandler(abs_logfile, backupCount=backup_count, maxBytes=20*1024*1024, delay=True)
    txt_handler.setFormatter(setup_logging.log_formatter)
    txt_handler.setLevel(setup_logging.txtloglevel)
    logger.addHandler(txt_handler)

def restore_logging():
    """Switch the file log handler back to the original log file.

    Delegates to :func:`switch_logging` with the settings that were
    captured during :func:`setup_logging`.
    """
    switch_logging(logdir=setup_logging.logdir, logfile=setup_logging.logfile)
    logger = logging.getLogger('coshsh')
    logger.debug("Logger restored to " + setup_logging.logdir+"/"+setup_logging.logfile+"\n")

def get_logger(self, name="coshsh"):
    """Return the named logger (default ``"coshsh"``).

    Note: the *self* parameter exists for historical reasons -- this
    function is not a bound method but accepts *self* so it can be
    monkey-patched onto classes if needed.
    """
    return logging.getLogger(name)

