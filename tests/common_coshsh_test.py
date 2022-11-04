import sys
sys.dont_write_bytecode = True
import os
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
import unittest
from coshsh.configparser import CoshshConfigParser
import shutil
import logging
import pprint
import coshsh
from coshsh.generator import Generator
from coshsh.datasource import Datasource
from coshsh.datarecipient import Datarecipient
from coshsh.host import Host
from coshsh.application import Application
from coshsh.monitoringdetail import MonitoringDetail
from coshsh.contact import Contact
from coshsh.util import setup_logging

logger = logging.getLogger('coshsh')

class CommonCoshshTest(unittest.TestCase):
    def print_header(self):
        print("#" * 80 + "\n" + "#" + " " * 78 + "#")
        print("#" + str.center(self.id(), 78) + "#")
        print("#" + " " * 78 + "#\n" + "#" * 80 + "\n")

    def setUp(self):
        self.print_header()
        Application.class_factory = []
        MonitoringDetail.class_factory = []
        Contact.class_factory = []
        Datasource.class_factory = []
        Datarecipient.class_factory = []
        self.called_from_dir = os.getcwd()
        self.tests_run_in_dir = os.path.dirname(os.path.realpath(__file__))
        self.coshsh_base_dir = os.path.dirname(self.tests_run_in_dir)
        os.chdir(self.tests_run_in_dir)
        if not self.tests_run_in_dir in sys.path:
            sys.path.append(self.coshsh_base_dir)
        sys.path = list(set([p for p in sys.path if not self.tests_run_in_dir in os.path.realpath(p)]))
        self.generator = coshsh.generator.Generator()
        setup_logging(scrnloglevel=logging.DEBUG)
        if hasattr(self, "mySetUp"):
            getattr(self, "mySetUp")()
        if hasattr(self, "_configfile"):
            if not hasattr(self, "default_recipe"):
                self.default_recipe = None
            if not hasattr(self, "default_log_level"):
                self.default_log_level = "info"
            if not hasattr(self, "force"):
                self.force = False
            if not hasattr(self, "safe_output"):
                self.safe_output = False
            self.setUpConfig(self._configfile, None, "info", False, False)
        if hasattr(self, "_objectsdir"):
            self.setUpObjectsDir()
        if hasattr(self, "mySetUpRm"):
            getattr(self, "mySetUpRm")()
        if hasattr(self, "mySetUpMk"):
            getattr(self, "mySetUpMk")()
        self.pp = pprint.PrettyPrinter(indent=4)


    def setUpConfig(self, configfile, default_recipe, default_log_level="info", force=False, safe_output=False):
        self.generator.read_cookbook([configfile], default_recipe, default_log_level, force, safe_output)

    def setUpObjectsDir(self):
        if not isinstance(self._objectsdir, list):
            self._objectsdir = [self._objectsdir]
        for od in self._objectsdir:
            shutil.rmtree(od, True)
            os.makedirs(od)

    def tearDown(self):
        if hasattr(self, "generator"):
            for recipe in self.generator.recipes.values():
                if hasattr(recipe, "objects_dir"):
                    objects_dir = os.path.realpath(recipe.objects_dir)
                    if objects_dir.startswith(self.tests_run_in_dir) and len(objects_dir) > len(self.tests_run_in_dir):
                        shutil.rmtree(objects_dir, True)
            if hasattr(self.generator, "log_dir"):
                shutil.rmtree(self.generator.log_dir, True)

        if hasattr(self, '_objectsdir'):
            if not isinstance(self._objectsdir, list):
                self._objectsdir = [self._objectsdir]
            for od in self._objectsdir:
                shutil.rmtree(od, True)
                os.makedirs(od)
        os.chdir(self.called_from_dir)

    def clean_generator(self):
        self.generator = None
        self.generator = coshsh.generator.Generator()
        setup_logging()

    def print_header(self):
        print("#" * 80 + "\n" + "#" + " " * 78 + "#")
        print("#" + str.center(self.id(), 78) + "#")
        print("#" + " " * 78 + "#\n" + "#" * 80 + "\n")

