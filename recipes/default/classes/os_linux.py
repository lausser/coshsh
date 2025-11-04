"""Linux OS Application Plugin

This plugin handles monitoring configuration for Linux operating systems.

Plugin Identification:
---------------------
Automatically identifies Linux systems by matching the OS type against
various Linux distribution patterns:
    - Red Hat / RHEL
    - SLES (SUSE Linux Enterprise Server)
    - Generic Linux
    - Debian
    - Ubuntu
    - CentOS
    - "limux" (typo tolerance)

When an application with name="os" and type matching any of these
patterns is detected, it is upgraded to a Linux application object.

SSH Remote Monitoring:
---------------------
The plugin configures SSH-based remote monitoring by setting custom
macros for SSH connection parameters:

    _SSHPORT: SSH port number (default: 22)
    _SSHUSER: SSH username (default: 'mon' or OMD_CLIENT_USER_LINUX env var)
    _SSHPATHPREFIX: Path prefix for remote scripts (default: '.' or OMD_CLIENT_PATH_PREFIX env var)

These macros are set both at application and host level, allowing
check_by_ssh commands to use $_HOSTSSHUSER$ and similar host macros.

Template Rules:
---------------
The plugin uses these templates:

1. os_linux_default: Always applied (needsattr=None)
   - Basic Linux system checks
   - CPU, memory, load average
   - Disk space (if not using os_linux_fs)

2. os_linux_fs: Applied when 'filesystems' attribute exists
   - Detailed filesystem monitoring
   - Per-filesystem checks
   - Mount point validation

Embedded Linux:
---------------
EmbeddedLinux is a simplified variant for embedded systems that only
performs basic heartbeat monitoring (os_linux_heartbeat template).

Configuration Example:
---------------------
CSV datasource:
    host_name,name,type,component,version
    server01,os,linux,rhel,7.9
    server02,os,ubuntu,server,20.04

Environment variables:
    OMD_CLIENT_USER_LINUX=monitoring  # SSH user for Linux monitoring
    OMD_CLIENT_PATH_PREFIX=/usr/local/libexec  # Path to monitoring scripts

Usage in Templates:
------------------
Jinja2 template example (os_linux_default.tpl):
    define service {
        host_name               {{ application.host_name }}
        service_description     SSH Alive
        check_command           check_by_ssh!$_HOSTSSHUSER$!$_HOSTSSHPORT$!check_alive
        ...
    }

Classes:
--------
- Linux: Main Linux OS application with full monitoring
- EmbeddedLinux: Simplified variant for embedded systems
"""

from __future__ import annotations

import os
from typing import Optional, Dict, Any

import coshsh
from coshsh.application import Application
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr, is_attr


