#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright 2010-2012 Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import time
import sys
import logging
from logging.handlers import TimedRotatingFileHandler

path = "./coshsh.log"
# Open the log and set to rotate once a day
basic_log_handler = TimedRotatingFileHandler(path,'midnight',backupCount=5)
basic_log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s - %(message)s"))
basic_log_handler.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s - %(message)s"))
console_handler.setLevel(logging.INFO)
logger = logging.getLogger()
logger.addHandler(basic_log_handler)
logger.addHandler(console_handler)
logger.setLevel(logging.DEBUG)


