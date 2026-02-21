"""Tests for hostname transformation operations in datasource (to_lower, strip_domain, resolve_ip, resolve_dns)."""
import coshsh
from tests.common_coshsh_test import CommonCoshshTest


class MergeTest(CommonCoshshTest):

    def test_datasource_default(self):
        """Verify each hostname_transform_ops combination produces the expected transformed hostname."""
        self.setUpConfig("etc/coshsh_merge.cfg", "merge")

        self.generator.cookbook.set("datasource_merge", "name", "merge")
        cfg = self.generator.cookbook.items("datasource_merge")
        ds = coshsh.datasource.Datasource(**dict(cfg))
        self.assertTrue(hasattr(ds, 'hostname_transform_ops'))
        self.assertTrue(not ds.hostname_transform_ops)

        self.generator.cookbook.set("datasource_merge_lower", "name", "merge_lower")
        cfg = self.generator.cookbook.items("datasource_merge_lower")
        ds = coshsh.datasource.Datasource(**dict(cfg))
        self.assertTrue(hasattr(ds, 'hostname_transform_ops'))
        self.assertFalse(not ds.hostname_transform_ops)
        self.assertEqual(ds.hostname_transform_ops, ["to_lower"])
        self.assertEqual(ds.transform_hostname("TESTHOST0.hihi.de"), "testhost0.hihi.de")

        self.generator.cookbook.set("datasource_merge_lower_nodomain", "name", "merge_lower_nodomain")
        cfg = self.generator.cookbook.items("datasource_merge_lower_nodomain")
        ds = coshsh.datasource.Datasource(**dict(cfg))
        self.assertTrue(hasattr(ds, 'hostname_transform_ops'))
        self.assertFalse(not ds.hostname_transform_ops)
        self.assertEqual(ds.hostname_transform_ops, ["to_lower", "strip_domain"])
        self.assertEqual(ds.transform_hostname("TESTHOST0.hihi.de"), "testhost0")

        self.generator.cookbook.set("datasource_merge_lookup_upper", "name", "merge_lookup_upper")
        cfg = self.generator.cookbook.items("datasource_merge_lookup_upper")
        ds = coshsh.datasource.Datasource(**dict(cfg))
        self.assertTrue(hasattr(ds, 'hostname_transform_ops'))
        self.assertFalse(not ds.hostname_transform_ops)
        self.assertEqual(ds.hostname_transform_ops, ["resolve_ip", "to_upper"])
        self.assertEqual(ds.transform_hostname("127.0.0.1"), "LOCALHOST")
        self.assertEqual(ds.transform_hostname("94.185.88.1"), "DMZ1.CONSOL.NET")

        self.generator.cookbook.set("datasource_merge_lookup_nodomain", "name", "merge_lookup_nodomain")
        cfg = self.generator.cookbook.items("datasource_merge_lookup_nodomain")
        ds = coshsh.datasource.Datasource(**dict(cfg))
        self.assertTrue(hasattr(ds, 'hostname_transform_ops'))
        self.assertFalse(not ds.hostname_transform_ops)
        self.assertEqual(ds.hostname_transform_ops, ["resolve_dns", "to_upper", "strip_domain"])
        self.assertEqual(ds.transform_hostname("omd.consol.de"), "LABS")