def __mi_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify Linux OS applications.

    Called by the plugin factory system to determine if an application
    should be upgraded to a Linux application object.

    Matches applications where:
        - name = "os"
        - type matches any Linux distribution pattern

    Args:
        params: Application attributes dictionary

    Returns:
        Linux class if matches Linux OS patterns
        None if no match

    Example:
        params = {'name': 'os', 'type': 'rhel'}
        Returns: Linux class

        params = {'name': 'os', 'type': 'windows'}
        Returns: None
    """
    if params is None:
        params = {}

    if (coshsh.util.is_attr("name", params, "os") and
        coshsh.util.compare_attr("type", params,
            r".*red\s*hat.*|.*rhel.*|.*sles.*|.*linux.*|.*limux.*|"
            r".*debian.*|.*ubuntu.*|.*centos.*")):
        return Linux
    return None


class Linux(coshsh.application.Application):
    """Linux OS application with full monitoring capabilities.

    Provides comprehensive Linux system monitoring including:
        - System resources (CPU, memory, load)
        - Disk/filesystem monitoring
        - SSH-based remote checks
        - Custom filesystem checks when 'filesystems' attribute present

    Template Rules:
        1. os_linux_default: Base Linux monitoring (always applied)
        2. os_linux_fs: Filesystem checks (when filesystems defined)

    SSH Configuration:
        Automatically configures SSH connection parameters as custom
        macros, both at application and host level.

    Attributes:
        SSHPORT: SSH port (default: 22)
        SSHUSER: SSH username (default: 'mon' or OMD_CLIENT_USER_LINUX)
        SSHPATHPREFIX: Script path (default: '.' or OMD_CLIENT_PATH_PREFIX)
        custom_macros: Dictionary of custom Nagios/Naemon macros
    """

    template_rules = [
        coshsh.templaterule.TemplateRule(
            needsattr=None,
            template="os_linux_default"
        ),
        coshsh.templaterule.TemplateRule(
            needsattr="filesystems",
            template="os_linux_fs"
        ),
    ]

    def wemustrepeat(self) -> None:
        """Configure SSH monitoring macros.

        Called during the assembly phase to set up SSH connection
        parameters for remote monitoring via check_by_ssh.

        Sets custom macros at both application and host level:
            _SSHPORT: Port for SSH connections
            _SSHUSER: Username for SSH connections
            _SSHPATHPREFIX: Path prefix for monitoring scripts

        Environment Variables:
            OMD_CLIENT_USER_LINUX: Override default SSH username
            OMD_CLIENT_PATH_PREFIX: Override default script path

        Why at Both Levels?
            Application macros: For application-specific checks
            Host macros: Allow generic check_by_ssh commands using
                        $_HOSTSSHUSER$ without duplicating config

        Example:
            # Environment
            export OMD_CLIENT_USER_LINUX=nagios
            export OMD_CLIENT_PATH_PREFIX=/usr/lib/nagios/plugins

            # Results in macros:
            _SSHUSER = nagios
            _SSHPATHPREFIX = /usr/lib/nagios/plugins
            _SSHPORT = 22

        Note:
            Method name is historical ("wemustrepeat" = "we must repeat"
            pattern used for objects that need post-processing).
        """
        # Get SSH parameters with fallbacks to environment or defaults
        self.SSHPORT = getattr(self, 'SSHPORT', 22)
        self.SSHUSER = getattr(
            self,
            'SSHUSER',
            os.environ.get('OMD_CLIENT_USER_LINUX', 'mon')
        )
        self.SSHPATHPREFIX = getattr(
            self,
            'SSHPATHPREFIX',
            os.environ.get('OMD_CLIENT_PATH_PREFIX', '.')
        )

        # Set application-level custom macros
        if not hasattr(self, 'custom_macros'):
            self.custom_macros = {}
        self.custom_macros['_SSHPORT'] = self.SSHPORT
        self.custom_macros['_SSHUSER'] = self.SSHUSER
        self.custom_macros['_SSHPATHPREFIX'] = self.SSHPATHPREFIX

        # Also set as host macros for generic check_by_ssh usage
        # This allows commands like: check_by_ssh -l $_HOSTSSHUSER$ -p $_HOSTSSHPORT$
        # without needing to specify macros on every application
        if not hasattr(self.host, 'custom_macros'):
            self.host.custom_macros = {}
        self.host.custom_macros['_SSHPORT'] = self.SSHPORT
        self.host.custom_macros['_SSHUSER'] = self.SSHUSER
        self.host.custom_macros['_SSHPATHPREFIX'] = self.SSHPATHPREFIX


class EmbeddedLinux(Linux):
    """Embedded Linux OS application with minimal monitoring.

    Simplified variant for embedded Linux systems (routers, IoT devices,
    appliances) that only performs basic heartbeat/alive checks.

    Uses os_linux_heartbeat template instead of full system monitoring.
    Inherits SSH configuration from Linux parent class.

    Template Rules:
        1. os_linux_heartbeat: Basic alive check only

    Example Use Cases:
        - Network routers
        - IoT devices
        - Industrial controllers
        - Appliances with minimal monitoring needs

    Configuration:
        To use EmbeddedLinux, manually set the application class or
        create a custom identification function.
    """

    template_rules = [
        coshsh.templaterule.TemplateRule(
            needsattr=None,
            template="os_linux_heartbeat"
        ),
    ]
