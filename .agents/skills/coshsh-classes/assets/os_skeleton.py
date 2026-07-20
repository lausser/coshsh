#!/usr/bin/env python
# coshsh OS class skeleton.
# File name MUST be os_<something>.py.
# Place in a directory listed in the recipe's classes_dir.
#
# os_*.py files are functionally identical to app_*.py — the prefix is
# just a convention for "this represents an operating system".

from coshsh.application import Application
from coshsh.templaterule import TemplateRule


def __mi_ident__(params={}):
    """Called for every Application(...) being assembled.

    params is the Application's params dict (host_name, name, type, ...).
    Standard dispatch is on params["type"], lowercased.
    Return the class to re-bless this Application into, or None.
    """
    if params["type"].lower() in ("redhat", "centos", "rocky", "alma"):
        return RedHat
    return None


class RedHat(Application):
    """Red Hat family Linux."""

    # Templates rendered for every RedHat instance.
    # Always extend Application.template_rules with `+ [...]` rather than
    # calling .append() so the parent class list isn't mutated.
    template_rules = Application.template_rules + [
        TemplateRule(
            template="os_linux_default",
            unique_attr="type",
        ),
        TemplateRule(
            needsattr="filesystems",
            template="os_linux_fs",
        ),
        TemplateRule(
            needsattr="interfaces",
            template="os_linux_if",
        ),
    ]

    # Optional: custom init for derived attributes.
    # def __init__(self, params={}):
    #     super().__init__(params)
    #     self.is_rhel9 = self.version and self.version.startswith("9")

    # Optional: second-pass hook. Runs after all details have been
    # attached, so self.filesystems etc. are available.
    # def wemustrepeat(self):
    #     self.has_lvm = any(fs.path.startswith("/dev/mapper") for fs in self.filesystems)
