#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

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

def filter_rfc3986(text):
    return 'rfc3986://' + urllib.request.pathname2url(text.encode('utf-8'))

def filter_neighbor_applications(application):
    return [app for app in application.host.applications]

def global_environ(var, default=None):
    val = os.getenv(var, default)
    return val if val != None else ""
