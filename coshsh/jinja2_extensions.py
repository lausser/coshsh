#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""
Custom Jinja2 tests, filters, and globals used by coshsh templates to
generate Nagios/Icinga/Naemon configuration snippets.

Does NOT: register itself with Jinja2 automatically.  Registration happens
in Recipe.__init__(), which wires each function into the Jinja2 environment
as a test, filter, or global based on its prefix.

Key contents:
    Tests (registered in Jinja2 env.tests):
        is_re_match      -- Jinja2 test: true if a regex matches the string.

    Filters (registered in Jinja2 env.filters):
        filter_re_sub    -- Jinja2 filter: regex search-and-replace on strings.
        filter_re_escape -- Jinja2 filter: escape regex metacharacters.
        filter_service   -- Jinja2 filter: generate a Nagios "define service"
                            block, optionally splitting into a template and
                            an instance when NAGIOSCONF attributes are present.
        filter_host      -- Jinja2 filter: generate a Nagios "define host" block
                            with the same template-split logic as filter_service.
        filter_contact   -- Jinja2 filter: generate a Nagios "define contact"
                            block with template-split logic.
        filter_custom_macros -- Jinja2 filter: render custom macro lines
                            (prefixed with "_") for any monitoring object.
        filter_rfc3986   -- Jinja2 filter: percent-encode a string into a
                            URI using the rfc3986:// scheme prefix.
        filter_neighbor_applications -- Jinja2 filter: return all applications
                            sharing the same host.

    Globals (registered in Jinja2 env.globals):
        global_environ   -- Jinja2 global: read an environment variable at
                            render time.

