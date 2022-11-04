import os
import io
from random import choices, randint
from string import ascii_lowercase
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):
    _configfile = 'etc/coshsh.cfg'
    _objectsdir = "./var/objects/test10"

    def print_header(self):
        print("#" * 80 + "\n" + "#" + " " * 78 + "#")
        print("#" + str.center(self.id(), 78) + "#")
        print("#" + " " * 78 + "#\n" + "#" * 80 + "\n")

    def setUps(self):
        self.config = coshsh.configparser.CoshshConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = coshsh.generator.Generator()
        setup_logging()

    def tearDowns(self):
        shutil.rmtree("./var/objects/test10", True)
        pass

    def test_host_templates_order(self):
        self.setUpConfig("etc/coshsh.cfg", "test10")
        r = self.generator.get_recipe("test10")
        r.count_before_objects()
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        saved_templates = {}
        for host in r.objects["hosts"].values():
            for len in range(3, randint(4, 10)):
                host.templates.append("".join(choices(ascii_lowercase, k=len)))
            saved_templates[host.host_name] = [t for t in host.templates]
            print("{} has {}".format(host.host_name, ",".join(host.templates)))
        r.assemble()
        r.render()
        for host in r.objects["hosts"].values():
            print("{} has {}".format(host.host_name, ",".join(host.templates)))
            pass

        self.assertTrue(hasattr(r.objects['hosts']['test_host_0'], 'config_files'))
        self.assertTrue('host.cfg' in r.objects['hosts']['test_host_0'].config_files['nagios'])

        r.output()
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts"))
        for host in r.objects["hosts"].values():
            self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/"+host.host_name+"/host.cfg"))
            with io.open("var/objects/test10/dynamic/hosts/"+host.host_name+"/host.cfg") as f:
                host_cfg = f.read()
                self.assertTrue(",".join(saved_templates[host.host_name]) in host_cfg)



