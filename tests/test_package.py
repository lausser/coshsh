import coshsh
from tests.common_coshsh_test import CommonCoshshTest

class CoshshTest(CommonCoshshTest):

    def test_read_config(self):
        self.setUpConfig("etc/coshsh.cfg", "test1")

    def test_create_hostgroup(self):
        hostgroup = coshsh.hostgroup.HostGroup()
        self.assertTrue(hostgroup.members == [])

    def test_create_contactgroup(self):
        contactgroup = coshsh.contactgroup.ContactGroup()
        self.assertTrue(contactgroup.members == [])

    def test_create_contact(self):
        contact = coshsh.contact.Contact({"type": "WEBREADONLY", "name": "sepp", "userid": "test", "notification_period": "5x8"})
        print("COCOCOCOC "+contact.contact_name)
        self.assertTrue(contact.contact_name == "unknown_WEBREADONLY_sepp_5x8")
        # Now read a config.
        # This is needed in order to run init_item_class_factories
        # Otherwise contact would still be a GenericContact
        self.setUpConfig("etc/coshsh.cfg", "test1")
        contact = coshsh.contact.Contact({"type": "WEBREADONLY", "name": "sepp", "userid": "test", "notification_period": "5x8"})
        # WEB* contacts are simply named after the userid
        self.assertTrue(contact.contact_name == "test")
        self.assertTrue(contact.host_notification_period == "5x8")

    def test_create_host(self):
        host = coshsh.host.Host({"host_name": "test"})
        self.assertTrue(host.hostgroups == [])
        self.assertTrue(host.ports == [22])
        self.assertTrue(host.alias == "test")

    def test_create_application(self):
        application = coshsh.application.Application({"host_name": "test", "name": "shop", "type": "apache"})
        self.assertTrue(application.contact_groups == [])
        self.assertTrue(application.__class__.__name__ == "GenericApplication")

    def test_create_application(self):
        application = coshsh.application.Application({"host_name": "test", "name": "shop", "type": "apache"})
        self.assertTrue(application.contact_groups == [])


