"""Windows OS Application Plugin

This plugin handles monitoring configuration for Windows operating systems.

Plugin Identification:
---------------------
Automatically identifies Windows systems by matching the OS type against
the pattern ".*windows.*".

When an application with name="os" and type matching "windows" is
detected, it is upgraded to a Windows application object.

NSClient++ Remote Monitoring:
-----------------------------
The plugin configures NSClient++ (NSCP) based remote monitoring by
setting custom macros for NSCP connection parameters:

    _NSCPORT: NSClient++ port number (default: 18443 for HTTPS)
    _NSCPASSWORD: NSClient++ password (default: 'secret')

These macros are set both at application and host level, allowing
check_nrpe/check_nscp commands to use $_HOSTNSCPORT$ and similar
host macros.

Template Rules:
---------------
The plugin uses these templates:

1. os_windows_default: Always applied (needsattr=None)
   - Basic Windows system checks
   - CPU, memory, disk space
   - Windows services
   - Event log monitoring

2. os_windows_fs: Applied when 'filesystems' attribute exists
   - Detailed filesystem/drive monitoring
   - Per-drive checks
   - Mount point validation

Configuration Example:
---------------------
CSV datasource:
    host_name,name,type,component,version
    winserver01,os,windows,server,2019
    winserver02,os,windows,server,2016

Template Usage:
---------------
Jinja2 template example (os_windows_default.tpl):
    define service {
        host_name               {{ application.host_name }}
        service_description     NSClient Health
        check_command           check_nscp!$_HOSTNSCPORT$!$_HOSTNSCPASSWORD$!check_cpu
        ...
    }

Security Note:
--------------
The NSCPASSWORD macro stores passwords in plain text in the generated
monitoring configuration. For production use, consider:
    - Using strong, unique passwords per host
    - Restricting file permissions on generated configs
    - Using certificate-based authentication where possible
    - Using vault integration to avoid hardcoded passwords

Classes:
--------
- Windows: Windows OS application with full monitoring
"""

from __future__ import annotations

from typing import Optional, Dict, Any

import coshsh
from coshsh.application import Application
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr, is_attr


def __mi_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify Windows OS applications.

    Called by the plugin factory system to determine if an application
    should be upgraded to a Windows application object.

    Matches applications where:
        - name = "os"
        - type matches ".*windows.*"

    Args:
        params: Application attributes dictionary

    Returns:
        Windows class if matches Windows OS pattern
        None if no match

    Example:
        params = {'name': 'os', 'type': 'windows'}
        Returns: Windows class

        params = {'name': 'os', 'type': 'linux'}
        Returns: None
    """
    if params is None:
        params = {}

    if (coshsh.util.is_attr("name", params, "os") and
        coshsh.util.compare_attr("type", params, ".*windows.*")):
        return Windows
    return None


class Windows(Application):
    """Windows OS application with full monitoring capabilities.

    Provides comprehensive Windows system monitoring including:
        - System resources (CPU, memory, disk)
        - Windows services
        - Event logs
        - Drive/filesystem monitoring
        - NSClient++ based remote checks

    Template Rules:
        1. os_windows_default: Base Windows monitoring (always applied)
        2. os_windows_fs: Filesystem/drive checks (when filesystems defined)

    NSClient++ Configuration:
        Automatically configures NSCP connection parameters as custom
        macros, both at application and host level.

    Attributes:
        NSCPORT: NSClient++ port (default: 18443)
        NSCPASSWORD: NSClient++ password (default: 'secret')
        custom_macros: Dictionary of custom Nagios/Naemon macros
    """

    template_rules = [
        coshsh.templaterule.TemplateRule(
            needsattr=None,
            template="os_windows_default"
        ),
        coshsh.templaterule.TemplateRule(
            needsattr="filesystems",
            template="os_windows_fs"
        ),
    ]

    def wemustrepeat(self) -> None:
        """Configure NSClient++ monitoring macros.

        Called during the assembly phase to set up NSClient++ connection
        parameters for remote Windows monitoring.

        Sets custom macros at both application and host level:
            _NSCPORT: Port for NSClient++ connections (default: 18443)
            _NSCPASSWORD: Password for NSClient++ authentication

        Why at Both Levels?
            Application macros: For application-specific checks
            Host macros: Allow generic check_nscp commands using
                        $_HOSTNSCPORT$ without duplicating config

        Example:
            # In datasource or application definition
            NSCPORT = 5666
            NSCPASSWORD = MySecurePassword123

            # Results in macros:
            _NSCPORT = 5666
            _NSCPASSWORD = MySecurePassword123

        Security Considerations:
            The password is stored in plain text in the generated
            monitoring configuration. In production:
                - Use strong, unique passwords
                - Restrict file permissions on generated configs
                - Consider using @VAULT[...] for password storage

        Note:
            Method name is historical ("wemustrepeat" = "we must repeat"
            pattern used for objects that need post-processing).
        """
        # Get NSClient++ parameters with fallbacks to defaults
        self.NSCPORT = getattr(self, 'NSCPORT', 18443)
        self.NSCPASSWORD = getattr(self, 'NSCPASSWORD', 'secret')

        # Set application-level custom macros
        if not hasattr(self, 'custom_macros'):
            self.custom_macros = {}
        self.custom_macros['_NSCPORT'] = self.NSCPORT
        self.custom_macros['_NSCPASSWORD'] = self.NSCPASSWORD

        # Also set as host macros for generic check_nscp usage
        # This allows commands like: check_nscp -H $HOSTADDRESS$ -p $_HOSTNSCPORT$
        # without needing to specify macros on every application
        if not hasattr(self.host, 'custom_macros'):
            self.host.custom_macros = {}
        self.host.custom_macros['_NSCPORT'] = self.NSCPORT
        self.host.custom_macros['_NSCPASSWORD'] = self.NSCPASSWORD
