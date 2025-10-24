#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from __future__ import annotations

import functools
import hashlib
import logging
import os
import re
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Union

# Compiled regex patterns cache for performance
_REGEX_CACHE: Dict[str, Pattern] = {}


def _get_compiled_pattern(pattern: str, flags: int = 0) -> Pattern:
    """Get a compiled regex pattern from cache or compile and cache it.

    Args:
        pattern: Regular expression pattern string
        flags: Regex flags (e.g., re.IGNORECASE)

    Returns:
        Compiled regex pattern object
    """
    cache_key = f"{pattern}:{flags}"
    if cache_key not in _REGEX_CACHE:
        _REGEX_CACHE[cache_key] = re.compile(pattern, flags)
    return _REGEX_CACHE[cache_key]


# Backward compatibility: odict is now just dict (Python 3.7+ dicts are ordered)
# This alias maintains compatibility with existing code
odict = dict


def compare_attr(
    key: str,
    params: Dict[str, Any],
    strings: Union[str, List[str]]
) -> bool:
    """Check if a parameter value matches any of the given string patterns.

    This function checks if params[key] matches any of the regex patterns
    in strings. Matching is case-insensitive.

    Args:
        key: The parameter key to check
        params: Dictionary of parameters
        strings: String pattern or list of string patterns to match against

    Returns:
        True if the parameter matches any pattern, False otherwise

    Example:
        >>> compare_attr("type", {"type": "Linux"}, [".*linux.*", ".*unix.*"])
        True
        >>> compare_attr("type", {"type": "Windows"}, ".*linux.*")
        False
    """
    if not isinstance(strings, list):
        strings = [strings]
    if key in params:
        if params[key] is None:
            return False
        for pattern in strings:
            if _get_compiled_pattern(pattern, re.IGNORECASE).match(params[key]):
                return True
    return False

def is_attr(
    key: str,
    params: Dict[str, Any],
    strings: Union[str, List[str]]
) -> bool:
    """Check if a parameter value exactly matches any of the given strings (case-insensitive).

    Unlike compare_attr, this does exact string matching, not regex matching.

    Args:
        key: The parameter key to check
        params: Dictionary of parameters
        strings: String or list of strings to match against

    Returns:
        True if the parameter matches any string (case-insensitive), False otherwise

    Example:
        >>> is_attr("name", {"name": "OS"}, "os")
        True
        >>> is_attr("name", {"name": "Application"}, "os")
        False
    """
    if not isinstance(strings, list):
        strings = [strings]
    if key in params:
        param_lower = params[key].lower() if isinstance(params[key], str) else str(params[key]).lower()
        for s in strings:
            if s.lower() == param_lower:
                return True
    return False

def cleanout(
    dirty_string: Optional[str],
    delete_chars: str = "",
    delete_words: Optional[List[str]] = None
) -> Optional[str]:
    """Remove specified characters and words from a string.

    Args:
        dirty_string: String to clean
        delete_chars: String of characters to remove
        delete_words: List of words/substrings to remove

    Returns:
        Cleaned string with specified characters and words removed, or None if input is None

    Example:
        >>> cleanout("hello world!", "!", ["world"])
        'hello '
    """
    if not dirty_string:
        return dirty_string
    delete_words = delete_words or []
    for dirt in delete_words + list(delete_chars):
        dirty_string = dirty_string.replace(dirt, "")
    return dirty_string.strip()

def substenv(matchobj: re.Match) -> str:
    """Substitute environment variables in matched pattern.

    Used as a callback for re.sub() to replace %ENV_VAR% with actual values.

    Args:
        matchobj: Regex match object containing the environment variable pattern

    Returns:
        Environment variable value if it exists, otherwise the original pattern

    Example:
        >>> import re
        >>> text = "Path is %HOME%/config"
        >>> re.sub(r'%.*?%', substenv, text)
        'Path is /home/user/config'
    """
    env_var = matchobj.group(0).replace('%', '')
    return os.environ.get(env_var, matchobj.group(0))

