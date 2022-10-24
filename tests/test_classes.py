import os
import io
import coshsh
from tests.common_coshsh_test import CommonCoshshTest


class CoshshTest(CommonCoshshTest):

    def test_create_recipe_check_paths(self):
        self.setUpConfig("etc/coshsh.cfg", "test4,test5")
        r_test4 = self.generator.get_recipe("test4")
        self.assertTrue(os.path.abspath(r_test4.classes_path[0]) == os.path.abspath('./recipes/test4/classes'))
        self.assertTrue(os.path.abspath(r_test4.templates_path[0]) == os.path.abspath('recipes/test4/templates'))
        self.assertTrue(os.path.abspath(r_test4.jinja2.loader.searchpath[0]) == os.path.abspath('recipes/test4/templates'))
        r_test5 = self.generator.get_recipe("test5")
        self.assertTrue(os.path.abspath(r_test5.classes_path[0]) == os.path.abspath('./recipes/test5/classes'))
        self.assertTrue(os.path.abspath(r_test5.templates_path[0]) == os.path.abspath('./recipes/test5/templates'))
        self.assertTrue(os.path.abspath(r_test5.jinja2.loader.searchpath[0]) == os.path.abspath('./recipes/test5/templates'))
        # did the jinja2 object get the self-written filters?
        self.assertTrue('re_match' in r_test5.jinja2.env.tests)
        self.assertTrue('service' in r_test5.jinja2.env.filters)

    def test_create_recipe_check_factories(self):
        self.setUpConfig("etc/coshsh.cfg", "test4")
        ds = self.generator.get_recipe("test4").get_datasource("simplesample")
        self.assertTrue(hasattr(ds, 'only_the_test_simplesample'))

        self.generator.cookbook.set("datasource_CSVSAMPLE", "name", "csvsample")
        csvsample = self.generator.cookbook.items("datasource_CSVSAMPLE")
        ds = coshsh.datasource.Datasource(**dict(csvsample))
        self.assertTrue(ds.dir == "./recipes/test1/data")

    def test_create_recipe_check_factories_env(self):
        os.environ['COSHSHDIR'] = '/opt/coshsh'
        os.environ['ZISSSSSSCHDIR'] = '/opt/zisch'
        self.setUpConfig("etc/coshsh.cfg", "test7")
        r_test7 = self.generator.get_recipe("test7")
        ds = self.generator.get_recipe("test7").get_datasource("envdirds")
        self.assertTrue(ds.dir == "/opt/coshsh/recipes/test7/data")
        self.assertTrue(r_test7.classes_path[0:2] == ['/opt/coshsh/recipes/test7/classes', '/opt/zisch/tmp'])

    def test_create_recipe_check_factories_read(self):
        self.setUpConfig("etc/coshsh.cfg", "test4")
        r_test4 = self.generator.get_recipe("test4")
        self.generator.cookbook.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.generator.cookbook.items("datasource_SIMPLESAMPLE")
        ds = coshsh.datasource.Datasource(**dict(cfg))
        self.assertTrue(hasattr(ds, 'only_the_test_simplesample'))
        objects = r_test4.objects
        ds.read(objects=objects)
        self.assertTrue(objects['hosts']['test_host_0'].my_host == True)
        self.assertTrue(list(objects['applications'].values())[0].test4_linux == True)
        self.assertTrue(list(objects['applications'].values())[1].test4_windows == True)


    def test_create_recipe_check_3factories_read(self):
        self.setUpConfig("etc/coshsh.cfg", "test4a")
        self.generator.cookbook.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.generator.cookbook.items("datasource_SIMPLESAMPLE")
        ds = coshsh.datasource.Datasource(**dict(cfg))
        self.assertTrue(hasattr(ds, 'only_the_test_simplesample'))
        objects = self.generator.recipes['test4a'].objects
        ds.read(objects=objects)
        self.assertTrue(objects['hosts']['test_host_0'].my_host == True)
        self.assertTrue(objects['applications']['test_host_0+os+windows'].test4_windows == True)
        self.assertTrue(objects['applications']['test_host_0+os+red hat'].mycorp_linux == True)

    def test_create_recipe_check_factories_write(self):
        self.setUpConfig("etc/coshsh.cfg", "test4")
        r_test4 = self.generator.get_recipe("test4")
        self.generator.cookbook.set("datasource_SIMPLESAMPLE", "name", "simplesample")
        cfg = self.generator.cookbook.items("datasource_SIMPLESAMPLE")
        r_test4.add_datasource(**dict(cfg))

        # remove target dir / create empty
        r_test4.count_before_objects()
        r_test4.cleanup_target_dir()

        r_test4.prepare_target_dir()
        # check target

        # read the datasources
        r_test4.collect()
        r_test4.assemble()

        # for each host, application get the corresponding template files
        # get the template files and cache them in a struct owned by the recipe
        # resolve the templates and attach the result as config_files to host/app
        r_test4.render()
        self.assertTrue(hasattr(r_test4.objects['hosts']['test_host_0'], 'config_files'))
        self.assertTrue('host.cfg' in r_test4.objects['hosts']['test_host_0'].config_files['nagios'])

        # write hosts/apps to the filesystem
        r_test4.output()
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg"))
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue('os_windows_default_check_unittest' in os_windows_default_cfg)
        # weil os_windows_kaas knallt wg jinja neighbor_applications_as_tuple
        self.assertTrue(r_test4.render_errors == 1)


    def test_create_recipe_check_factories_write2(self):
        self.setUpConfig("etc/coshsh.cfg", "test4b")
        r_test4 = self.generator.get_recipe("test4b")
        self.generator.cookbook.set("datasource_SIMPLESAMPLE", "name", "simplesample")

        # remove target dir / create empty
        r_test4.count_before_objects()
        r_test4.cleanup_target_dir()

        r_test4.prepare_target_dir()
        # check target

        # read the datasources
        r_test4.collect()
        r_test4.assemble()
        
        # for each host, application get the corresponding template files
        # get the template files and cache them in a struct owned by the recipe
        # resolve the templates and attach the result as config_files to host/app
        r_test4.render()
        self.assertTrue(hasattr(r_test4.objects['hosts']['test_host_0'], 'config_files'))
        self.assertTrue('host.cfg' in r_test4.objects['hosts']['test_host_0'].config_files["nagios"])

        # write hosts/apps to the filesystem
        r_test4.output()
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_linux_default.cfg"))
        self.assertTrue(os.path.exists("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg"))
        with io.open("var/objects/test1/dynamic/hosts/test_host_0/os_windows_default.cfg") as f:
            os_windows_default_cfg = f.read()
        self.assertTrue('os_windows_default_check_unittest' in os_windows_default_cfg)

    def test_ds_handshake(self):
        self.setUpConfig("etc/coshsh.cfg", "test8")
        r_test8 = self.generator.get_recipe("test8")
        ds = self.generator.get_recipe("test8").get_datasource("handsh")
        try:
            hosts, applications, contacts, contactgroups, appdetails, dependencies, bps = ds.read()
        except Exception as exp:
            self.assertTrue(exp.__class__.__name__ == "DatasourceNotCurrent")
        else:
            fail("datasource did not raise DatasourceNotCurrent")
        coll_success = r_test8.collect()
        self.assertTrue(coll_success == False)
        r_test8.assemble()



if __name__ == '__main__':
    unittest.main()


