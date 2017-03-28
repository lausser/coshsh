{{ application|service("os_linux_default_plugin_rollout") }}
  host_name                       {{ application.host_name }}
  use                             os_linux_default
  normal_check_interval           240
  retry_check_interval            10
  max_check_attempts              2
  check_command                   plugin_rollout_linux
  _WORKER                         local
}

{{ application|service("os_linux_default_linux_version") }}
  host_name                       {{ application.host_name }}
  use                             os_linux_default
  normal_check_interval           240
  retry_check_interval            240
  max_check_attempts              1
  check_command                   check_by_ssh!60!( ( grep -sh PRETTY_NAME /etc/*release || head -1 /etc/SuSE-release ) || cat /etc/redhat-release ) && uname -a
}

{{ application|service("os_linux_default_ssh_controlmaster") }}
  host_name                       {{ application.host_name }}
  use                             os_linux_default
  check_command                   check_ssh_controlmaster
}

{{ application|service("os_linux_default_check_load") }}
  host_name                       {{ application.host_name }}
  use                             os_linux_default,srv-perf
  check_command                   check_by_ssh!60!$_HOSTSSHPATHPREFIX$/lib/nagios/plugins/check_load -w 5.0,5.0,5.0 -c 10.0,10.0,10.0 --percpu
}

{#
{{ application|service("os_linux_default_check_memory_and_swap") }}
  host_name                       {{ application.host_name }}
  use                             os_linux_default,srv-perf
  check_command                   check_by_ssh!60!$_HOSTSSHPATHPREFIX$/lib/nagios/plugins/check_mem -w 85 -c 95 -W 70 -C 80
  # Hard state after 2 hours
  retry_check_interval            10
  max_check_attempts              12
}
#}

{{ application|service("os_linux_default_check_swap") }}
  host_name                       {{ application.host_name }}
  use                             os_linux_default,srv-perf
  check_command                   check_by_ssh!60!$_HOSTSSHPATHPREFIX$/lib/nagios/plugins/check_swap -w 15% -c 8%
}

{{ application|service("os_linux_default_check_zombies") }}
  host_name                       {{ application.host_name }}
  use                             os_linux_default,srv-perf
  check_interval                  60
  retry_interval                  10
  check_command                   check_by_ssh!60!$_HOSTSSHPATHPREFIX$/lib/nagios/plugins/check_procs -s Z -w 1 -c 1
}

{{ application|service("os_linux_default_check_process_cron") }}
  use                             os_linux_default
  host_name                       {{ application.host_name }}
  check_command                   check_by_ssh!60!$_HOSTSSHPATHPREFIX$/lib/nagios/plugins/check_procs -w :10 -c 1: --ereg-argument-array='^/usr/sbin/cron|^crond|^cron'
}

{{ application|service("os_linux_default_check_process_syslog") }}
  use                             os_linux_default
  host_name                       {{ application.host_name }}
  check_command                   check_by_ssh!60!$_HOSTSSHPATHPREFIX$/lib/nagios/plugins/check_procs -w :10 -c 1: --ereg-argument-array='^/usr/sbin/rsyslogd|^/sbin/syslog-ng|^rsyslogd|^syslogd|^/sbin/rsyslogd'
}


{#
{{ application|service("os_linux_if_check_eth0") }}
  host_name                       {{ application.host_name }}
  use                             os_linux_default,srv-perf
  check_command                   check_by_ssh!60!PERL5LIB=$_HOSTSSHPATHPREFIX$/lib/perl5 $_HOSTSSHPATHPREFIX$/lib/nagios/plugins/check_nwc_health \
      --hostname localhost \
      --mode interface-health \
      --name eth0 \
      --units Mbit \
      --servertype linuxlocal
}
#}

define servicedependency {
  name                             dependency_os_linux_default_ssh_controlmaster_uc_{{ application.host_name }}
  host_name                        {{ application.host_name }}
  service_description              os_linux_default_ssh_controlmaster
  execution_failure_criteria       u,c,p
  notification_failure_criteria    u,c
  dependent_service_description    os_linux_default_plugin_rollout,\
                                   os_linux_default_linux_version
}

define servicedependency {
  name                             dependency_os_linux_default_plugin_rollout_uc_{{ application.host_name }}
  host_name                        {{ application.host_name }}
  service_description              os_linux_default_plugin_rollout
  execution_failure_criteria       u,w,c,p
  notification_failure_criteria    u,c
  dependent_service_description    os_linux_.*,\
                                   !os_linux_default_linux_version,\
                                   !os_linux_default_plugin_rollout,\
                                   !os_linux_default_ssh_controlmaster
}

{% if not application.filesystems %}
{{ application|service("os_linux_default_check_disks") }}
  use                             os_linux_default
  host_name                       {{ application.host_name }}
  check_command                   check_by_ssh!60!$_HOSTSSHPATHPREFIX$/lib/nagios/plugins/check_disk -w 5% -c 2% -e -A -l -x '/dev' -x '/dev/shm' -i '/boot' -x '/home' -i '/var/lib/docker' -i '/run/docker' -i '/data.*/docker.*' -i 'net:'
  check_interval                  30
}
{% endif %}
