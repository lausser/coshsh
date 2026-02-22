"""Unit tests for Datasource.add(), find(), get(), and host linking."""

from coshsh.host import Host
from coshsh.application import Application
from tests.common_coshsh_test import CommonCoshshTest


class DatasourceUnitTest(CommonCoshshTest):

    def _get_ds(self):
        """Return a concrete datasource from the test2 recipe."""
        self.setUpConfig("etc/coshsh.cfg", "test2")
        r = self.generator.get_recipe("test2")
        return r.get_datasource("simplesample")

    def test_add_host_stores_by_fingerprint(self):
        """add() stores host and find()/get() retrieve it by fingerprint."""
        ds = self._get_ds()
        host = Host({'host_name': 'myhost01', 'address': '127.0.0.1'})
        ds.add('hosts', host)
        self.assertTrue(ds.find('hosts', 'myhost01'))
        self.assertIs(ds.get('hosts', 'myhost01'), host)

    def test_add_application_links_to_host(self):
        """add() links application.host to the existing host object."""
        ds = self._get_ds()
        host = Host({'host_name': 'myhost01', 'address': '127.0.0.1'})
        ds.add('hosts', host)
        app = Application({'host_name': 'myhost01', 'name': 'myapp', 'type': 'web'})
        ds.add('applications', app)
        self.assertIs(app.host, host)

    def test_add_records_in_chronicle(self):
        """add() records a chronicle entry on the added object."""
        ds = self._get_ds()
        host = Host({'host_name': 'myhost01', 'address': '127.0.0.1'})
        ds.add('hosts', host)
        self.assertGreaterEqual(len(host.object_chronicle), 1)
        self.assertIn('datasource', host.object_chronicle[0])

    def test_get_returns_none_for_missing_fingerprint(self):
        """get() returns None for a fingerprint that does not exist."""
        ds = self._get_ds()
        self.assertIsNone(ds.get('hosts', 'nonexistent'))

    def test_find_returns_false_for_missing(self):
        """find() returns False for a fingerprint that does not exist."""
        ds = self._get_ds()
        self.assertFalse(ds.find('hosts', 'nonexistent'))

    def test_getall_returns_all_objects(self):
        """getall() returns all objects of the given type."""
        ds = self._get_ds()
        host1 = Host({'host_name': 'host1', 'address': '10.0.0.1'})
        host2 = Host({'host_name': 'host2', 'address': '10.0.0.2'})
        ds.add('hosts', host1)
        ds.add('hosts', host2)
        self.assertEqual(len(ds.getall('hosts')), 2)

    def test_getall_returns_empty_for_missing_type(self):
        """getall() returns an empty list for a type that has no objects."""
        ds = self._get_ds()
        self.assertEqual(ds.getall('nonexistent_type'), [])
