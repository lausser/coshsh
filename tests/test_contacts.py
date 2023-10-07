import os
import sys
import re
import coshsh
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):
    _configfile = 'etc/coshsh4.cfg'
    _objectsdir = "./var/objects/test1"

    def print_header(self):
        print("#" * 80 + "\n" + "#" + " " * 78 + "#")
        print("#" + str.center(self.id(), 78) + "#")
        print("#" + " " * 78 + "#\n" + "#" * 80 + "\n")

    def ssetUp(self):
        super(CoshshTest, self).setUp()
        if 'OMD_ROOT' in os.environ:
            self.log_dir = os.path.join(os.environ['OMD_ROOT'], "var", "coshsh")
        else:
            self.log_dir = gettempdir()


    def tearDowns(self):
        pass

    def test_create_custom_contact(self):
        self.setUpConfig("etc/coshsh4.cfg", "test221")
        # read the datasources
        self.generator.recipes['test221'].collect()
        self.generator.recipes['test221'].assemble()

        cwebw = self.generator.recipes['test221'].objects['contacts']['lausser+WEBREADWRITE++lausserg']
        cmail = self.generator.recipes['test221'].objects['contacts']['lausser+MAIL+gerhard.lausser@consol.de+lausserg']
        ctick = self.generator.recipes['test221'].objects['contacts']['lausser+MYTICKETTOOL+lausser@consolq+lausserg']
        ctick.custom_macros["ENVIRONMENT"] = "dev"
        utick = self.generator.recipes['test221'].objects['contacts']['lausser+UNKTICKETTOOL+lausser@consolq+lausserg']
        utick.custom_macros["ENVIRONMENT"] = "dev"
        self.generator.recipes['test221'].render()

        #self.pp.pprint(cwebw.__dict__)
        #self.pp.pprint(cmail.__dict__)
        #self.pp.pprint(ctick.__dict__)
        #self.pp.pprint(utick.__dict__)

        print(self.generator.recipes['test221'].objects['contacts'])

        self.assertTrue(cwebw.can_submit_commands == True)
        self.assertTrue(cwebw.service_notification_options == "n")
        self.assertTrue(cwebw.service_notification_commands == ["notify_by_nothing"])

        self.assertTrue(cmail.can_submit_commands == False)
        self.assertTrue(cmail.service_notification_options == "w,c,u,r,f")
        self.assertTrue(cmail.service_notification_commands == ["service-notify-by-email"])
        self.assertTrue(cmail.email == "gerhard.lausser@consol.de")

        self.assertTrue(ctick.__class__.__name__ == "ContactMyTicketTool")
        self.assertTrue(ctick.can_submit_commands == False)
        self.assertTrue(ctick.service_notification_options == "w,c")
        self.assertTrue(ctick.service_notification_commands == ["service-notify-by-msend"])
        self.assertTrue(ctick.queue_id == "lausser@consolq")
        self.assertTrue("ENVIRONMENT" in ctick.config_files['nagios']['contact_lausserg.cfg'])

        self.assertTrue(utick.__class__.__name__ == "GenericContact")

        self.generator.recipes['test221'].output()
        self.assertTrue(os.path.exists("var/objects/test22/dynamic/hosts"))

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
        self.assertTrue(u_bmc.__class__.__name__ == "GenericContact")
        self.assertTrue(u_bmc.can_submit_commands == False)
        self.assertTrue(u_bmc.service_notification_options == "w,c,u,r,s")
        self.assertTrue(u_bmc.host_notification_options == "d,u,r")
        self.assertTrue(u_bmc.service_notification_commands == ["notify-service-optis"])

    def test_create_custom_contacts(self):
        self.setUpConfig("etc/coshsh4.cfg", "test221")
        # read the datasources
        self.generator.recipes['test221'].collect()
        self.generator.recipes['test221'].assemble()
        # benutzt eigenes tpl
        cexitp1 = self.generator.recipes['test221'].objects['contacts']['lausser+EXISTINGTEMPLATE+localit@wattens.swar.at+localit']
        cexitp1.templates = ["localit_inc5", "bereitschaft"]
        # benutzt standard contact.tpl
        cexitp2 = self.generator.recipes['test221'].objects['contacts']['lausser+EXISTINGTEMPLATE2+localit2@wattens.swar.at+localit2']
        cexitp2.templates = ["localit_inc3", "bereitschaft"]
        self.generator.recipes['test221'].render()
        print("DEBUG"+str(cexitp1.config_files["nagios"].keys()))
        print("DEBUG"+cexitp1.config_files["nagios"]["contact_localit.cfg"])
        self.assertTrue(re.search(r'define.*use\s+localit_inc5,bereitschaft', cexitp1.config_files["nagios"]["contact_localit.cfg"], re.DOTALL))
        #print(cexitp2.config_files["nagios"]["contact_localit2.cfg"])
        self.assertTrue(re.search(r'define.*use\s+localit_inc3,bereitschaft', cexitp2.config_files["nagios"]["contact_localit2.cfg"], re.DOTALL))


