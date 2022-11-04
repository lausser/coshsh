import os
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):
    _configfile = 'etc/timeperiods.cfg'
    _objectsdir = "./var/objects/tp"
    default_recipe = "test10"

    def print_header(self):
        print("#" * 80 + "\n" + "#" + " " * 78 + "#")
        print("#" + str.center(self.id(), 78) + "#")
        print("#" + " " * 78 + "#\n" + "#" * 80 + "\n")

    def setUps(self):
        os.chdir(os.path.realpath(os.path.dirname(__file__)))
        self.config = coshsh.configparser.CoshshConfigParser()
        self.config.read('etc/timeperiods.cfg')
        self.generator = coshsh.generator.Generator()
        #setup_logging()
        setup_logging(scrnloglevel=logging.DEBUG)

    def tearDowns(self):
        #shutil.rmtree("./var/objects/tp", True)
        pass

    def test_create_recipe_multiple_sources(self):
        self.setUpConfig("etc/timeperiods.cfg", "test10")
        r = self.generator.get_recipe("test10")
        # remove target dir / create empty
        r.count_before_objects()
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        r.assemble()
        r.render()
        self.assertTrue(hasattr(r.objects['hosts']['monops_tp_cmd_dummy_host'], 'config_files'))
        self.assertTrue('host.cfg' in r.objects['hosts']['monops_tp_cmd_dummy_host'].config_files['nagios'])

        # write hosts/apps to the filesystem
        self.generator.recipes['test10'].output()
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/monops_tp_cmd_dummy_host"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts//monops_tp_cmd_dummy_host/timeperiods_monops.cfg"))


