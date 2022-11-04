import os
import io
import shutil
import logging
from coshsh.util import setup_logging
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def tearDown(self):
        #shutil.rmtree("./var/objects/test1", True)
        print()

    def test_log(self):
        shutil.rmtree("./var/log", True)
        os.makedirs("./var/log")
        setup_logging(logfile="zishsh.log", logdir="./var/log", scrnloglevel=logging.DEBUG, txtloglevel=logging.INFO)
        # default, wie im coshsh-cook
        setup_logging(logdir="./var/log", scrnloglevel=logging.INFO)
        logger = logging.getLogger('zishsh')
        print(logger.__dict__)
        print
        for h in logger.handlers:
            print(h.__dict__)
            print
        logger.warning("i warn you")
        logger.info("i inform you")
        logger.debug("i spam you")
        self.assertTrue(os.path.exists("./var/log/zishsh.log"))
        with io.open('./var/log/zishsh.log') as x:
            zishshlog = x.read()
        self.assertTrue("WARNING" in zishshlog)
        self.assertTrue("INFO" in zishshlog)
        self.assertTrue("DEBUG" not in zishshlog)

    def test_write(self):
        self.setUpConfig("etc/coshsh.cfg", "test4")
        r = self.generator.get_recipe("test4")
        self.generator.run()
        self.assertTrue(hasattr(r.objects['hosts']['test_host_0'], 'config_files'))
        self.assertTrue('host.cfg' in r.objects['hosts']['test_host_0'].config_files['nagios'])
        #r.output()
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg"))
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue('os_windows_default_check_unittest' in os_windows_default_cfg)
        self.assertTrue(os.path.exists("./var/log/coshsh.log"))
        with io.open('./var/log/coshsh.log') as x:
            coshshlog = x.read()
        self.assertTrue("test_host_0" in coshshlog)



