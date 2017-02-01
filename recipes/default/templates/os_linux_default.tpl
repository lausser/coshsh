{{ application|service("os_linux_default_check_controlmaster") }}
  use                             os_linux_default
  host_name                       {{ application.host_name }}
  max_check_attempts              1
  check_interval                  2
  check_command                   check_ssh_controlmaster
}

define servicedependency {
  name                             dependency_os_linux_default_check_controlmast
er_uc_{{ application.host_name }}
  host_name                        {{ application.host_name }}
  service_description              os_linux_default_check_controlmaster
  execution_failure_criteria       u,c,p
  notification_failure_criteria    u,c
  dependent_service_description    os_linux_.*,\
                                   !os_linux_default_check_controlmaster
}

{{ application|service("os_linux_default_check_crond") }}
  use                             os_linux_default
  host_name                       {{ application.host_name }}
{% if "sles" in application.type %}
  check_command                   check_by_ssh!60!./{{ application.host.environment }}/lib/nagios/plugins/check_procs -w :100 -c 1: -C cron
{% else %}
  check_command                   check_by_ssh!60!./{{ application.host.environment }}/lib/nagios/plugins/check_procs -w :100 -c 1: -C crond
{% endif %}
}

{{ application|service("os_linux_default_check_mailq") }}
  use                             os_linux_default
  host_name                       {{ application.host_name }}
  check_interval                  60
  retry_interval                  10
  check_command                   check_by_ssh!180!PERL5LIB=./{{ application.host.environment }}/lib/nagios/plugins ./{{ application.host.environment }}/lib/nagios/plugins/check_mailq -w 1 -c 100 -t 120
}

{{ application|service("os_linux_default_check_zombies") }}
  use                             os_linux_default
  host_name                       {{ application.host_name }}
  check_interval                  60
  retry_interval                  10
  check_command                   check_by_ssh!60!./{{ application.host.environment }}/lib/nagios/plugins/check_procs -w 20 -c 40 -p 1 -s Z
}

{{ application|service("os_linux_default_check_swap") }}
  use                             os_linux_default
  host_name                       {{ application.host_name }}
  check_command                   check_by_ssh!60!./{{ application.host.environment }}/lib/nagios/plugins/check_swap -w 5% -c 1%
  check_interval                  30
}

{% if not application.filesystems %}
{{ application|service("os_linux_default_check_disks") }}
  use                             os_linux_default
  host_name                       {{ application.host_name }}
  check_command                   check_by_ssh!60!./{{ application.host.environment }}/lib/nagios/plugins/check_disk -w 15% -c 10%
  check_interval                  30
}
{% endif %}
