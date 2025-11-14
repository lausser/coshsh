"""Test suite for core coshsh object creation and initialization.

This module tests the basic functionality of creating core coshsh objects
like hosts, applications, contacts, hostgroups, and contactgroups, verifying
default values and class factories.
"""

from __future__ import annotations

import coshsh
from tests.common_coshsh_test import CommonCoshshTest


class CoreObjectsTest(CommonCoshshTest):
    """Test suite for core coshsh object creation.

    This suite verifies that:
    - Configuration files can be read successfully
    - Core objects (Host, Application, Contact, etc.) can be instantiated
    - Default values are correctly assigned
    - Class factories work correctly (GenericContact vs specific types)
    - Contact name generation follows naming conventions

    Core Objects Tested:
        - HostGroup: Container for host members
        - ContactGroup: Container for contact members
        - Contact: Notification contacts with type-specific behavior
        - Host: Monitored hosts with default attributes
        - Application: Services/applications on hosts

    Test Configuration:
        Uses config file: etc/coshsh.cfg
        Recipe: test1
    """

    def test_config_file_loads_successfully(self) -> None:
        """Test that configuration file can be loaded.

        This is a basic sanity check that the test configuration
        file is valid and can be parsed by coshsh.

        Expected Behavior:
            setUpConfig should complete without raising exceptions.
        """
        # Act & Assert: Load config (should not raise)
        self.setUpConfig("etc/coshsh.cfg", "test1")

    def test_hostgroup_creates_with_empty_members(self) -> None:
        """Test that HostGroup creates with empty members list.

        Verifies default initialization of HostGroup objects.
        A new hostgroup should start with no members.

        Expected Behavior:
            HostGroup.members is an empty list.

        Assertions:
            - members attribute is an empty list
        """
        # Act: Create a hostgroup
        hostgroup = coshsh.hostgroup.HostGroup()

        # Assert: Verify default members list
        self.assertEqual(
            hostgroup.members,
            [],
            "New hostgroup should have empty members list"
        )

    def test_contactgroup_creates_with_empty_members(self) -> None:
        """Test that ContactGroup creates with empty members list.

        Verifies default initialization of ContactGroup objects.
        A new contactgroup should start with no members.

        Expected Behavior:
            ContactGroup.members is an empty list.

        Assertions:
            - members attribute is an empty list
        """
        # Act: Create a contactgroup
        contactgroup = coshsh.contactgroup.ContactGroup()

        # Assert: Verify default members list
        self.assertEqual(
            contactgroup.members,
            [],
            "New contactgroup should have empty members list"
        )

    def test_contact_naming_conventions_with_and_without_class_factory(self) -> None:
        """Test contact naming conventions with generic and specific contact types.

        This test verifies that:
        1. Before class factories are initialized, contacts use generic naming
        2. After class factories are initialized, type-specific naming is used
        3. WEB* contacts use simplified naming (just userid)
        4. Notification periods are correctly assigned

        Contact Naming Rules:
            - Generic: unknown_<TYPE>_<name>_<notification_period>
            - WEBREADONLY: <userid> (simplified)

        Test Scenario:
            Create WEBREADONLY contact before and after loading config
            to verify class factory behavior.

        Expected Behavior:
            Before config: contact_name = "unknown_WEBREADONLY_sepp_5x8"
            After config: contact_name = "test" (userid-based)

        Assertions:
            - Generic naming format before class factories
            - Type-specific naming after class factories
            - Notification period is correctly set
        """
        # Act: Create contact before loading config (no class factories)
        contact = coshsh.contact.Contact({
            "type": "WEBREADONLY",
            "name": "sepp",
            "userid": "test",
            "notification_period": "5x8"
        })

        # Assert: Generic contact uses full naming convention
        print("COCOCOCOC " + contact.contact_name)
        self.assertEqual(
            contact.contact_name,
            "unknown_WEBREADONLY_sepp_5x8",
            "Generic contact should use full naming format before class factories"
        )

        # Arrange: Load config to initialize class factories
        self.setUpConfig("etc/coshsh.cfg", "test1")

        # Act: Create contact after loading config (with class factories)
        contact = coshsh.contact.Contact({
            "type": "WEBREADONLY",
            "name": "sepp",
            "userid": "test",
            "notification_period": "5x8"
        })

        # Assert: WEBREADONLY contacts use userid-based naming
        self.assertEqual(
            contact.contact_name,
            "test",
            "WEBREADONLY contact should be named after userid"
        )
        self.assertEqual(
            contact.host_notification_period,
            "5x8",
            "Contact should have correct notification period"
        )

    def test_host_creates_with_default_attributes(self) -> None:
        """Test that Host creates with correct default attributes.

        Verifies that Host objects are initialized with expected default
        values for hostgroups, ports, and alias.

        Default Values:
            - hostgroups: [] (empty list)
            - ports: [22] (SSH port)
            - alias: same as host_name if not specified

        Expected Behavior:
            Host object has correct default values.

        Assertions:
            - hostgroups is empty list
            - ports includes default SSH port (22)
            - alias equals host_name when not specified
        """
        # Act: Create a host
        host = coshsh.host.Host({"host_name": "test"})

        # Assert: Verify default attributes
        self.assertEqual(
            host.hostgroups,
            [],
            "New host should have empty hostgroups list"
        )
        self.assertEqual(
            host.ports,
            [22],
            "New host should have default SSH port (22)"
        )
        self.assertEqual(
            host.alias,
            "test",
            "Host alias should default to host_name"
        )

    def test_application_creates_as_generic_application(self) -> None:
        """Test that Application creates as GenericApplication for unknown types.

        Verifies that applications with unknown types fall back to
        GenericApplication class, and have correct default attributes.

        This is important because not all application types have
        custom classes defined.

        Expected Behavior:
            - Application with unknown type becomes GenericApplication
            - contact_groups is empty list by default

        Assertions:
            - Application class is GenericApplication
            - contact_groups is empty list
        """
        # Act: Create application with unknown type
        application = coshsh.application.Application({
            "host_name": "test",
            "name": "shop",
            "type": "apache"
        })

        # Assert: Verify generic application attributes
        self.assertEqual(
            application.contact_groups,
            [],
            "New application should have empty contact_groups list"
        )
        self.assertEqual(
            application.__class__.__name__,
            "GenericApplication",
            "Unknown application type should become GenericApplication"
        )


