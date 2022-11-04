import os
import io
import shutil
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def test_recipe_max_deltas_default(self):
        self.setUpConfig("etc/coshsh.cfg", "test10")
        r = self.generator.get_recipe("test10")
        self.assertTrue(r.max_delta == ())

    def test_recipe_max_deltas_simple(self):
        self.setUpConfig("etc/coshsh.cfg", "test10")
        recipe = {'classes_dir': '/tmp', 'objects_dir': '/tmp', 'templates_dir': '/tmp', 'datasources': 'datasource', 'max_delta': '101' }
        self.generator.add_recipe(name='recp', **recipe)
        self.assertTrue(self.generator.get_recipe('recp').max_delta == (101, 101))

    def test_recipe_max_deltas_double(self):
        self.setUpConfig("etc/coshsh.cfg", "test10")
        recipe = {'classes_dir': '/tmp', 'objects_dir': '/tmp', 'templates_dir': '/tmp', 'datasources': 'datasource', 'max_delta': '101:202' }
        self.generator.add_recipe(name='recp', **recipe)
        self.assertTrue(self.generator.get_recipe('recp').max_delta == (101, 202))

    def test_create_recipe_multiple_sources(self):
        self.setUpConfig("etc/coshsh.cfg", "test10")
        r = self.generator.get_recipe("test10")
        # remove target dir / create empty
        r.count_before_objects()
        r.cleanup_target_dir()
        r.prepare_target_dir()
        # read the datasources
        r.collect()
        r.assemble()
        r.render()
        self.assertTrue(hasattr(self.generator.recipes['test10'].objects['hosts']['test_host_0'], 'config_files'))
        self.assertTrue('host.cfg' in self.generator.recipes['test10'].objects['hosts']['test_host_0'].config_files['nagios'])

        # write hosts/apps to the filesystem
        r.output()
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg"))
        with io.open("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue('os_windows_default_check_' in os_windows_default_cfg)
        self.assertTrue(len(self.generator.recipes['test10'].objects['applications']['test_host_1+os+windows2k8r2'].filesystems) == 5)
        # must be sorted
        self.assertTrue([f.path for f in self.generator.recipes['test10'].objects['applications']['test_host_1+os+windows2k8r2'].filesystems] == ['C', 'D', 'F', 'G', 'Z'])
        # git_init is yes by default
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/.git"))

        # three mysql objects and three app_db_mysql... files. (in a later test
        # these will not exist because of render exceptions)
        self.assertTrue(len([app for app in self.generator.recipes['test10'].objects['applications'].values() if "mysql" in app.__class__.__name__.lower()]) == 3)
        mysql_files = []
        for mysql in [app for app in r.objects['applications'].values() if "mysql" in app.__class__.__name__.lower()]:
            mysql_files.extend([mysql.host_name+"/"+cfg for cfg in mysql.config_files["nagios"].keys()])
        self.assertTrue(len(mysql_files) == 3)
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/test_host_0/app_db_mysql_intranet_default.cfg"))
        for cfg in mysql_files:
            self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/"+cfg))
        self.assertTrue(self.generator.recipes['test10'].render_errors == 0)

    def test_create_recipe_multiple_sources_no_git(self):
        self.setUpConfig("etc/coshsh.cfg", "test10nogit")
        r = self.generator.get_recipe("test10nogit")
        self.assertFalse(r.git_init)
        self.generator.run()
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg"))
        # git_init is yes by default, but here explicitely no
        self.assertTrue(not os.path.exists("var/objects/test10/dynamic/.git"))

    def test_create_recipe_set_env(self):
        os.environ['OMD_SITE'] = 'sitexy'
        os.environ['COSHSHDIR'] = '/opt/coshsh'
        os.environ['ZISSSSSSCHDIR'] = '/opt/zisch'
        self.setUpConfig("etc/coshsh.cfg", "test7inv")
        r = self.generator.get_recipe("test7inv")
        ds = r.get_datasource("test7inv")
        self.assertTrue(os.environ["THERCP"] == "test7inv_xyz")
        self.assertTrue(os.environ["THECDIR"] == "/opt/coshsh/i_am_the_dir")
        self.assertTrue(os.environ["THEZDIR"] == "/opt/zisch/i_am_the_dir")
        self.assertTrue(os.environ["MIBDIRS"] == "/usr/share/snmp/mibs:/omd/sites/sitexy/etc/coshsh/data/mibs")
        # remove target dir / create empty

    def test_create_recipe_template_error(self):
        self.setUpConfig("etc/coshsh.cfg", "test10tplerr")
        r = self.generator.get_recipe("test10tplerr")
        # remove target dir / create empty
        r.count_before_objects()
        r.cleanup_target_dir()
        r.prepare_target_dir()
        # read the datasources
        r.collect()
        r.assemble()
        r.render()
        self.assertTrue(hasattr(r.objects['hosts']['test_host_0'], 'config_files'))
        self.assertTrue('host.cfg' in r.objects['hosts']['test_host_0'].config_files['nagios'])

        # we have three mysql applications
        self.assertTrue(len([app for app in r.objects['applications'].values() if "mysql" in app.__class__.__name__.lower()]) == 3)

        r.output()
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg"))
        with io.open("var/objects/test10/dynamic/hosts/test_host_1/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue('os_windows_default_check_' in os_windows_default_cfg)
        self.assertTrue(len(r.objects['applications']['test_host_1+os+windows2k8r2'].filesystems) == 5)
        # must be sorted
        self.assertTrue([f.path for f in r.objects['applications']['test_host_1+os+windows2k8r2'].filesystems] == ['C', 'D', 'F', 'G', 'Z'])
        # git_init is yes by default
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/.git"))

        self.assertTrue(len([app for app in r.objects['applications'].values() if "mysql" in app.__class__.__name__.lower()]) == 3)
        mysql_files = []
        for mysql in [app for app in r.objects['applications'].values() if "mysql" in app.__class__.__name__.lower()]:
            print(mysql.__dict__)
            self.assertTrue("nagios" not in mysql.config_files)
        self.assertFalse(os.path.exists("var/objects/test10/dynamic/hosts/test_host_0/app_db_mysql_intranet_default.cfg"))
        self.assertTrue(r.render_errors == 3)

