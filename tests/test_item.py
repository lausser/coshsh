"""Tests for Item base class: init, pythonize/depythonize, resolve_monitoring_details, render, and chronicle."""

import unittest
from coshsh.application import Application
from coshsh.host import Host
from coshsh.item import Item
from coshsh.monitoringdetail import MonitoringDetail
from tests.common_coshsh_test import CommonCoshshTest


class ItemTest(CommonCoshshTest):

    def test_depythonize_then_pythonize_restores_lists(self):
        """depythonize() converts lists to CSV strings, pythonize() splits them back.

        This is the only valid call sequence — both are used together inside
        render_cfg_template: depythonize() before rendering, pythonize() after.
        """
        host = Host({'host_name': 'h'})
        host.hostgroups = ['a', 'b', 'c']
        host.depythonize()
        self.assertIsInstance(host.hostgroups, str)
        host.pythonize()
        self.assertEqual(host.hostgroups, ['a', 'b', 'c'])

    def test_depythonize_joins_lists_to_string(self):
        """depythonize() joins list attributes to sorted comma-separated strings."""
        self.setUpConfig("etc/coshsh.cfg", "test1")
        app = Application({'host_name': 'h', 'name': 'a', 'type': 't'})
        app.hostgroups = ['b', 'a', 'c']
        app.depythonize()
        self.assertEqual(app.hostgroups, 'a,b,c')

    def test_depythonize_deduplicates(self):
        """depythonize() removes duplicate entries from lists."""
        self.setUpConfig("etc/coshsh.cfg", "test1")
        app = Application({'host_name': 'h', 'name': 'a', 'type': 't'})
        app.contacts = ['alice', 'bob', 'alice']
        app.depythonize()
        self.assertEqual(app.contacts, 'alice,bob')

    def test_pythonize_depythonize_roundtrip(self):
        """pythonize() and depythonize() roundtrip preserves set membership."""
        self.setUpConfig("etc/coshsh.cfg", "test1")
        app = Application({'host_name': 'h', 'name': 'a', 'type': 't'})
        app.hostgroups = ['web', 'linux']
        app.depythonize()
        app.pythonize()
        self.assertEqual(set(app.hostgroups), {'web', 'linux'})

    def test_templates_order_preserved_by_depythonize(self):
        """depythonize() does NOT sort templates — order matters."""
        self.setUpConfig("etc/coshsh.cfg", "test1")
        app = Application({'host_name': 'h', 'name': 'a', 'type': 't'})
        app.templates = ['base', 'override']
        app.depythonize()
        self.assertEqual(app.templates, 'base,override')

    def test_record_in_chronicle_appends_entry(self):
        """record_in_chronicle() appends messages to object_chronicle."""
        host = Host({'host_name': 'h'})
        host.record_in_chronicle('created')
        host.record_in_chronicle('updated')
        self.assertEqual(len(host.object_chronicle), 2)

    def test_record_in_chronicle_ignores_empty_message(self):
        """record_in_chronicle() does not append empty messages."""
        host = Host({'host_name': 'h'})
        host.record_in_chronicle('')
        self.assertEqual(host.object_chronicle, [])

    def test_dont_strip_attributes_bool_true(self):
        """dont_strip_attributes=True preserves whitespace on all attributes."""
        class NoStripHost(Host):
            dont_strip_attributes = True
        h = NoStripHost({'host_name': ' srv01 '})
        self.assertEqual(h.host_name, ' srv01 ')

    def test_dont_strip_attributes_list(self):
        """dont_strip_attributes=[name] preserves whitespace only on listed attributes."""
        class PartialStripItem(Item):
            dont_strip_attributes = ['description']
            monitoring_details = []
        item = object.__new__(PartialStripItem)
        item.dont_strip_attributes = ['description']
        Item.__init__(item, {'host_name': ' srv01 ', 'description': ' has spaces '})
        self.assertEqual(item.host_name, 'srv01')
        self.assertEqual(item.description, ' has spaces ')

    def test_item_fingerprint_falls_back_to_host_name(self):
        """Item.fingerprint() falls back to host_name when name/type are absent."""
        host = Host({'host_name': 'srv01'})
        # Host overrides fingerprint as a lambda, use the class method via Item
        result = Item.fingerprint(host)
        self.assertEqual(result, 'srv01')

    def test_item_fingerprint_raises_on_missing_all(self):
        """[BUG-3a fixed] Item.fingerprint() raises AttributeError when all identity fields are missing."""
        item = object.__new__(Item)
        item.monitoring_details = []
        item.config_files = {}
        item.object_chronicle = []
        with self.assertRaises(AttributeError):
            Item.fingerprint(item)

    def test_resolve_monitoring_details_unique_attribute_deduplication(self):
        """resolve_monitoring_details() deduplicates by unique_attribute."""
        self.setUpConfig("etc/coshsh.cfg", "test6")
        app = Application({
            'host_name': 'test', 'name': 'test', 'type': 'generic',
        })
        fs1 = MonitoringDetail({
            'host_name': 'test', 'name': 'test', 'type': 'generic',
            'monitoring_type': 'FILESYSTEM',
            'monitoring_0': '/',
            'monitoring_1': 90,
            'monitoring_2': 95,
        })
        fs2 = MonitoringDetail({
            'host_name': 'test', 'name': 'test', 'type': 'generic',
            'monitoring_type': 'FILESYSTEM',
            'monitoring_0': '/',
            'monitoring_1': 85,
            'monitoring_2': 90,
        })
        app.monitoring_details.extend([fs1, fs2])
        app.resolve_monitoring_details()
        self.assertEqual(len(app.filesystems), 1)

    def test_resolve_monitoring_details_unique_attribute_different_values(self):
        """resolve_monitoring_details() keeps entries with different unique_attribute values."""
        self.setUpConfig("etc/coshsh.cfg", "test6")
        app = Application({
            'host_name': 'test', 'name': 'test', 'type': 'generic',
        })
        fs1 = MonitoringDetail({
            'host_name': 'test', 'name': 'test', 'type': 'generic',
            'monitoring_type': 'FILESYSTEM',
            'monitoring_0': '/',
            'monitoring_1': 90,
            'monitoring_2': 95,
        })
        fs2 = MonitoringDetail({
            'host_name': 'test', 'name': 'test', 'type': 'generic',
            'monitoring_type': 'FILESYSTEM',
            'monitoring_0': '/var',
            'monitoring_1': 85,
            'monitoring_2': 90,
        })
        app.monitoring_details.extend([fs1, fs2])
        app.resolve_monitoring_details()
        self.assertEqual(len(app.filesystems), 2)

    # --- resolve_onto() unit tests ---

    def test_resolve_onto_generic_dict(self):
        """resolve_onto() for generic dict detail sets attributes including colon-nested keys."""
        self.setUpConfig("etc/coshsh.cfg", "test6")
        app = Application({'host_name': 'h', 'name': 'a', 'type': 't'})
        detail = MonitoringDetail({
            'host_name': 'h', 'name': 'a', 'type': 't',
            'monitoring_type': 'KEYVALUES',
            'monitoring_0': 'swap_warning', 'monitoring_1': '15%',
            'monitoring_2': 'thresholds:cron_warning', 'monitoring_3': '30',
        })
        detail.resolve_onto(app)
        self.assertEqual(app.swap_warning, '15%')
        self.assertTrue(hasattr(app, 'thresholds'))
        self.assertEqual(app.thresholds.cron_warning, '30')

    def test_resolve_onto_generic_list(self):
        """resolve_onto() for generic list detail extends list attributes on target."""
        self.setUpConfig("etc/coshsh.cfg", "test6")
        app = Application({'host_name': 'h', 'name': 'a', 'type': 't'})
        detail = MonitoringDetail({
            'host_name': 'h', 'name': 'a', 'type': 't',
            'monitoring_type': 'KEYVALUESARRAY',
            'monitoring_0': 'roles', 'monitoring_1': 'prod',
            'monitoring_2': 'roles', 'monitoring_3': 'dmz',
        })
        detail.resolve_onto(app)
        self.assertIn('prod', app.roles)
        self.assertIn('dmz', app.roles)

    def test_resolve_onto_generic_scalar(self):
        """resolve_onto() for generic scalar detail sets attribute/value on target."""
        self.setUpConfig("etc/coshsh.cfg", "test6")
        app = Application({'host_name': 'h', 'name': 'a', 'type': 't'})
        detail = MonitoringDetail({
            'host_name': 'h', 'name': 'a', 'type': 't',
            'monitoring_type': 'NAGIOS',
            'monitoring_0': 'max_check_attempts', 'monitoring_1': '5',
        })
        detail.resolve_onto(app)
        self.assertEqual(app.max_check_attempts, '5')

    def test_resolve_onto_named_list_plain(self):
        """resolve_onto() for list-typed detail appends detail object to list."""
        self.setUpConfig("etc/coshsh.cfg", "test6")
        app = Application({'host_name': 'h', 'name': 'a', 'type': 't'})
        port = MonitoringDetail({
            'host_name': 'h', 'name': 'a', 'type': 't',
            'monitoring_type': 'PORT', 'monitoring_0': '8080',
        })
        port.resolve_onto(app)
        self.assertEqual(len(app.ports), 1)
        self.assertEqual(app.ports[0].port, '8080')

    def test_resolve_onto_named_list_unique(self):
        """resolve_onto() for list-typed detail with unique_attribute deduplicates by that attribute."""
        self.setUpConfig("etc/coshsh.cfg", "test6")
        app = Application({'host_name': 'h', 'name': 'a', 'type': 't'})
        fs1 = MonitoringDetail({
            'host_name': 'h', 'name': 'a', 'type': 't',
            'monitoring_type': 'FILESYSTEM', 'monitoring_0': '/',
            'monitoring_1': '90', 'monitoring_2': '95',
        })
        fs2 = MonitoringDetail({
            'host_name': 'h', 'name': 'a', 'type': 't',
            'monitoring_type': 'FILESYSTEM', 'monitoring_0': '/',
            'monitoring_1': '80', 'monitoring_2': '90',
        })
        fs1.resolve_onto(app)
        fs2.resolve_onto(app)
        self.assertEqual(len(app.filesystems), 1)
        self.assertEqual(app.filesystems[0].warning, '80')

    def test_resolve_onto_named_list_property_attr(self):
        """resolve_onto() for list-typed detail with property_attr appends the flat attribute."""
        self.setUpConfig("etc/coshsh.cfg", "test6")
        app = Application({'host_name': 'h', 'name': 'a', 'type': 't'})
        tag = MonitoringDetail({
            'host_name': 'h', 'name': 'a', 'type': 't',
            'monitoring_type': 'TAG', 'monitoring_0': 'important',
        })
        tag.resolve_onto(app)
        self.assertEqual(app.tags, ['important'])

    def test_resolve_onto_named_dict(self):
        """resolve_onto() for dict-typed detail inserts key/value pair."""
        self.setUpConfig("etc/coshsh.cfg", "test6")
        app = Application({'host_name': 'h', 'name': 'a', 'type': 't'})
        macro = MonitoringDetail({
            'host_name': 'h', 'name': 'a', 'type': 't',
            'monitoring_type': 'CUSTOMMACRO',
            'monitoring_0': '_MYKEY', 'monitoring_1': 'myval',
        })
        macro.resolve_onto(app)
        self.assertEqual(app.custom_macros, {'_MYKEY': 'myval'})

    def test_resolve_onto_named_scalar(self):
        """resolve_onto() for scalar-typed detail assigns detail object as attribute."""
        self.setUpConfig("etc/coshsh.cfg", "test6")
        app = Application({'host_name': 'h', 'name': 'a', 'type': 't'})
        login = MonitoringDetail({
            'host_name': 'h', 'name': 'a', 'type': 't',
            'monitoring_type': 'LOGIN',
            'monitoring_0': 'admin', 'monitoring_1': 'secret',
        })
        login.resolve_onto(app)
        self.assertEqual(app.login.username, 'admin')
        self.assertEqual(app.login.password, 'secret')

    def test_resolve_onto_named_scalar_flat(self):
        """resolve_onto() for scalar-typed detail with property_flat assigns the inner value."""
        self.setUpConfig("etc/coshsh.cfg", "test6")
        app = Application({'host_name': 'h', 'name': 'a', 'type': 't'})
        role = MonitoringDetail({
            'host_name': 'h', 'name': 'a', 'type': 't',
            'monitoring_type': 'ROLE', 'monitoring_0': 'webserver',
        })
        role.resolve_onto(app)
        self.assertEqual(app.role, 'webserver')

    def test_resolve_onto_custom_override(self):
        """A subclass can override resolve_onto() for custom merge behaviour."""
        self.setUpConfig("etc/coshsh.cfg", "test6")
        from coshsh.monitoringdetail import MonitoringDetail as MD

        class CustomDetail(MD):
            property = "custom"
            property_type = str

            def __init__(self, params=None):
                if params is None:
                    params = {}
                self.monitoring_type = "CUSTOM"
                self.monitoring_0 = "x"
                self.val = params.get("val", "default")

            def resolve_onto(self, target):
                target.custom_resolved = f"custom:{self.val}"

        app = Application({'host_name': 'h', 'name': 'a', 'type': 't'})
        detail = CustomDetail({"val": "hello"})
        detail.resolve_onto(app)
        self.assertEqual(app.custom_resolved, "custom:hello")
        self.assertFalse(hasattr(app, 'custom'))

    def test_resolve_monitoring_details_url_property_attr(self):
        """resolve_monitoring_details() uses property_attr to extract scalar from URL detail."""
        self.setUpConfig("etc/coshsh.cfg", "test6")
        app = Application({
            'host_name': 'test', 'name': 'test', 'type': 'generic',
        })
        url = MonitoringDetail({
            'host_name': 'test', 'name': 'test', 'type': 'generic',
            'monitoring_type': 'URL',
            'monitoring_0': 'http://example.com',
        })
        app.monitoring_details.append(url)
        app.resolve_monitoring_details()
        self.assertTrue(hasattr(app, 'urls'))
        self.assertEqual(len(app.urls), 1)
