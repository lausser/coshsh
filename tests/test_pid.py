import os
import io
import shutil
import random
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def tearDown(self):
        super(CoshshTest, self).tearDown()
        if os.path.exists(self.generator.recipes['test1'].pid_file):
            os.remove(self.generator.recipes['test1'].pid_file)

    def test_run(self):
        self.setUpConfig("etc/coshsh.cfg", "test1")
        self.generator.run()

    def test_pid_exists(self):
        self.setUpConfig("etc/coshsh.cfg", "test1")
        pid_file = self.generator.recipes['test1'].pid_protect()
        self.assertTrue(os.path.exists(pid_file))

    def test_pid_exists2(self):
        self.setUpConfig("etc/coshsh.cfg", "test1")
        pid_file = self.generator.recipes['test1'].pid_protect()
        self.assertTrue(os.path.exists(pid_file))
        with io.open(self.generator.recipes['test1'].pid_file) as f:
            pid = f.read().strip()
        self.assertTrue(pid == str(os.getpid()))
        self.generator.recipes['test1'].pid_remove()
        self.assertTrue(not os.path.exists(pid_file))

    def test_pid_stale(self):
        self.setUpConfig("etc/coshsh.cfg", "test1")
        while True:
            pid = random.randrange(1,50000)
            if not self.generator.recipes['test1'].pid_exists(pid):
                # does not exist
                with io.open(self.generator.recipes['test1'].pid_file, 'w') as f:
                    f.write(str(pid))
                print("stale pid is", pid)
                break
        pid_file = self.generator.recipes['test1'].pid_protect()
        self.assertTrue(os.path.exists(pid_file))
        with io.open(self.generator.recipes['test1'].pid_file) as f:
            pid = f.read().strip()
            print("my pid is", pid)
            self.assertTrue(pid == str(os.getpid()))
        

    def test_pid_blocked(self):
        self.setUpConfig("etc/coshsh.cfg", "test1")
        while True:
            pid = random.randrange(1,50000)
            if self.generator.recipes['test1'].pid_exists(pid):
                with io.open(self.generator.recipes['test1'].pid_file, 'w') as f:
                    f.write(str(pid))
                print("running pid is", pid)
                break
        try:
            pid_file = self.generator.recipes['test1'].pid_protect()
        except Exception as exp:
            print("exp is ", exp.__class__.__name__)
            self.assertTrue(exp.__class__.__name__ == "RecipePidAlreadyRunning")
        else:
            fail("running pid did not force an abort")

    def test_pid_garbled(self):
        self.setUpConfig("etc/coshsh.cfg", "test1")
        with io.open(self.generator.recipes['test1'].pid_file, 'w') as f:
            f.write("schlonz")
        self.generator.run()
        try:
            pid_file = self.generator.recipes['test1'].pid_protect()
        except Exception as exp:
            print("exp is ", exp.__class__.__name__)
            self.assertTrue(exp.__class__.__name__ == "RecipePidGarbage")
        else:
            fail("garbage in pid file was not correctly identified")

    def test_pid_empty(self):
        self.setUpConfig("etc/coshsh.cfg", "test1")
        pid_file = self.generator.recipes['test1'].pid_file
        open(pid_file, 'a').close()
        shutil.rmtree("var/objects/test1/dynamic/hosts", True)
        self.generator.run()
        # bricht ab wegen garbage, loescht aber das pid-file
        self.assertTrue(not os.path.exists(pid_file))
        self.assertTrue(not os.path.exists("var/objects/test1/dynamic/hosts"))
        self.generator.run()
        # loescht das pid-file, weil der lauf ganz normal war
        self.assertTrue(not os.path.exists(pid_file))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts"))

    def test_pid_perms(self):
        self.setUpConfig("etc/coshsh.cfg", "test1")
        self.generator.recipes['test1'].pid_dir = os.path.join(os.getcwd(), 'hundsglumpvarreckts')
        os.mkdir(self.generator.recipes['test1'].pid_dir)
        self.generator.run()
        os.chmod(self.generator.recipes['test1'].pid_dir, 0)
        try:
            pid_file = self.generator.recipes['test1'].pid_protect()
            os.remove(self.generator.recipes['test1'].pid_file)
        except Exception as exp:
            print("exp is ", exp.__class__.__name__)
            self.assertTrue(exp.__class__.__name__ == "RecipePidNotWritable")
        else:
            fail("non-writable pid dir was not correctly detected")
        finally:
            os.rmdir(self.generator.recipes['test1'].pid_dir)
        

