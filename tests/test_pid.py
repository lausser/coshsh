import unittest
import random
import re
import os
import sys
import shutil
import string
import tempfile
from optparse import OptionParser
import ConfigParser
import logging
from logging import INFO, DEBUG


sys.dont_write_bytecode = True

import coshsh
from coshsh.generator import Generator
from coshsh.datasource import Datasource
from coshsh.application import Application
from coshsh.util import substenv, setup_logging

class CoshshTest(unittest.TestCase):
    def print_header(self):
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def setUp(self):
        shutil.rmtree("./var/objects/test1", True)
        os.makedirs("./var/objects/test1")
        shutil.rmtree("./var/tmp", True)
        os.makedirs("./var/tmp")
        recipe_configs = {}
        datasource_configs = {}
        datarecipient_configs = {}
        cookbook = ConfigParser.ConfigParser()
        cookbook.read("etc/coshsh.cfg")
        for ds in [section for section in cookbook.sections() if section.startswith('datarecipient_')]:
            datarecipient_configs[ds.replace("datarecipient_", "", 1).lower()] = cookbook.items(ds) + [('name', ds.replace("datarecipient_", "", 1).lower())]
        for ds in [section for section in cookbook.sections() if section.startswith('datasource_')]:
            datasource_configs[ds.replace("datasource_", "", 1).lower()] = cookbook.items(ds) + [('name', ds.replace("datasource_", "", 1).lower())]
        for recipe in [section for section in cookbook.sections() if section.startswith('recipe_')]:
            recipe_configs[recipe.replace("recipe_", "", 1).lower()] = cookbook.items(recipe) + [('name', recipe.replace("recipe_", "", 1).lower())]
        recipes = []
        if False:
            pass
            #recipes = [r.lower() for r in opts.default_recipe.split(",")]
        else:
            if "defaults" in cookbook.sections() and "recipes" in [c[0] for c in cookbook.items("defaults")]:
                recipes = [recipe.lower() for recipe in dict(cookbook.items("defaults"))["recipes"].split(",")]
            else:
                recipes = recipe_configs.keys()
        if "defaults" in cookbook.sections() and "log_dir" in [c[0] for c in cookbook.items("defaults")]:
            log_dir = dict(cookbook.items("defaults"))["log_dir"]
            log_dir = re.sub('%.*?%', substenv, log_dir)
        else:
            coshsh_home = os.path.join(os.path.dirname(__file__), '..', 'coshsh')
            os.environ['COSHSH_HOME'] = coshsh_home
            log_dir = os.path.join(os.environ['COSHSH_HOME'], "..")
        if "defaults" in cookbook.sections() and "pid_dir" in [c[0] for c in cookbook.items("defaults")]:
            pid_dir = dict(cookbook.items("defaults"))["pid_dir"]
            pid_dir = re.sub('%.*?%', substenv, pid_dir)
        else:
            pid_dir = os.path.join(os.environ['COSHSH_HOME'], "..")
        self.generator = coshsh.generator.Generator()
	setup_logging(scrnloglevel=DEBUG)
        for recipe in recipes:
            if recipe == 'test1':
                recipe_configs[recipe].append(('pid_dir', pid_dir))
                self.generator.add_recipe(**dict(recipe_configs[recipe]))



    def tearDown(self):
        if os.path.exists(self.generator.recipes['test1'].pid_file):
            os.remove(self.generator.recipes['test1'].pid_file)

    def test_run(self):
        self.print_header()
        self.generator.run()

    def test_pid_exists(self):
        self.print_header()
        pid_file = self.generator.recipes['test1'].pid_protect()
        self.assert_(os.path.exists(pid_file))

    def test_pid_exists(self):
        self.print_header()
        pid_file = self.generator.recipes['test1'].pid_protect()
        self.assert_(os.path.exists(pid_file))
        pid = open(self.generator.recipes['test1'].pid_file).read().strip()
        self.assert_(pid == str(os.getpid()))
        self.generator.recipes['test1'].pid_remove()
        self.assert_(not os.path.exists(pid_file))

    def test_pid_stale(self):
        self.print_header()
        while True:
            pid = random.randrange(1,50000)
            try:
                os.kill(pid, 0)
            except OSError, (code, text):
                # does not exist
                file(self.generator.recipes['test1'].pid_file, 'w').write(str(pid))
                print "stale pid is", open(self.generator.recipes['test1'].pid_file).read().strip()
                break
        pid_file = self.generator.recipes['test1'].pid_protect()
        self.assert_(os.path.exists(pid_file))
        pid = open(self.generator.recipes['test1'].pid_file).read().strip()
        print "my pid is", open(self.generator.recipes['test1'].pid_file).read().strip()
        self.assert_(pid == str(os.getpid()))

    def test_pid_blocked(self):
        self.print_header()
        while True:
            pid = random.randrange(1,50000)
            try:
                os.kill(pid, 0)
                file(self.generator.recipes['test1'].pid_file, 'w').write(str(pid))
                print "running pid is", open(self.generator.recipes['test1'].pid_file).read().strip()
                break
            except OSError, (code, text):
                # does not exist
                pass
        try:
            pid_file = self.generator.recipes['test1'].pid_protect()
        except Exception, exp:
            print "exp is ", exp.__class__.__name__
        self.assert_(exp.__class__.__name__ == "RecipePidAlreadyRunning")

    def test_pid_garbled(self):
        self.print_header()
        file(self.generator.recipes['test1'].pid_file, 'w').write("schlonz")
        self.generator.run()
        try:
            pid_file = self.generator.recipes['test1'].pid_protect()
        except Exception, exp:
            print "exp is ", exp.__class__.__name__
        self.assert_(exp.__class__.__name__ == "RecipePidGarbage")

    def test_pid_empty(self):
        self.print_header()
        pid_file = self.generator.recipes['test1'].pid_file
        open(pid_file, 'a').close()
        self.generator.run()
        # bricht ab wegen garbage, loescht aber das pid-file
        self.assert_(not os.path.exists(pid_file))
        self.assert_(not os.path.exists("var/objects/test1/dynamic/hosts"))
        self.generator.run()
        # loescht das pid-file, weil der lauf ganz normal war
        self.assert_(not os.path.exists(pid_file))
        self.assert_(os.path.exists("var/objects/test1/dynamic/hosts"))

    def test_pid_perms(self):
        self.print_header()
        #self.generator.recipes['test1'].pid_dir = "/"
        self.generator.recipes['test1'].pid_dir = os.path.join(os.getcwd(), 'hundsglumpvarreckts')
        os.mkdir(self.generator.recipes['test1'].pid_dir)
        self.generator.run()
        os.chmod(self.generator.recipes['test1'].pid_dir, 0)
        try:
            pid_file = self.generator.recipes['test1'].pid_protect()
            os.remove(self.generator.recipes['test1'].pid_file)
        except Exception, exp:
            print "exp is ", exp.__class__.__name__
        self.assert_(exp.__class__.__name__ == "RecipePidNotWritable")
        os.rmdir(self.generator.recipes['test1'].pid_dir)
        
if __name__ == '__main__':
    unittest.main()


