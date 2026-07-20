#!/usr/bin/env python
# coshsh datarecipient skeleton.
# File name MUST be datarecipient_<something>.py.
# Place in a directory listed in the recipe's classes_dir.
#
# Datarecipients consume the assembled+rendered objects and write the
# final outputs (config files, JSON, pushes to an API, etc.).
# The built-in >>>recipient writes Nagios-style configs into objects_dir;
# add custom datarecipients to emit other formats or to push elsewhere.

import json
import logging
import os

from coshsh.datarecipient import Datarecipient

logger = logging.getLogger("coshsh")


def __dr_ident__(params={}):
    """Return the class for this datarecipient section, or None."""
    if params.get("type") == "CHANGEME":
        return MyDatarecipient
    return None


class MyDatarecipient(Datarecipient):
    """One-line description of what this emits and where."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Stash cookbook params:
        self.target = kwargs.get("target")
        # Required-param checks belong here so failures are loud and early.
        if not self.target:
            raise ValueError("MyDatarecipient requires 'target' in cookbook")

    def output(self, filter=None, objects={}):
        """Emit configs for the supplied objects.

        objects has keys 'hosts', 'applications', 'contacts', 'contactgroups'.
        Each is a dict {fingerprint: instance}. Iterate .values().

        If you only want items tagged with a specific for_tool, filter on
        TemplateRule.for_tool from the application's template_rules.
        """
        # Example: dump host targets as a JSON file.
        targets = []
        for host in objects.get("hosts", {}).values():
            targets.append({
                "labels": {
                    "host": host.host_name,
                    "address": host.address,
                },
                # Add per-application info if relevant:
                "apps": [a.name for a in host.applications],
            })

        # Write atomically: write to .tmp, then rename.
        tmp = self.target + ".tmp"
        with open(tmp, "w") as f:
            json.dump(targets, f, indent=2)
        os.replace(tmp, self.target)
        logger.info("MyDatarecipient wrote %d targets to %s", len(targets), self.target)
