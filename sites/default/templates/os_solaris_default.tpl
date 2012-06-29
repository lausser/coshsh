{{ application|service("os_solaris_default_check_ssh") }}
   host_name                       {{ application.host_name }}
   use                             os_solaris_default
   check_command                   check_ssh!$HOSTADDRESS$!60!22
}

{{ application|service("os_solaris_default_check_shell") }}
   use                             os_solaris_default
   max_check_attempts              10
   check_command                   check_ssh_login!$HOSTADDRESS$!60!22
}

{{ application|service("os_solaris_default_check_load") }}
   use                             os_solaris_default
   check_command                   check_by_ssh!60!$USER10$/lib/nagios/plugins/check_load -w 5.0,5.0,5.0 -c 10.0,10.0,10.0
}

{{ application|service("os_solaris_default_check_swap") }}
   use                             os_solaris_default
   check_command                   check_by_ssh!60!$USER10$/lib/nagios/plugins/check_swap -w 15% -c 8%
}

{{ application|service("os_solaris_default_check_ntp") }}
   use                             os_solaris_default
   normal_check_interval           60
   retry_check_interval            10
   check_command                   check_by_ssh!60!$USER10$/lib/nagios/plugins/check_ntp_health
}

{{ application|service("os_solaris_default_check_interfaces") }}
   use                             os_solaris_default
   check_command                   check_by_ssh!60!$USER10$/lib/nagios/plugins/check_interfaces
}

{% if application.host.virtual == "PS" %}
{{ application|service("os_solaris_default_check_hardware") }}
   use                             os_solaris_default
   normal_check_interval           15
   check_command                   check_by_ssh!60!$USER10$/lib/nagios/plugins/check_prtdiag
}
{% endif %}

{{ application|service("os_solaris_default_check_uptime") }}
   use                             os_solaris_default
   check_command                   check_by_ssh!60!$USER10$/lib/nagios/plugins/check_uptime 30
}

