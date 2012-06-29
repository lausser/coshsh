{{ application|service("os_linux_default_check_ssh") }}
  host_name                       {{ application.host_name }}
  use                             os_linux_default
  check_command                   check_ssh!60!22
}

{#
{{ application|service("os_linux_default_check_shell") }}
  host_name                       {{ application.host_name }}
  use                             os_linux_default
  max_check_attempts              10
  check_command                   check_ssh_login!60!22
}
#}

{{ application|service("os_linux_default_check_load") }}
  host_name                       {{ application.host_name }}
  use                             os_linux_default,srv-pnp
  check_command                   check_by_ssh!60!$USER10$/lib/nagios/plugins/check_load -w 5.0,5.0,5.0 -c 10.0,10.0,10.0
}

{{ application|service("os_linux_default_check_swap") }}
  host_name                       {{ application.host_name }}
  use                             os_linux_default,srv-pnp
  check_command                   check_by_ssh!60!$USER10$/lib/nagios/plugins/check_swap -w 15% -c 8%
}

{{ application|service("os_linux_default_check_crond") }}
  use                             os_linux_default
  host_name                       {{ application.host_name }}
{% if application.type.startswith('sles') %}
  check_command                   check_by_ssh!60!$USER10$/lib/nagios/plugins/check_procs -w :10 -c 1: -C cron
{% else %}
  check_command                   check_by_ssh!60!$USER10$/lib/nagios/plugins/check_procs -w :10 -c 1: -C crond
{% endif %}
}

{#
  virtuelle Server bekommen ihre Uhrzeit vom Hostsystem
#}
{% if application.host.virtual == "PS" %}
{{ application|service("os_linux_default_check_ntp") }}
  use                             os_linux_default
  host_name                       {{ application.host_name }}
  check_interval                  60
  retry_interval                  10
  check_command                   check_by_ssh!60!$USER10$/local/lib/nagios/plugins/check_ntp_health
}


{{ application|service("os_linux_default_check_interfaces") }}
  host_name                       {{ application.host_name }}
  use                             os_linux_default
  check_command                   check_by_ssh!60!$USER10$/lib/nagios/plugins/check_interfaces
}

{{ application|service("os_linux_default_check_hardware") }}
  host_name                       {{ application.host_name }}
  use                             os_linux_default
  normal_check_interval           15
{% if application.host.hardware == "FJS" %}
  check_command                   check_local!check_fujitsu_primergy.pl -H $HOSTADDRESS$ -C $_SNMPCOMMUNITY$ -v 2
  _SNMPCOMMUNITY                  {{ application.host.snmpcommunity }}
{% endif %}
}
{% endif %}

{#
{{ application|service("os_linux_default_check_uptime") }}
  host_name                       {{ application.host_name }}
  use                             os_linux_default
  check_command                   check_by_ssh!60!$USER10$/lib/nagios/plugins/check_uptime 30        
}
#}

