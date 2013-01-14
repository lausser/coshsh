#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
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
        if k != k.lower():
            if the_dict[k] != None and isinstance(the_dict[k], basestring):
                the_dict[k.lower()] = the_dict[k].strip()
            del the_dict[k]
        else:
            if the_dict[k] != None and isinstance(the_dict[k], basestring):
                the_dict[k] = the_dict[k].strip()
    for attr in [k for k in the_dict.keys() if k in titles]:
        the_dict[attr] = the_dict[attr].lower()


