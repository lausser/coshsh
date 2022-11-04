import os
import shutil
import io
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def test_osenviron(self):
        self.setUpConfig("etc/coshsh.cfg", "test4b")
        r = self.generator.get_recipe("test4b")
        # remove target dir / create empty
        r.count_before_objects()
        r.cleanup_target_dir()

        r.prepare_target_dir()
        # check target

        # read the datasources
        r.collect()
        r.assemble()
        
        # for each host, application get the corresponding template files
        # get the template files and cache them in a struct owned by the recipe
        # resolve the templates and attach the result as config_files to host/app
        r.render()
        self.assertTrue(hasattr(r.objects['hosts']['test_host_0'], 'config_files'))
        self.assertTrue('host.cfg' in r.objects['hosts']['test_host_0'].config_files["nagios"])

        # write hosts/apps to the filesystem
        r.output()
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg"))
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue('environment variable COSHSHENV1 ()' in os_windows_default_cfg)
        self.assertTrue('environment default COSHSHENV1 (schlurz)' in os_windows_default_cfg)

        shutil.rmtree("./var/objects/test1", True)
        os.makedirs("./var/objects/test1")
        os.environ["COSHSHENV1"] = "die nr 1"
        os.environ["COSHSHENV2"] = "die nr 2"
        r.render()
        r.output()
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue('environment variable COSHSHENV1 (die nr 1)' in os_windows_default_cfg)
        self.assertTrue('environment variable COSHSHENV2 (die nr 2)' in os_windows_default_cfg)
        self.assertTrue('environment default COSHSHENV1 (die nr 1)' in os_windows_default_cfg)
        self.assertTrue('environment variante die nr 2' in os_windows_default_cfg)

        shutil.rmtree("./var/objects/test1", True)
        os.makedirs("./var/objects/test1")
        os.environ["COSHSHENV1"] = "variante1"
        r.render()
        r.output()
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue('environment variable COSHSHENV1 (variante1)' in os_windows_default_cfg)
        self.assertTrue('environment variable COSHSHENV2 (die nr 2)' in os_windows_default_cfg)
        self.assertTrue('environment variante variante1' in os_windows_default_cfg)

        shutil.rmtree("./var/objects/test1", True)
        os.makedirs("./var/objects/test1")
        os.environ["COSHSHENV1"] = "variantex"
        r.render()
        r.output()
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue('environment variable COSHSHENV1 (variantex)' in os_windows_default_cfg)
        self.assertTrue('environment variable COSHSHENV2 (die nr 2)' in os_windows_default_cfg)
        self.assertTrue('environment variante die nr 2' in os_windows_default_cfg)


