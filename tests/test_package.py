"""Tests for Host, Application, Contact, and HostGroup object creation and default attribute values."""

import coshsh
from tests.common_coshsh_test import CommonCoshshTest


class PackageTest(CommonCoshshTest):

    def test_read_config(self):
        """Recipe configuration is parsed without error."""
        self.setUpConfig("etc/coshsh.cfg", "test1")

    def test_create_hostgroup(self):
        """HostGroup initialises with an empty members list."""
        hostgroup = coshsh.hostgroup.HostGroup()
        self.assertEqual(hostgroup.members, [])

    def test_create_contactgroup(self):
        """ContactGroup initialises with an empty members list."""
        contactgroup = coshsh.contactgroup.ContactGroup()
        self.assertEqual(contactgroup.members, [])

    def test_create_contact(self):
        """Contact class factory selects the correct subclass after cookbook is loaded."""
        contact = coshsh.contact.Contact({"type": "WEBREADONLY", "name": "sepp", "userid": "test", "notification_period": "5x8"})
        self.assertEqual(contact.contact_name, "unknown_WEBREADONLY_sepp_5x8")
        # Now read a config.
        # This is needed in order to run init_item_class_factories
        # Otherwise contact would still be a GenericContact
        self.setUpConfig("etc/coshsh.cfg", "test1")
        contact = coshsh.contact.Contact({"type": "WEBREADONLY", "name": "sepp", "userid": "test", "notification_period": "5x8"})
        # WEB* contacts are simply named after the userid
        self.assertEqual(contact.contact_name, "test")
        self.assertEqual(contact.host_notification_period, "5x8")

    def test_create_host(self):
        """Host initialises with default hostgroups, ports, and alias derived from host_name."""
        host = coshsh.host.Host({"host_name": "test"})
        self.assertEqual(host.hostgroups, [])
        self.assertEqual(host.ports, [22])
        self.assertEqual(host.alias, "test")

    def test_create_application_default_class(self):
        """Application created before class factory init is GenericApplication with empty contact_groups."""
        application = coshsh.application.Application({"host_name": "test", "name": "shop", "type": "apache"})
        self.assertEqual(application.contact_groups, [])
        self.assertEqual(application.__class__.__name__, "GenericApplication")

    def test_application_lower_columns_normalised(self):
        """Application name and type are lowered on init."""
        application = coshsh.application.Application({"host_name": "TEST", "name": "Shop", "type": "Apache"})
        self.assertEqual(application.name, "shop")
        self.assertEqual(application.type, "apache")

    def test_create_application(self):
        """Application has empty contact_groups list."""
        application = coshsh.application.Application({"host_name": "test", "name": "shop", "type": "apache"})
        self.assertEqual(application.contact_groups, [])
