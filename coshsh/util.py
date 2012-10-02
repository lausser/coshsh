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