def normalize_dict(
    the_dict: Dict[str, Any],
    titles: Optional[List[str]] = None
) -> None:
    """Normalize dictionary keys to lowercase and optionally lowercase specific values.

    Modifies the dictionary in-place:
    1. Converts all keys to lowercase
    2. Strips string values
    3. Lowercases values for keys in titles list

    Args:
        the_dict: Dictionary to normalize (modified in-place)
        titles: List of keys whose values should also be lowercased

    Example:
        >>> d = {"Name": "Linux", "TYPE": "OS"}
        >>> normalize_dict(d, titles=["type"])
        >>> d
        {'name': 'Linux', 'type': 'os'}
    """
    titles = titles or []
    # Create a list of keys to avoid RuntimeError: dictionary changed size during iteration
    keys_to_process = list(the_dict.keys())

    for k in keys_to_process:
        try:
            value = the_dict[k]
            lower_key = k.lower()

            # Strip string values
            if isinstance(value, str):
                value = value.strip()

            # Update or add with lowercase key
            if k != lower_key:
                del the_dict[k]
            the_dict[lower_key] = value
        except (AttributeError, TypeError):
            # Handle non-string values gracefully
            pass

    # Lowercase values for specified keys
    for attr in titles:
        if attr in the_dict:
            try:
                the_dict[attr] = the_dict[attr].lower()
            except (AttributeError, TypeError):
                # Handle non-string values gracefully
                pass

