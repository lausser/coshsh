import unittest
import os
import sys
import shutil
import string
from optparse import OptionParser
import ConfigParser
import logging

print "sys.path", sys.path
import coshsh
from coshsh.contact import Contact
from coshsh.contactgroup import ContactGroup
from coshsh.host import Host
from coshsh.application import Application
from coshsh.hostgroup import HostGroup
from coshsh.generator import Generator

sys.dont_write_bytecode = True

class CoshshTest(unittest.TestCase):
    def print_header(self):
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def setUp(self):
        shutil.rmtree("./var/objects/test1", True)
        os.makedirs("./var/objects/test1")
        self.config = ConfigParser.ConfigParser()
        self.config.read('etc/coshsh.cfg')

    def tearDown(self):
        #shutil.rmtree("./var/objects/test1", True)
        print

    def test_read_config(self):
        self.print_header()
        self.config = ConfigParser.ConfigParser()
        self.config.read('etc/coshsh.cfg')

    def test_create_generator(self):
        self.print_header()
        self.generator = coshsh.generator.Generator()
        self.generator.setup_logging(scrnloglevel=logging.DEBUG)

    def xtest_create_generator_by_coshsh(self):
        self.print_header()
        self.generator = coshsh.Generator()
        self.generator.setup_logging(scrnloglevel=logging.DEBUG)

    def test_create_hostgroup(self):
        self.print_header()
        self.hostgroup = coshsh.hostgroup.HostGroup()
        self.assert_(self.hostgroup.members == [])

    def test_create_contactgroup(self):
        self.print_header()
        self.contactgroup = coshsh.contactgroup.ContactGroup()
        self.assert_(self.contactgroup.members == [])

    def test_create_contact(self):
        self.print_header()
        self.contact = coshsh.contact.Contact({"type": "WEBREADONLY", "name": "sepp", "userid": "test", "notification_period": "5x8"})
        # the name is unknown... because we didn't init the class factory
        # so it becomes a generic contact
        print self.contact.__dict__
        self.assert_(self.contact.contact_name == "unknown_WEBREADONLY_sepp_5x8")
        self.assert_(self.contact.host_notification_period == "5x8")

    def test_create_host(self):
        self.print_header()
        self.host = coshsh.host.Host({"host_name": "test"})
        self.assert_(self.host.hostgroups == [])
        self.assert_(self.host.ports == [22])
        self.assert_(self.host.alias == "test")

    def test_create_application(self):
        self.print_header()
        self.application = coshsh.application.Application({"host_name": "test", "name": "shop", "type": "apache"})
        self.assert_(self.application.contact_groups == [])
        self.assert_(self.application.__class__.__name__ == "GenericApplication")

    def test_create_application(self):
        self.print_header()
        self.application = coshsh.application.Application({"host_name": "test", "name": "shop", "type": "apache"})
        self.assert_(self.application.contact_groups == [])
        print self.application.fingerprint()
        print self.application.__class__.__name__

if __name__ == '__main__':
    unittest.main()

