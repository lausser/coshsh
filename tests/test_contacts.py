import unittest
import os
import sys
import shutil
import string
from optparse import OptionParser
import ConfigParser
import logging
import pprint
from logging import INFO, DEBUG
from tempfile import gettempdir

sys.dont_write_bytecode = True

import coshsh
from coshsh.generator import Generator
from coshsh.datasource import Datasource
from coshsh.application import Application

class CoshshTest(unittest.TestCase):
    def print_header(self):
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def setUp(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read('etc/coshsh4.cfg')
        self.generator = coshsh.generator.Generator()
        self.generator.setup_logging()
        self.pp = pprint.PrettyPrinter(indent=4)
        if 'OMD_ROOT' in os.environ:
            self.log_dir = os.path.join(os.environ['OMD_ROOT'], "var", "coshsh")
        else:
            self.log_dir = gettempdir()


    def tearDown(self):
        pass

    def test_create_custom_contact(self):
        self.print_header()
        self.generator.add_recipe(name='test221', **dict(self.config.items('recipe_test221')))
        self.generator.add_recipe(name='test222', **dict(self.config.items('recipe_test222')))

        self.config.set("datasource_CSV22", "name", "csv22")
        cfg = self.config.items("datasource_CSV22")
        self.generator.recipes['test221'].add_datasource(**dict(cfg))
        self.generator.recipes['test222'].add_datasource(**dict(cfg))

        # read the datasources
        self.generator.setup_logging(logdir=self.log_dir, scrnloglevel=DEBUG)
        self.generator.recipes['test221'].collect()
        self.generator.recipes['test221'].assemble()

        self.generator.recipes['test221'].render()
        cwebw = self.generator.recipes['test221'].objects['contacts']['lausser+WEBREADWRITE++lausserg']
        cmail = self.generator.recipes['test221'].objects['contacts']['lausser+MAIL+gerhard.lausser@consol.de+lausserg']
        ctick = self.generator.recipes['test221'].objects['contacts']['lausser+MYTICKETTOOL+lausser@consolq+lausserg']
        utick = self.generator.recipes['test221'].objects['contacts']['lausser+UNKTICKETTOOL+lausser@consolq+lausserg']

        #self.pp.pprint(cwebw.__dict__)
        #self.pp.pprint(cmail.__dict__)
        #self.pp.pprint(ctick.__dict__)
        #self.pp.pprint(utick.__dict__)

        print self.generator.recipes['test221'].objects['contacts']

        self.assert_(cwebw.can_submit_commands == True)
        self.assert_(cwebw.service_notification_options == "n")
        self.assert_(cwebw.service_notification_commands == ["notify_by_nothing"])

        self.assert_(cmail.can_submit_commands == False)
        self.assert_(cmail.service_notification_options == "w,c,u,r,f")
        self.assert_(cmail.service_notification_commands == ["service-notify-by-email"])
        self.assert_(cmail.email == "gerhard.lausser@consol.de")

        self.assert_(ctick.__class__.__name__ == "ContactMyTicketTool")
        self.assert_(ctick.can_submit_commands == False)
        self.assert_(ctick.service_notification_options == "w,c")
        self.assert_(ctick.service_notification_commands == ["service-notify-by-msend"])
        self.assert_(ctick.queue_id == "lausser@consolq")

        self.assert_(utick.__class__.__name__ == "GenericContact")

        self.generator.recipes['test221'].output()
        self.assert_(os.path.exists("var/objects/test22/dynamic/hosts"))

    def test_create_bmc_contact(self):
        self.print_header()
        u_bmc = coshsh.contact.Contact({
            "type": "BMC", "name": "bmc", "userid": "bmc",
            "notification_period": "24x7",
            "service_notification_commands": ["notify-service-optis"],
            "host_notification_commands": ["notify-host-optis"],
            "host_notification_options": "d,u,r",
            "service_notification_options": "w,c,u,r,s",
        })
        self.assert_(u_bmc.__class__.__name__ == "GenericContact")
        self.assert_(u_bmc.can_submit_commands == False)
        self.assert_(u_bmc.service_notification_options == "w,c,u,r,s")
        self.assert_(u_bmc.host_notification_options == "d,u,r")
        self.assert_(u_bmc.service_notification_commands == ["notify-service-optis"])

if __name__ == '__main__':
    unittest.main()

