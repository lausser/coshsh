"""Tests for log file creation, log level filtering, and log content after a recipe run."""

import os
import io
import shutil
import logging
from coshsh.util import setup_logging
from tests.common_coshsh_test import CommonCoshshTest


class LoggingTest(CommonCoshshTest):

    def tearDown(self):
        pass

    def test_log(self):
        """Verify log file is created, WARNING and INFO are written, DEBUG is filtered out."""
        shutil.rmtree("./var/log", True)
        os.makedirs("./var/log")
        setup_logging(logfile="zishsh.log", logdir="./var/log", scrnloglevel=logging.DEBUG, txtloglevel=logging.INFO)
        # default, wie im coshsh-cook
        setup_logging(logdir="./var/log", scrnloglevel=logging.INFO)
        logger = logging.getLogger('zishsh')
        logger.warning("i warn you")
        logger.info("i inform you")
        logger.debug("i spam you")
        self.assertTrue(os.path.exists("./var/log/zishsh.log"))
        with io.open('./var/log/zishsh.log') as x:
            zishshlog = x.read()
        self.assertIn("WARNING", zishshlog)
        self.assertIn("INFO", zishshlog)
        self.assertNotIn("DEBUG", zishshlog)

    def test_write(self):
        """Verify recipe run creates host config files and writes entries to the coshsh log."""
        self.setUpConfig("etc/coshsh.cfg", "test4")
        r = self.generator.get_recipe("test4")
        self.generator.run()
        self.assertTrue(hasattr(r.objects['hosts']['test_host_0'], 'config_files'))
        self.assertIn('host.cfg', r.objects['hosts']['test_host_0'].config_files['nagios'])
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg"))
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertIn('os_windows_default_check_unittest', os_windows_default_cfg)
        self.assertTrue(os.path.exists("./var/log/coshsh.log"))
        with io.open('./var/log/coshsh.log') as x:
            coshshlog = x.read()
        self.assertIn("test_host_0", coshshlog)