Custom extension registration (my_jinja2_extensions):
    The recipe config key ``my_jinja2_extensions`` accepts a comma-separated
    list of function names.  Recipe.__init__() imports each name from a
    module called ``my_jinja2_extensions`` (which must be on sys.path, e.g.
    placed in the recipe's classes_dir) and registers it based on prefix:
        - ``is_*``      --> Jinja2 test  (prefix stripped)
        - ``filter_*``  --> Jinja2 filter (prefix stripped)
        - ``global_*``  --> Jinja2 global (prefix stripped)
    This allows users to add project-specific template helpers without
    modifying coshsh core code.

AI agent note:
    The ``service`` filter (filter_service) implements a two-tier output
    pattern: when an application has ``nagios_config_attributes`` matching
    the service_description, the filter emits a concrete service (with the
    NAGIOSCONF overrides) that ``use``s a generated template service.
    Without NAGIOSCONF attributes, a simple service definition is emitted.
    This dual-output pattern is central to coshsh's config-override model.
"""

import re
import urllib.request
import os

# Jinja2 extensions
r"""
** test re_match(pattern[, flags])
If regex pattern matches the string, return True.
Otherwise return False. The optional argument "flags"
is a string that may be empty (the default) or contain
one or more of regex flag characters.


*** filter re_sub(pattern, repl[, flags[, count]])
Return the string obtained by replacing the leftmost non-overlapping
occurrences of pattern in string by the replacement repl.
If the pattern isn't found, string is returned unchanged.


repl must be a string. Any backslash escapes in it are processed.
That is, \n is converted to a single newline character, \r is
converted
to a linefeed, and so forth. Unknown escapes such as \j are left
alone.
Backreferences, such as \6, are replaced with the substring
matched by group 6 in the pattern.


The optional argument "flags" is similar to the flags argument
in test re_match() (see above).


The optional argument count is the maximum number of pattern
occurrences to be replaced; count must be a non-negative integer.
If omitted or zero, all occurrences will be replaced.


*** filter re_escape
Return string with all non-alphanumerics backslashed;
this is useful if you want to match an arbitrary literal
string that may have regular expression metacharacters in it.
"""

# WHY: Regex flags are passed as a string (e.g. "im" for IGNORECASE+MULTILINE)
# rather than as Python constants because these functions are called from Jinja2
# templates where Python's re module is not directly accessible.  The string
# convention mirrors the inline-flag syntax familiar from most regex dialects.
def get_re_flags(flagstr):
    reflags = 0
    if flagstr:
        if flagstr.find("i") > -1: reflags |= re.IGNORECASE
        if flagstr.find("l") > -1: reflags |= re.LOCALE
        if flagstr.find("m") > -1: reflags |= re.MULTILINE
        if flagstr.find("s") > -1: reflags |= re.DOTALL
        if flagstr.find("u") > -1: reflags |= re.UNICODE
        if flagstr.find("x") > -1: reflags |= re.VERBOSE
    return reflags


def is_re_match(s, rs, flagstr=None):
    reflags = get_re_flags(flagstr)
    if re.search(rs, s, reflags):
        return True
    else:
        return False

def filter_re_sub(s, rs, repl, flagstr=None, count=0):
    reflags = get_re_flags(flagstr)
    myre = re.compile(rs, reflags)
    return re.sub(myre, repl, s, count)

def filter_re_escape(s):
    return re.escape(s)

# ['libkbo01.muc', 'os', 'linux', 'NAGIOSCONF', 'os_linux_default_check_ssh', 'max_check_attempts', '2', None, None, None],
# if a NAGIOSCONF attribute exists, the service is transformed into a
# service template (name=service_description+host_name) and a new service
# is created. the new service has all the NAGIOSCONF attributes and then
# uses the template
# WHY: The service filter implements a two-tier output pattern.  When a service
# has NAGIOSCONF overrides (stored as MonitoringDetail objects on the application),
# the filter creates BOTH a concrete service (with the overrides) AND a template
# service (register 0) that the concrete service inherits via "use".  This
# two-tier approach lets Nagios admins override individual service attributes
# per-host without duplicating the entire service definition.  Without
# NAGIOSCONF attributes, a single simple service block is emitted.
def filter_service(application, service_description):
    relevant_details = [d for d in getattr(application, "nagios_config_attributes", []) if d.name == service_description]
    if not relevant_details:
        snippet = "define service {\n  service_description             %s" % service_description
        if len(application.contact_groups) > 0:
            snippet += "\n  contact_groups %s" % (application.contact_groups, )
    else:
        snippet = "define service {\n  service_description             %s\n" % service_description
        for detail in relevant_details:
            snippet += "  %-31s %s\n" % (detail.attribute, detail.value)
        snippet += "  use                             %s_%s\n}\n" % (service_description, application.host_name, )
        snippet += "define service {\n  name                            %s_%s\n" % (service_description, application.host_name)
        snippet += "  register                        0"
        if len(application.contact_groups) > 0:
            snippet += "\n  contact_groups %s" % application.contact_groups
    macros = filter_custom_macros(application)
    if macros:
        snippet += macros
    return snippet

def filter_host(host):
    relevant_details = getattr(host, "nagios_config_attributes", [])
    if not relevant_details:
        snippet = "define host {\n  host_name                         %s" % host.host_name
        if len(host.contact_groups) > 0:
            snippet += "\n  contact_groups %s" % host.contact_groups
    else:
        snippet = "define host {\n  host_name                         %s\n" % host.host_name
        for detail in relevant_details:
            snippet += "  %-31s %s\n" % (detail.attribute, detail.value)
        snippet += "  use                             %s\n}\n" % (host.host_name + "_coshsh", )
        snippet += "define host {\n  name                            %s\n" % (host.host_name + "_coshsh", )
        snippet += "  register                        0"
        if len(host.contact_groups) > 0:
            snippet += "\n  contact_groups %s" % host.contact_groups
    macros = filter_custom_macros(host)
    if macros:
        snippet += macros
    return snippet

def filter_contact(contact):
    relevant_details = getattr(contact, "nagios_config_attributes", [])
    if not relevant_details:
        snippet = "define contact {\n  contact_name                      %s" % contact.contact_name
        if len(contact.contactgroups) > 0:
            snippet += "\n  contactgroups %s" % contact.contactgroups
    else:
        snippet = "define contact {\n  contact_name                      %s\n" % contact.contact_name
        for detail in relevant_details:
            snippet += "  %-31s %s\n" % (detail.attribute, detail.value)
        snippet += "  use                             %s\n}\n" % (contact.contact_name + "_coshsh", )
        snippet += "define contact {\n  name                            %s\n" % (contact.contact_name + "_coshsh", )
        snippet += "  register                        0"
        if len(contact.contactgroups) > 0:
            snippet += "\n  contactgroups %s" % contact.contactgroups
    macros = filter_custom_macros(contact)
    if macros:
        snippet += macros
    return snippet

def filter_custom_macros(obj):
    snippet = ""
    macros = "\n".join("  %-31s %s" % (k, v) for k, v in
        sorted([x if x[0].startswith("_") else ("_" + x[0], x[1]) \
            for x in list(getattr(obj, "custom_macros", {}).items()) + \
                 list(getattr(obj, "macros", {}).items())], key=lambda x: x[0]))
    if macros:
        snippet += "\n" + macros
    return snippet

# WHY: The rfc3986 filter encodes arbitrary text (typically a service description
# or hostname) into a URI-safe form.  This is used in templates that generate
# URLs for web-based monitoring dashboards (e.g., Thruk action URLs).
def filter_rfc3986(text):
    return 'rfc3986://' + urllib.request.pathname2url(text)

def filter_neighbor_applications(application):
    return [app for app in application.host.applications]

def global_environ(var, default=None):
    val = os.getenv(var, default)
    return val if val != None else ""
