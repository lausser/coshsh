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
log_level = logging.DEBUG
basic_log_handler = TimedRotatingFileHandler(path,'midnight',backupCount=5)
basic_log_handler.setLevel(log_level)
basic_log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s")
basic_log_handler.setFormatter(basic_log_formatter)
logger = logging.getLogger()
#logger.addHandler(basic_log_handler)
logger.setLevel(log_level)

console_handler = logging.StreamHandler(sys.stderr)
#console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


