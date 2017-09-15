#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import time
import re
import copy
import os
from UserDict import DictMixin


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

