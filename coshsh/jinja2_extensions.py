#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Jinja2 custom filters and tests for coshsh templates.

This module provides custom Jinja2 extensions used in coshsh templates:
- Regex operations (match, substitute, escape)
- Nagios configuration helpers (service, host, contact)
- Custom macro handling
- URL encoding

These are registered with the Jinja2 environment and available in all templates.
"""

from __future__ import annotations

import re
import urllib.request
import os
from typing import Optional, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from coshsh.application import Application
    from coshsh.host import Host
    from coshsh.contact import Contact

# Jinja2 extensions documentation
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

def get_re_flags(flagstr: Optional[str]) -> int:
    """Convert flag string to regex flags.

    Args:
        flagstr: String containing regex flag characters:
            'i' = IGNORECASE, 'l' = LOCALE, 'm' = MULTILINE,
            's' = DOTALL, 'u' = UNICODE, 'x' = VERBOSE

    Returns:
        Combined regex flags as integer
    """
    reflags = 0
    if flagstr:
        if "i" in flagstr: reflags |= re.IGNORECASE
        if "l" in flagstr: reflags |= re.LOCALE
        if "m" in flagstr: reflags |= re.MULTILINE
        if "s" in flagstr: reflags |= re.DOTALL
        if "u" in flagstr: reflags |= re.UNICODE
        if "x" in flagstr: reflags |= re.VERBOSE
    return reflags


def is_re_match(s: str, rs: str, flagstr: Optional[str] = None) -> bool:
    """Test if regex pattern matches the string.

    Jinja2 test function for regex matching.

    Args:
        s: String to search in
        rs: Regex pattern to search for
        flagstr: Optional regex flags (see get_re_flags)

    Returns:
        True if pattern matches, False otherwise
    """
    reflags = get_re_flags(flagstr)
    return bool(re.search(rs, s, reflags))


def filter_re_sub(s: str, rs: str, repl: str, flagstr: Optional[str] = None, count: int = 0) -> str:
    """Replace regex pattern matches in string.

    Jinja2 filter for regex substitution.

    Args:
        s: String to perform substitution on
        rs: Regex pattern to match
        repl: Replacement string (can include backreferences like \\1, \\2)
        flagstr: Optional regex flags (see get_re_flags)
        count: Maximum number of replacements (0 = all)

    Returns:
        String with replacements made
    """
    reflags = get_re_flags(flagstr)
    myre = re.compile(rs, reflags)
    return re.sub(myre, repl, s, count)


def filter_re_escape(s: str) -> str:
    """Escape regex metacharacters in string.

    Jinja2 filter to escape special regex characters.

    Args:
        s: String to escape

    Returns:
        String with all regex metacharacters escaped
    """
    return re.escape(s)

def filter_service(application: Application, service_description: str) -> str:
    """Generate Nagios service configuration snippet.

    If NAGIOSCONF attributes exist, creates a service template and a service
    that uses the template. Otherwise creates a simple service definition.

    Args:
        application: Application object with config attributes
        service_description: Name of the service

    Returns:
        Nagios configuration snippet for the service
    """
    relevant_details = [d for d in getattr(application, "nagios_config_attributes", [])
                       if d.name == service_description]

    if not relevant_details:
        snippet = f"define service {{\n  service_description             {service_description}"
        if len(application.contact_groups) > 0:
            snippet += f"\n  contact_groups {application.contact_groups}"
    else:
        snippet = f"define service {{\n  service_description             {service_description}\n"
        for detail in relevant_details:
            snippet += f"  {detail.attribute:<31} {detail.value}\n"
        snippet += f"  use                             {service_description}_{application.host_name}\n}}\n"
        snippet += f"define service {{\n  name                            {service_description}_{application.host_name}\n"
        snippet += "  register                        0"
        if len(application.contact_groups) > 0:
            snippet += f"\n  contact_groups {application.contact_groups}"

    macros = filter_custom_macros(application)
    if macros:
        snippet += macros
    return snippet

def filter_host(host: Host) -> str:
    """Generate Nagios host configuration snippet.

    If NAGIOSCONF attributes exist, creates a host template and a host
    that uses the template. Otherwise creates a simple host definition.

    Args:
        host: Host object with config attributes

    Returns:
        Nagios configuration snippet for the host
    """
    relevant_details = getattr(host, "nagios_config_attributes", [])
    if not relevant_details:
        snippet = f"define host {{\n  host_name                         {host.host_name}"
        if len(host.contact_groups) > 0:
            snippet += f"\n  contact_groups {host.contact_groups}"
    else:
        snippet = f"define host {{\n  host_name                         {host.host_name}\n"
        for detail in relevant_details:
            snippet += f"  {detail.attribute:<31} {detail.value}\n"
        snippet += f"  use                             {host.host_name}_coshsh\n}}\n"
        snippet += f"define host {{\n  name                            {host.host_name}_coshsh\n"
        snippet += "  register                        0"
        if len(host.contact_groups) > 0:
            snippet += f"\n  contact_groups {host.contact_groups}"

    macros = filter_custom_macros(host)
    if macros:
        snippet += macros
    return snippet

def filter_contact(contact: Contact) -> str:
    """Generate Nagios contact configuration snippet.

    If NAGIOSCONF attributes exist, creates a contact template and a contact
    that uses the template. Otherwise creates a simple contact definition.

    Args:
        contact: Contact object with config attributes

    Returns:
        Nagios configuration snippet for the contact
    """
    relevant_details = getattr(contact, "nagios_config_attributes", [])
    if not relevant_details:
        snippet = f"define contact {{\n  contact_name                      {contact.contact_name}"
        if len(contact.contactgroups) > 0:
            snippet += f"\n  contactgroups {contact.contactgroups}"
    else:
        snippet = f"define contact {{\n  contact_name                      {contact.contact_name}\n"
        for detail in relevant_details:
            snippet += f"  {detail.attribute:<31} {detail.value}\n"
        snippet += f"  use                             {contact.contact_name}_coshsh\n}}\n"
        snippet += f"define contact {{\n  name                            {contact.contact_name}_coshsh\n"
        snippet += "  register                        0"
        if len(contact.contactgroups) > 0:
            snippet += f"\n  contactgroups {contact.contactgroups}"

    macros = filter_custom_macros(contact)
    if macros:
        snippet += macros
    return snippet


def filter_custom_macros(obj: Any) -> str:
    """Generate custom Nagios macros from object attributes.

    Combines custom_macros and macros attributes, ensures all macro names
    start with underscore, and formats them for Nagios config.

    Args:
        obj: Object with custom_macros and/or macros attributes

    Returns:
        Formatted custom macro definitions (empty string if none)
    """
    snippet = ""
    # Collect all macros, ensuring they start with underscore
    all_macros = (list(getattr(obj, "custom_macros", {}).items()) +
                  list(getattr(obj, "macros", {}).items()))
    normalized_macros = [(k if k.startswith("_") else f"_{k}", v) for k, v in all_macros]

    # Format and sort by macro name
    macros = "\n".join(f"  {k:<31} {v}" for k, v in sorted(normalized_macros, key=lambda x: x[0]))
    if macros:
        snippet += "\n" + macros
    return snippet


def filter_rfc3986(text: str) -> str:
    """Convert text to RFC 3986 URI format.

    Jinja2 filter to URL-encode text with RFC 3986 scheme.

    Args:
        text: Text to encode

    Returns:
        RFC 3986 formatted URI
    """
    return 'rfc3986://' + urllib.request.pathname2url(text.encode('utf-8'))


def filter_neighbor_applications(application: Application) -> List[Application]:
    """Get all applications on the same host.

    Jinja2 filter to access neighbor applications.

    Args:
        application: Application object

    Returns:
        List of all applications on the same host
    """
    return [app for app in application.host.applications]


def global_environ(var: str, default: Optional[str] = None) -> str:
    """Get environment variable value.

    Jinja2 global function to access environment variables from templates.

    Args:
        var: Environment variable name
        default: Default value if variable not set

    Returns:
        Environment variable value or empty string
    """
    val = os.getenv(var, default)
    return val if val is not None else ""
