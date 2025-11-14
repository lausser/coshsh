"""Test suite for contact creation and contact plugin functionality.

This module tests the creation and behavior of contact objects in coshsh,
including custom contact types, contact templates, and notification settings.
"""

from __future__ import annotations

import os
import re

import coshsh
from tests.common_coshsh_test import CommonCoshshTest


class ContactCreationTest(CommonCoshshTest):
    """Test suite for contact object creation and custom contact plugins.

    This test suite verifies that:
    - Custom contact plugins are correctly loaded and instantiated
    - Contact notification options are properly configured
    - Contact notification commands are correctly assigned
    - Contact templates are properly applied
    - Different contact types (MAIL, WEBREADWRITE, ticket tools) work correctly

    Test Configuration:
        Uses test recipe in tests/recipes/test221/
        Config file: etc/coshsh4.cfg

    Contact Types Tested:
        - WEBREADWRITE: Web interface contacts with command submission rights
        - MAIL: Email notification contacts
        - MYTICKETTOOL: Custom ticket tool integration
        - UNKTICKETTOOL: Unknown/generic ticket tool handling
        - BMC: BMC Remedy integration
        - EXISTINGTEMPLATE: Contacts with custom templates
    """

    _configfile = 'etc/coshsh4.cfg'
    _objectsdir = "./var/objects/test1"

    def print_header(self) -> None:
        """Print test header with test ID."""
        print("#" * 80 + "\n" + "#" + " " * 78 + "#")
        print("#" + str.center(self.id(), 78) + "#")
        print("#" + " " * 78 + "#\n" + "#" * 80 + "\n")

    def ssetUp(self) -> None:
        """Set up test environment (currently disabled).

        Note: Method name 'ssetUp' suggests this is intentionally disabled.
        If enabled, would configure log directory based on OMD_ROOT.
        """
        super(ContactCreationTest, self).setUp()
        if 'OMD_ROOT' in os.environ:
            self.log_dir = os.path.join(os.environ['OMD_ROOT'], "var", "coshsh")
        else:
            self.log_dir = gettempdir()

    def tearDowns(self) -> None:
        """Tear down test environment (currently disabled).

        Note: Method name 'tearDowns' suggests this is intentionally disabled.
        """
        pass

    def test_create_custom_contact_types_with_different_notification_settings(self) -> None:
        """Test creation of multiple custom contact types with varying notification settings.

        This test verifies that different contact types are correctly instantiated
        with their specific notification options, commands, and custom properties.
        It covers WEBREADWRITE, MAIL, and custom ticket tool contacts.

        Setup:
            - Loads configuration for test221 recipe
            - Collects and assembles contact objects from datasources
            - Creates contacts with different notification types

        Expected Behavior:
            - WEBREADWRITE contacts can submit commands and have 'nothing' notifications
            - MAIL contacts cannot submit commands and use email notifications
            - Custom ticket tool contacts use msend notifications with queue_id
            - Unknown ticket tools fall back to GenericContact
            - Custom macros like ENVIRONMENT are properly rendered in config files

        Assertions:
            - Contact types are correctly identified
            - Notification options match contact type specifications
            - Notification commands are properly assigned
            - Custom attributes (email, queue_id) are set correctly
            - Config files contain expected custom macros
            - Output directory is created
        """
        # Arrange: Set up configuration and load contacts
        self.setUpConfig("etc/coshsh4.cfg", "test221")
        recipe = self.generator.recipes['test221']

        # Act: Collect and assemble contact objects
        recipe.collect()
        recipe.assemble()

        # Retrieve specific contact objects for testing
        contacts = recipe.objects['contacts']
        cwebw = contacts['lausser+WEBREADWRITE++lausserg']
        cmail = contacts['lausser+MAIL+gerhard.lausser@consol.de+lausserg']
        ctick = contacts['lausser+MYTICKETTOOL+lausser@consolq+lausserg']
        ctick.custom_macros["ENVIRONMENT"] = "dev"
        utick = contacts['lausser+UNKTICKETTOOL+lausser@consolq+lausserg']
        utick.custom_macros["ENVIRONMENT"] = "dev"

        # Render contact configuration files
        recipe.render()

        print(recipe.objects['contacts'])

        # Assert: Verify WEBREADWRITE contact properties
        self.assertTrue(
            cwebw.can_submit_commands == True,
            "WEBREADWRITE contact should have command submission enabled"
        )
        self.assertTrue(
            cwebw.service_notification_options == "n",
            "WEBREADWRITE contact should have notification options set to 'n' (none)"
        )
        self.assertTrue(
            cwebw.service_notification_commands == ["notify_by_nothing"],
            "WEBREADWRITE contact should use notify_by_nothing command"
        )

        # Assert: Verify MAIL contact properties
        self.assertTrue(
            cmail.can_submit_commands == False,
            "MAIL contact should not have command submission enabled"
        )
        self.assertTrue(
            cmail.service_notification_options == "w,c,u,r,f",
            "MAIL contact should have full notification options"
        )
        self.assertTrue(
            cmail.service_notification_commands == ["service-notify-by-email"],
            "MAIL contact should use email notification command"
        )
        self.assertTrue(
            cmail.email == "gerhard.lausser@consol.de",
            "MAIL contact should have correct email address"
        )

        # Assert: Verify custom ticket tool contact properties
        self.assertTrue(
            ctick.__class__.__name__ == "ContactMyTicketTool",
            "Custom ticket tool contact should use ContactMyTicketTool class"
        )
        self.assertTrue(
            ctick.can_submit_commands == False,
            "Ticket tool contact should not have command submission enabled"
        )
        self.assertTrue(
            ctick.service_notification_options == "w,c",
            "Ticket tool contact should have warning and critical notifications"
        )
        self.assertTrue(
            ctick.service_notification_commands == ["service-notify-by-msend"],
            "Ticket tool contact should use msend notification command"
        )
        self.assertTrue(
            ctick.queue_id == "lausser@consolq",
            "Ticket tool contact should have correct queue_id"
        )
        self.assertTrue(
            "ENVIRONMENT" in ctick.config_files['nagios']['contact_lausserg.cfg'],
            "Ticket tool contact config should contain ENVIRONMENT macro"
        )

        # Assert: Verify unknown ticket tool falls back to generic contact
        self.assertTrue(
            utick.__class__.__name__ == "GenericContact",
            "Unknown ticket tool should fall back to GenericContact class"
        )

        # Act: Write configuration files to output directory
        recipe.output()

        # Assert: Verify output directory was created
        self.assertTrue(
            os.path.exists("var/objects/test22/dynamic/hosts"),
            "Output directory should be created after running output()"
        )

    def test_create_bmc_contact_with_remedy_integration(self) -> None:
        """Test creation of BMC Remedy contact with specific notification settings.

        Verifies that BMC contact type is correctly created with Remedy-specific
        notification commands and options for both host and service notifications.

        Setup:
            - Creates a BMC contact object directly with dictionary parameters
            - Configures BMC-specific notification commands

        Expected Behavior:
            - BMC contact uses GenericContact class (no custom BMC class)
            - Cannot submit commands
            - Has both host and service notification settings
            - Uses Optis notification commands

        Assertions:
            - Contact class is GenericContact
            - Command submission is disabled
            - Service notification options are correct
            - Host notification options are correct
            - Notification commands are properly configured
        """
        # Arrange & Act: Create BMC contact object with specific parameters
        self.print_header()
        u_bmc = coshsh.contact.Contact({
            "type": "BMC",
            "name": "bmc",
            "userid": "bmc",
            "notification_period": "24x7",
            "service_notification_commands": ["notify-service-optis"],
            "host_notification_commands": ["notify-host-optis"],
            "host_notification_options": "d,u,r",
            "service_notification_options": "w,c,u,r,s",
        })

        # Assert: Verify BMC contact properties
        self.assertTrue(
            u_bmc.__class__.__name__ == "GenericContact",
            "BMC contact should use GenericContact class"
        )
        self.assertTrue(
            u_bmc.can_submit_commands == False,
            "BMC contact should not have command submission enabled"
        )
        self.assertTrue(
            u_bmc.service_notification_options == "w,c,u,r,s",
            "BMC contact should have all service notification options enabled"
        )
        self.assertTrue(
            u_bmc.host_notification_options == "d,u,r",
            "BMC contact should have down, unreachable, and recovery host notifications"
        )
        self.assertTrue(
            u_bmc.service_notification_commands == ["notify-service-optis"],
            "BMC contact should use Optis service notification command"
        )

    def test_create_custom_contacts_with_existing_templates(self) -> None:
        """Test creation of contacts that use existing custom templates.

        Verifies that contacts can reference existing Nagios templates through
        the 'use' directive and that these templates are correctly rendered
        in the contact configuration files.

        Setup:
            - Loads configuration for test221 recipe
            - Collects and assembles contacts
            - Assigns custom templates to contacts

        Expected Behavior:
            - Contacts can have multiple templates assigned
            - Templates are properly rendered in 'use' directive
            - Both custom contact templates and standard contact.tpl work

        Assertions:
            - Contact config files contain correct 'use' directive
            - Template names appear in the expected comma-separated format
            - Both custom and standard template rendering work correctly
        """
        # Arrange: Set up configuration and load contacts
        self.setUpConfig("etc/coshsh4.cfg", "test221")
        recipe = self.generator.recipes['test221']

        # Act: Collect and assemble contact objects
        recipe.collect()
        recipe.assemble()

        # Configure contacts with custom templates
        contacts = recipe.objects['contacts']

        # Contact using custom template (custom tpl file)
        cexitp1 = contacts['lausser+EXISTINGTEMPLATE+localit@wattens.swar.at+localit']
        cexitp1.templates = ["localit_inc5", "bereitschaft"]

        # Contact using standard contact.tpl
        cexitp2 = contacts['lausser+EXISTINGTEMPLATE2+localit2@wattens.swar.at+localit2']
        cexitp2.templates = ["localit_inc3", "bereitschaft"]

        # Render contact configuration files
        recipe.render()

        print("DEBUG" + str(cexitp1.config_files["nagios"].keys()))
        print("DEBUG" + cexitp1.config_files["nagios"]["contact_localit.cfg"])

        # Assert: Verify custom template contact has correct 'use' directive
        self.assertTrue(
            re.search(
                r'define.*use\s+localit_inc5,bereitschaft',
                cexitp1.config_files["nagios"]["contact_localit.cfg"],
                re.DOTALL
            ),
            "Contact with custom template should have 'use localit_inc5,bereitschaft' in config"
        )

        # Assert: Verify standard template contact has correct 'use' directive
        self.assertTrue(
            re.search(
                r'define.*use\s+localit_inc3,bereitschaft',
                cexitp2.config_files["nagios"]["contact_localit2.cfg"],
                re.DOTALL
            ),
            "Contact with standard template should have 'use localit_inc3,bereitschaft' in config"
        )