def clean_umlauts(text: str) -> str:
    """Replace German umlauts with ASCII equivalents.

    Converts characters like ä, ö, ü, ß to ASCII-compatible strings.

    Args:
        text: Text containing umlauts

    Returns:
        Text with umlauts replaced by ASCII equivalents

    Example:
        >>> clean_umlauts("Größe")
        'Groesse'
        >>> clean_umlauts("München")
        'Muenchen'
    """
    translations = (
        ('\N{LATIN SMALL LETTER SHARP S}', 'ss'),
        ('\N{LATIN SMALL LETTER A WITH DIAERESIS}', 'ae'),
        ('\N{LATIN SMALL LETTER O WITH DIAERESIS}', 'oe'),
        ('\N{LATIN SMALL LETTER U WITH DIAERESIS}', 'ue'),
        ('\N{LATIN CAPITAL LETTER A WITH DIAERESIS}', 'Ae'),
        ('\N{LATIN CAPITAL LETTER O WITH DIAERESIS}', 'Oe'),
        ('\N{LATIN CAPITAL LETTER U WITH DIAERESIS}', 'Ue'),
    )
    for from_str, to_str in translations:
        text = text.replace(from_str, to_str)
    return text


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by replacing invalid characters.

    Replaces characters that are invalid in filenames (/, \\, *, ?, :, ", <, >, |, space)
    with underscores. If the filename was modified, appends a 4-character hash
    to ensure uniqueness.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem use

    Example:
        >>> sanitize_filename("my file.txt")
        'my_file.txt'
        >>> sanitize_filename("my:file?.txt")
        'my_file__a1b2.txt'
    """
    name, ext = os.path.splitext(filename)
    sanitized = re.sub(r'[\\/*?:"<>| ]+', '_', name)
    if sanitized == name:
        return filename
    hash_suffix = hashlib.md5(filename.encode()).hexdigest()[:4]
    return f"{sanitized}_{hash_suffix}{ext}"


def setup_logging(
    logdir: str = ".",
    logfile: str = "coshsh.log",
    scrnloglevel: int = logging.INFO,
    txtloglevel: int = logging.INFO,
    format: str = "%(asctime)s - %(levelname)s - %(message)s",
    backup_count: int = 2
) -> logging.Logger:
    """Setup logging configuration for coshsh.

    Configures both file and console logging with rotating file handlers.
    Can be called multiple times (e.g., in unit tests).

    Args:
        logdir: Directory for log files
        logfile: Log filename
        scrnloglevel: Console log level (default: INFO)
        txtloglevel: File log level (default: INFO)
        format: Log message format string
        backup_count: Number of backup log files to keep

    Returns:
        Configured logger instance

    Note:
        This function stores configuration in function attributes for later
        use by switch_logging() and restore_logging().
    """
    logdir = os.path.abspath(logdir)
    abs_logfile = logfile if os.path.isabs(logfile) else os.path.join(logdir, logfile)

    # Create log directory if it doesn't exist
    log_parent = os.path.dirname(abs_logfile)
    if not os.path.exists(log_parent):
        os.makedirs(log_parent, 0o755)

    setup_logging.logger_name = os.path.basename(abs_logfile).replace(".log", "")
    logger = logging.getLogger(setup_logging.logger_name)

    if logger.hasHandlers():
        # This method can be called multiple times (e.g., in unit tests)
        for handler in list(logger.handlers):  # Create a copy of the list
            handler.close()
            logger.removeHandler(handler)

    logger.setLevel(logging.DEBUG)
    log_formatter = logging.Formatter(format)

    # File handler with rotation
    txt_handler = RotatingFileHandler(
        abs_logfile,
        backupCount=backup_count,
        maxBytes=20 * 1024 * 1024,  # 20MB
        delay=True
    )
    txt_handler.setFormatter(log_formatter)
    txt_handler.setLevel(txtloglevel)
    logger.addHandler(txt_handler)
    logger.debug("Logger initialized.")

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(scrnloglevel)
    logger.addHandler(console_handler)

    # Store configuration in function attributes for switch_logging/restore_logging
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


def switch_logging(**kwargs: Any) -> None:
    """Switch logging to a different log file.

    Changes the log file target while preserving other logging configuration.
    Used by recipes to write to recipe-specific log files.

    Args:
        **kwargs: Optional keyword arguments:
            logdir: New log directory
            logfile: New log filename
            backup_count: Number of backup files

    Note:
        If the abs_logfile hasn't changed, this function returns immediately.
    """
    logdir = kwargs.get("logdir", setup_logging.logdir)
    logfile = kwargs.get("logfile", setup_logging.logfile)
    backup_count = kwargs.get("backup_count", setup_logging.backup_count)

    # Handle None values
    logdir = setup_logging.logdir if logdir is None else logdir
    logfile = setup_logging.logfile if logfile is None else logfile
    backup_count = setup_logging.backup_count if backup_count is None else backup_count

    abs_logfile = logfile if os.path.isabs(logfile) else os.path.join(logdir, logfile)

    # No change needed
    if abs_logfile == setup_logging.abs_logfile:
        return

    # Create directory if needed
    log_parent = os.path.dirname(abs_logfile)
    if not os.path.exists(log_parent):
        os.makedirs(log_parent, 0o755)

    logger = logging.getLogger(setup_logging.logger_name)
    logger.debug(f"Logger switches to {abs_logfile}")

    # Remove old file handlers
    logger.removeHandler(setup_logging.txt_handler)
    for handler in list(logger.handlers):  # Create a copy of the list
        if hasattr(handler, "baseFilename"):
            logger.removeHandler(handler)

    # Add new file handler
    txt_handler = RotatingFileHandler(
        abs_logfile,
        backupCount=backup_count,
        maxBytes=20 * 1024 * 1024,  # 20MB
        delay=True
    )
    txt_handler.setFormatter(setup_logging.log_formatter)
    txt_handler.setLevel(setup_logging.txtloglevel)
    logger.addHandler(txt_handler)

def restore_logging() -> None:
    """Restore logging to the original configuration set by setup_logging().

    Switches back to the original log file after a call to switch_logging().
    """
    switch_logging(logdir=setup_logging.logdir, logfile=setup_logging.logfile)
    logger = logging.getLogger('coshsh')
    logger.debug(f"Logger restored to {setup_logging.logdir}/{setup_logging.logfile}\n")


def get_logger(name: str = "coshsh") -> logging.Logger:
    """Get a logger instance by name.

    Args:
        name: Logger name (default: "coshsh")

    Returns:
        Logger instance
    """
    return logging.getLogger(name)

