import os
import shutil
import io
from coshsh.host import Host
from coshsh.application import Application, GenericApplication
from coshsh.monitoringdetail import MonitoringDetail
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def setUpLogfile(self):
        super(CoshshTest, self).setUp()
        if "defaults" in self.config.sections() and "log_dir" in [c[0] for c in self.config.items("defaults")]:
            log_dir = dict(self.config.items("defaults"))["log_dir"]
            log_dir = re.sub('%.*?%', coshsh.util.substenv, log_dir)
        elif 'OMD_ROOT' in os.environ:
            log_dir = os.path.join(os.environ['OMD_ROOT'], "var", "coshsh")
        else:
            log_dir = gettempdir()
        setup_logging(logdir=log_dir, scrnloglevel=logging.DEBUG)

    def test_generic_app(self):
        self.setUpConfig("etc/coshsh5.cfg", "test33")
        r = self.generator.get_recipe("test33")
        r.update_item_class_factories()
        ds = self.generator.get_recipe("test33").get_datasource("simplesample")
        ds.objects = r.objects

        # init-meldungen von test33
        self.assertTrue(os.path.exists("./var/log/coshshlogs/coshsh_test33.log"))
        # aber auch vom generator
        # eigentlich. aber der generator loggt nur fehler
	# self.assertTrue(os.path.exists("./var/log/coshshlogs/coshsh.log"))
        host = Host({
            'host_name': 'testhost',
            'address': '127.0.0.1',
        })
        ds.add('hosts', host)
        app = Application({
            'host_name': 'testhost',
            'name': 'noname',
            'type': 'arschknarsch',
        })
        self.generator.recipes['test33'].datasources[0].add('applications', app)
        self.generator.recipes['test33'].collect()
        self.generator.recipes['test33'].assemble()
        self.generator.recipes['test33'].render()
        self.assertTrue(len(self.generator.recipes['test33'].objects['applications']) == 1)
        self.assertTrue(list(self.generator.recipes['test33'].datasources[0].getall('applications'))[0] == app)
        self.assertTrue(list(self.generator.recipes['test33'].datasources[0].getall('applications'))[0].__class__ == GenericApplication)
        self.generator.recipes['test33'].output()
        self.assertTrue(os.path.exists("var/objects/test33/dynamic/hosts/testhost/host.cfg"))
        self.assertTrue(not os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_fs.cfg"))
        self.assertTrue(not os.path.exists("var/objects/test33/dynamic/hosts/testhost/app_my_generic_ports.cfg"))


    def test_everything_default(self):
        self.setUpConfig("etc/coshsh5.cfg", "test35")
        self.assertTrue(os.path.exists("./var/log/coshshlogs/coshsh.log"))

    def test_extra_dir(self):
        self.setUpConfig("etc/coshsh5.cfg", "test36")
        # init-meldungen von test36
        self.assertTrue(os.path.exists("/tmp/coshsh5/coshsh.log"))
        # siehe oben
        # self.assertTrue(os.path.exists("./var/log/coshshlogs/coshsh.log"))

