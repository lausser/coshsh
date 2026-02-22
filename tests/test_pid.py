"""Tests for recipe PID-file protection — creation, stale PID detection, active PID blocking, garbled content, empty file, and unwritable directory."""

import io
import os
import random
import shutil

from tests.common_coshsh_test import CommonCoshshTest


class PidTest(CommonCoshshTest):

    def tearDown(self):
        super(PidTest, self).tearDown()
        if os.path.exists(self.generator.recipes["test1"].pid_file):
            os.remove(self.generator.recipes["test1"].pid_file)

    def test_run(self):
        """Full generator run completes without error."""
        self.setUpConfig("etc/coshsh.cfg", "test1")
        self.generator.run()

    def test_pid_exists(self):
        """pid_protect() creates the pid file."""
        self.setUpConfig("etc/coshsh.cfg", "test1")
        pid_file = self.generator.recipes["test1"].pid_protect()
        self.assertTrue(os.path.exists(pid_file))

    def test_pid_exists2(self):
        """pid_protect() writes the current process PID, and pid_remove() deletes the file."""
        self.setUpConfig("etc/coshsh.cfg", "test1")
        pid_file = self.generator.recipes["test1"].pid_protect()
        self.assertTrue(os.path.exists(pid_file))
        with io.open(self.generator.recipes["test1"].pid_file) as f:
            pid = f.read().strip()
        self.assertEqual(pid, str(os.getpid()))
        self.generator.recipes["test1"].pid_remove()
        self.assertFalse(os.path.exists(pid_file))

    def test_pid_stale(self):
        """Stale PID file (non-running process) is overwritten by pid_protect()."""
        self.setUpConfig("etc/coshsh.cfg", "test1")
        while True:
            pid = random.randrange(1, 50000)
            if not self.generator.recipes["test1"].pid_exists(pid):
                with io.open(self.generator.recipes["test1"].pid_file, "w") as f:
                    f.write(str(pid))
                break
        pid_file = self.generator.recipes["test1"].pid_protect()
        self.assertTrue(os.path.exists(pid_file))
        with io.open(self.generator.recipes["test1"].pid_file) as f:
            pid = f.read().strip()
            self.assertEqual(pid, str(os.getpid()))

    def test_pid_blocked(self):
        """Active PID file (running process) causes pid_protect() to raise RecipePidAlreadyRunning."""
        self.setUpConfig("etc/coshsh.cfg", "test1")
        while True:
            pid = random.randrange(1, 50000)
            if self.generator.recipes["test1"].pid_exists(pid):
                with io.open(self.generator.recipes["test1"].pid_file, "w") as f:
                    f.write(str(pid))
                break
        try:
            pid_file = self.generator.recipes["test1"].pid_protect()
        except Exception as exp:
            self.assertEqual(exp.__class__.__name__, "RecipePidAlreadyRunning")
        else:
            self.fail("running pid did not force an abort")

    def test_pid_garbled(self):
        """Garbage in PID file causes pid_protect() to raise RecipePidGarbage."""
        self.setUpConfig("etc/coshsh.cfg", "test1")
        with io.open(self.generator.recipes["test1"].pid_file, "w") as f:
            f.write("schlonz")
        self.generator.run()
        try:
            pid_file = self.generator.recipes["test1"].pid_protect()
        except Exception as exp:
            self.assertEqual(exp.__class__.__name__, "RecipePidGarbage")
        else:
            self.fail("garbage in pid file was not correctly identified")

    def test_pid_empty(self):
        """Empty PID file is treated as garbage; generator cleans it up on next run."""
        self.setUpConfig("etc/coshsh.cfg", "test1")
        pid_file = self.generator.recipes["test1"].pid_file
        open(pid_file, "a").close()
        shutil.rmtree("var/objects/test1/dynamic/hosts", True)
        self.generator.run()
        # aborts due to garbage, but removes the pid file
        self.assertFalse(os.path.exists(pid_file))
        self.assertFalse(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.generator.run()
        # removes the pid file because the run completed normally
        self.assertFalse(os.path.exists(pid_file))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts"))

    def test_pid_perms(self):
        """Unwritable PID directory causes pid_protect() to raise RecipePidNotWritable."""
        self.setUpConfig("etc/coshsh.cfg", "test1")
        self.generator.recipes["test1"].pid_dir = os.path.join(os.getcwd(), "hundsglumpvarreckts")
        os.mkdir(self.generator.recipes["test1"].pid_dir)
        self.generator.run()
        os.chmod(self.generator.recipes["test1"].pid_dir, 0)
        try:
            pid_file = self.generator.recipes["test1"].pid_protect()
            os.remove(self.generator.recipes["test1"].pid_file)
        except Exception as exp:
            self.assertEqual(exp.__class__.__name__, "RecipePidNotWritable")
        else:
            self.fail("non-writable pid dir was not correctly detected")
        finally:
            os.rmdir(self.generator.recipes["test1"].pid_dir)
