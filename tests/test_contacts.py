"""Tests for Contact class factory selection and contact_name attribute derivation."""

import os
import re
import coshsh
from tests.common_coshsh_test import CommonCoshshTest


class ContactsTest(CommonCoshshTest):
    _configfile = "etc/coshsh4.cfg"
    _objectsdir = "./var/objects/test1"

    def test_create_custom_contact(self):
        """Verify class factory selects the correct Contact subclass and sets notification attributes for each contact type."""
        self.setUpConfig("etc/coshsh4.cfg", "test221")
        self.generator.recipes["test221"].collect()
        self.generator.recipes["test221"].assemble()

        cwebw = self.generator.recipes["test221"].objects["contacts"]["lausser+WEBREADWRITE++lausserg"]
        cmail = self.generator.recipes["test221"].objects["contacts"]["lausser+MAIL+gerhard.lausser@consol.de+lausserg"]
        ctick = self.generator.recipes["test221"].objects["contacts"]["lausser+MYTICKETTOOL+lausser@consolq+lausserg"]
        ctick.custom_macros["ENVIRONMENT"] = "dev"
        utick = self.generator.recipes["test221"].objects["contacts"]["lausser+UNKTICKETTOOL+lausser@consolq+lausserg"]
        utick.custom_macros["ENVIRONMENT"] = "dev"
        self.generator.recipes["test221"].render()

        self.assertEqual(cwebw.can_submit_commands, True)
        self.assertEqual(cwebw.service_notification_options, "n")
        self.assertEqual(cwebw.service_notification_commands, ["notify_by_nothing"])

        self.assertEqual(cmail.can_submit_commands, False)
        self.assertEqual(cmail.service_notification_options, "w,c,u,r,f")
        self.assertEqual(cmail.service_notification_commands, ["service-notify-by-email"])
        self.assertEqual(cmail.email, "gerhard.lausser@consol.de")

        self.assertEqual(ctick.__class__.__name__, "ContactMyTicketTool")
        self.assertEqual(ctick.can_submit_commands, False)
        self.assertEqual(ctick.service_notification_options, "w,c")
        self.assertEqual(ctick.service_notification_commands, ["service-notify-by-msend"])
        self.assertEqual(ctick.queue_id, "lausser@consolq")
        self.assertIn("ENVIRONMENT", ctick.config_files["nagios"]["contact_lausserg.cfg"])

        self.assertEqual(utick.__class__.__name__, "GenericContact")

        self.generator.recipes["test221"].output()
        self.assertTrue(os.path.exists("var/objects/test22/dynamic/hosts"))

    def test_create_bmc_contact(self):
        """Verify that a BMC-type contact falls back to GenericContact with the given notification settings intact."""
        u_bmc = coshsh.contact.Contact({
            "type": "BMC", "name": "bmc", "userid": "bmc",
            "notification_period": "24x7",
            "service_notification_commands": ["notify-service-optis"],
            "host_notification_commands": ["notify-host-optis"],
            "host_notification_options": "d,u,r",
            "service_notification_options": "w,c,u,r,s",
        })
        self.assertEqual(u_bmc.__class__.__name__, "GenericContact")
        self.assertEqual(u_bmc.can_submit_commands, False)
        self.assertEqual(u_bmc.service_notification_options, "w,c,u,r,s")
        self.assertEqual(u_bmc.host_notification_options, "d,u,r")
        self.assertEqual(u_bmc.service_notification_commands, ["notify-service-optis"])

    def test_create_custom_contacts(self):
        """Verify that contacts with existing Nagios templates render the correct use directive in their config files."""
        self.setUpConfig("etc/coshsh4.cfg", "test221")
        self.generator.recipes["test221"].collect()
        self.generator.recipes["test221"].assemble()
        # uses its own tpl
        cexitp1 = self.generator.recipes["test221"].objects["contacts"]["lausser+EXISTINGTEMPLATE+localit@wattens.swar.at+localit"]
        cexitp1.templates = ["localit_inc5", "bereitschaft"]
        # uses standard contact.tpl
        cexitp2 = self.generator.recipes["test221"].objects["contacts"]["lausser+EXISTINGTEMPLATE2+localit2@wattens.swar.at+localit2"]
        cexitp2.templates = ["localit_inc3", "bereitschaft"]
        self.generator.recipes["test221"].render()
        self.assertTrue(re.search(r"define.*use\s+localit_inc5,bereitschaft", cexitp1.config_files["nagios"]["contact_localit.cfg"], re.DOTALL))
        self.assertTrue(re.search(r"define.*use\s+localit_inc3,bereitschaft", cexitp2.config_files["nagios"]["contact_localit2.cfg"], re.DOTALL))
