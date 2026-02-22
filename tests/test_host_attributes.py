"""Tests for host template ordering and output path correctness."""
import os
import io
from random import choices, randint
from string import ascii_lowercase
from tests.common_coshsh_test import CommonCoshshTest


class HostAttributesTest(CommonCoshshTest):
    _configfile = 'etc/coshsh.cfg'
    _objectsdir = './var/objects/test10'

    def test_host_templates_order(self):
        """Verify template list is preserved through render and written to the correct output path."""
        self.setUpConfig("etc/coshsh.cfg", "test10")
        r = self.generator.get_recipe("test10")
        r.count_before_objects()
        r.cleanup_target_dir()
        r.prepare_target_dir()
        r.collect()
        saved_templates = {}
        for host in r.objects["hosts"].values():
            for length in range(3, randint(4, 10)):
                host.templates.append("".join(choices(ascii_lowercase, k=length)))
            saved_templates[host.host_name] = [t for t in host.templates]
        r.assemble()
        r.render()

        self.assertTrue(hasattr(r.objects["hosts"]["test_host_0"], "config_files"))
        self.assertIn("host.cfg", r.objects["hosts"]["test_host_0"].config_files["nagios"])

        r.output()
        self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts"))
        for host in r.objects["hosts"].values():
            self.assertTrue(os.path.exists("var/objects/test10/dynamic/hosts/" + host.host_name + "/host.cfg"))
            with io.open("var/objects/test10/dynamic/hosts/" + host.host_name + "/host.cfg") as f:
                host_cfg = f.read()
                self.assertIn(",".join(saved_templates[host.host_name]), host_cfg)
