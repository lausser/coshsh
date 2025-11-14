"""Test suite for host template ordering and attributes.

This module tests that host template attributes are correctly preserved
and maintained in their original order through the recipe processing pipeline.
"""

from __future__ import annotations

import os
from random import choices, randint
from string import ascii_lowercase

from tests.common_coshsh_test import CommonCoshshTest


class HostTemplateOrderingTest(CommonCoshshTest):
    """Test suite for host template order preservation.

    This suite verifies that:
    - Host templates maintain their order through collect/assemble/render
    - Random template additions preserve order
    - Template lists are correctly written to output config files
    - Template order is the same in memory and on disk

    Test Configuration:
        Uses test recipe: test10
        Configuration file: etc/coshsh.cfg
        Output directory: var/objects/test10

    Context:
        Template order is critical in Nagios-like systems because templates
        are processed in order and later templates can override earlier ones.
        This test ensures that the order defined in datasources is preserved
        all the way through to the final configuration files.
    """

    _configfile = 'etc/coshsh.cfg'
    _objectsdir = "./var/objects/test10"

    def print_header(self) -> None:
        """Print formatted test header with test ID.

        Outputs:
            Prints a formatted header box with the test ID centered.
        """
        print("#" * 80 + "\n" + "#" + " " * 78 + "#")
        print("#" + str.center(self.id(), 78) + "#")
        print("#" + " " * 78 + "#\n" + "#" * 80 + "\n")

    def test_host_templates_preserve_order_through_pipeline(self) -> None:
        """Test that host template order is preserved through processing.

        Host objects can have multiple templates assigned. The order of these
        templates matters in Nagios configuration. This test verifies that:
        1. Templates can be added dynamically to hosts
        2. Template order is preserved after assemble() and render()
        3. Template order in config files matches in-memory order

        Test Setup:
            - Loads recipe with standard hosts from CSV
            - Adds 4-10 random templates to each host
            - Saves the template order before processing
            - Processes through assemble and render phases
            - Compares final template order to saved order

        Expected Behavior:
            - Host objects have config_files attribute after rendering
            - Each host has a host.cfg file
            - Output files are created for each host
            - Template order in config files exactly matches saved order

        Assertions:
            - Hosts have config_files attribute
            - host.cfg exists in config_files
            - Output directory structure is created
            - Each host has host.cfg file
            - Template list in config file matches saved order
        """
        # Arrange: Set up recipe and prepare for collection
        self.setUpConfig("etc/coshsh.cfg", "test10")
        recipe = self.generator.get_recipe("test10")
        recipe.count_before_objects()
        recipe.cleanup_target_dir()
        recipe.prepare_target_dir()
        recipe.collect()

        # Add random templates to each host and save the order
        saved_templates = {}
        for host in recipe.objects["hosts"].values():
            # Add 4-10 random templates of varying lengths (3+ characters)
            for length in range(3, randint(4, 10)):
                host.templates.append("".join(choices(ascii_lowercase, k=length)))
            saved_templates[host.host_name] = [template for template in host.templates]
            print("{} has {}".format(host.host_name, ",".join(host.templates)))

        # Act: Process recipe through assemble and render
        recipe.assemble()
        recipe.render()

        # Verify templates are still in order after processing
        for host in recipe.objects["hosts"].values():
            print("{} has {}".format(host.host_name, ",".join(host.templates)))

        # Assert: Verify config_files attribute exists
        self.assertTrue(
            hasattr(recipe.objects['hosts']['test_host_0'], 'config_files'),
            "Host should have config_files attribute after rendering"
        )
        self.assertTrue(
            'host.cfg' in recipe.objects['hosts']['test_host_0'].config_files['nagios'],
            "Host should have host.cfg in Nagios config files"
        )

        # Act: Write config files to disk
        recipe.output()

        # Assert: Verify output structure and template order in files
        self.assertTrue(
            os.path.exists("var/objects/test10/dynamic/hosts"),
            "Hosts output directory should be created"
        )

        for host in recipe.objects["hosts"].values():
            host_cfg_path = "var/objects/test10/dynamic/hosts/" + host.host_name + "/host.cfg"

            self.assertTrue(
                os.path.exists(host_cfg_path),
                f"Config file should exist for host {host.host_name}"
            )

            # Read the host config file
            with open(host_cfg_path) as f:
                host_cfg = f.read()

            # Verify template order is preserved in the config file
            expected_templates = ",".join(saved_templates[host.host_name])
            self.assertTrue(
                expected_templates in host_cfg,
                f"Host {host.host_name} config should contain templates in order: {expected_templates}"
            )
