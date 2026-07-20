#!/usr/bin/env python
# coshsh custom MonitoringDetail skeleton.
# File name MUST be detail_<something>.py.
# Place in a directory listed in the recipe's classes_dir.
#
# Most projects don't need this — built-in monitoring_types
# (FILESYSTEM, PORT, INTERFACE, URL, LOGIN, etc.) cover most cases.
# Subclass MonitoringDetail only when you need a custom data shape
# not expressible via the built-in slots.

from coshsh.monitoringdetail import MonitoringDetail


def __detail_ident__(params={}):
    """Return the class for this monitoring_type, or None to pass."""
    if params["monitoring_type"] == "MY_CUSTOM_TYPE":
        return MyCustomDetail
    return None


class MyCustomDetail(MonitoringDetail):
    """Description of what this monitoring detail represents."""

    # The attribute name on the parent application where instances land.
    # If property_type is list, parent.things will be a list of instances.
    # If property_type is "scalar", the LAST instance wins.
    property = "things"
    property_type = list

    def __init__(self, params={}):
        super().__init__(params)
        # The slot fields are monitoring_0, monitoring_1, ...
        # Give them meaningful names here.
        self.path = params.get("monitoring_0")
        self.alias = params.get("monitoring_1")
        self.warning = params.get("monitoring_2", 80)
        self.critical = params.get("monitoring_3", 90)

    def fingerprint(self):
        """Uniqueness key for dedup. Two details with the same
        fingerprint on the same app are treated as one (later wins)."""
        return self.path
