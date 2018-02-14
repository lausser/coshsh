#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import time
import sys
import re
import copy
import os
import logging
from logging.handlers import RotatingFileHandler
from UserDict import DictMixin

global_log_dir = "/"

class odict(DictMixin):
    """
    Copied from 
    http://code.activestate.com/recipes/496761-a-more-clean-implementation-for-ordered-dictionary/
    Thanks! I use the odict class for generator.recipes
    """
    def __init__(self):
        self._keys = []
        self._data = {}

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


def compare_attr(key, params, strings):
    if not isinstance(strings, list):
        strings = [strings]
    if key in params:
        if params[key] == None:
            return False
        elif [str1 for str1 in strings if re.match(str1, params[key], re.IGNORECASE)]:
            return True
    return False

def is_attr(key, params, strings):
    if not isinstance(strings, list):
        strings = [strings]
    if key in params:
        if [str1 for str1 in strings if str1.lower() == params[key].lower()]:
            return True
    return False

def cleanout(dirty_string, delete_chars="", delete_words=[]):
    if not dirty_string:
        return dirty_string
    for dirt in delete_words + list(delete_chars):
        dirty_string = dirty_string.replace(dirt, "")
    return dirty_string.strip()

def substenv(matchobj):
    if matchobj.group(0).replace('%', '') in os.environ.keys():
        return os.environ[matchobj.group(0).replace('%', '')]
    else:
        return matchobj.group(0)

def normalize_dict(the_dict, titles=[]):
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
    translations = (
        (u'\N{LATIN SMALL LETTER SHARP S}', u'ss'),
        (u'\N{LATIN SMALL LETTER O WITH DIAERESIS}', u'oe'),
        (u'\N{LATIN SMALL LETTER U WITH DIAERESIS}', u'ue'),
        (u'\N{LATIN CAPITAL LETTER A WITH DIAERESIS}', u'Ae'),
        (u'\N{LATIN CAPITAL LETTER O WITH DIAERESIS}', u'Oe'),
        (u'\N{LATIN CAPITAL LETTER U WITH DIAERESIS}', u'Ue'),
        # et cetera
    )
    for from_str, to_str in translations:
        text = text.replace(from_str, to_str)
    return text

def setup_logging(logdir=".", logfile="coshsh.log", scrnloglevel=logging.INFO, txtloglevel=logging.INFO):
    logdir = os.path.abspath(logdir)
    abs_logfile = logfile if os.path.isabs(logfile) else os.path.join(logdir, logfile)
    if not os.path.exists(os.path.dirname(abs_logfile)):
        os.mkdir(os.path.dirname(abs_logfile))
   
    logger = logging.getLogger('coshsh')
    if logger.handlers:
        # this method can be called multiple times in the unittests
        logger.handlers = []
    logger.setLevel(logging.DEBUG)
    log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    txt_handler = RotatingFileHandler(abs_logfile, backupCount=2, maxBytes=20*1024*1024)
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


def switch_logging(**kwargs):
    logdir = kwargs.get("logdir", setup_logging.logdir)
    logfile = kwargs.get("logfile", setup_logging.logfile)
    logdir = setup_logging.logdir if logdir == None else logdir
    logfile = setup_logging.logfile if logfile == None else logfile
    abs_logfile = logfile if os.path.isabs(logfile) else os.path.join(logdir, logfile)
    if abs_logfile == setup_logging.abs_logfile:
        return
    if not os.path.exists(os.path.dirname(abs_logfile)):
        os.mkdir(os.path.dirname(abs_logfile))
    logger = logging.getLogger('coshsh')
    logger.debug("Logger switches to " + abs_logfile)
    # remove the txt_handler
    logger.removeHandler(setup_logging.txt_handler)
    for handler in logger.handlers:
        if hasattr(handler, "baseFilename"):
            logger.removeHandler(handler)
    txt_handler = RotatingFileHandler(abs_logfile, backupCount=2, maxBytes=20*1024*1024)
    txt_handler.setFormatter(setup_logging.log_formatter)
    txt_handler.setLevel(setup_logging.txtloglevel)
    logger.addHandler(txt_handler)

def restore_logging():
    switch_logging(logdir=setup_logging.logdir, logfile=setup_logging.logfile)
    logger = logging.getLogger('coshsh')
    logger.debug("Logger restored to " + setup_logging.abs_logfile)

def get_logger(self, name="coshsh"):
    return logging.getLogger(name)

