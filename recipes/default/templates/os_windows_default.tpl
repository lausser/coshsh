{{ application|service("os_windows_default_check_nsclient") }}
  host_name                       {{ application.host_name }}
  use                             os_windows_default
  check_command                   check_nsc_web!30
  _NSCPORT                        {{ application.NSCPORT }}
  _NSCPASSWORD                    {{ application.NSCPASSWORD }}
}

define servicedependency {
  name                             dependency_os_windows_default_check_nsclient_uc_{{ application.host_name }}
  host_name                        {{ application.host_name }}
  service_description              os_windows_default_check_nsclient
  execution_failure_criteria       u,c,p
  notification_failure_criteria    u,c
  dependent_service_description    os_windows_.*,\
                                   !os_windows_default_check_nsclient
}

{{ application|service("os_windows_default_check_uptime") }}
  host_name                       {{ application.host_name }}
  use                             os_windows_default,srv-perf
  max_check_attempts              10
  check_command                   check_nsc_web!30!check_uptime 'warning=uptime<180s' 'critical=uptime<60s'
  _NSCPORT                        {{ application.NSCPORT }}
  _NSCPASSWORD                    {{ application.NSCPASSWORD }}
}

{{ application|service("os_windows_default_check_cpu") }}
  host_name                       {{ application.host_name }}
  use                             os_windows_default,srv-perf
  max_check_attempts              10
  check_command                   check_nsc_web!30!check_cpu 'filter=none' 'warning=load > 80' 'crit=load > 90'
  _NSCPORT                        {{ application.NSCPORT }}
  _NSCPASSWORD                    {{ application.NSCPASSWORD }}
}

{{ application|service("os_windows_default_check_mem") }}
  host_name                       {{ application.host_name }}
  use                             os_windows_default,srv-perf
  check_command                   check_nsc_web!30!check_memory 'filter=none' 'warning=free_pct < 10' 'crit=free_pct < 5'
  _NSCPORT                        {{ application.NSCPORT }}
  _NSCPASSWORD                    {{ application.NSCPASSWORD }}
}

{% if not application.filesystems %}
{{ application|service("os_windows_default_check_drives") }}
  host_name                       {{ application.host_name }}
  use                             os_windows_default,srv-perf
  check_command                   check_nsc_web!30!check_drivesize 'warning=used > 95' 'crit=used > 98' "empty-state=unknown" "filter=type in ('fixed') AND mounted=1 AND name not like '\?\'" "show-all"
  _NSCPORT                        {{ application.NSCPORT }}
  _NSCPASSWORD                    {{ application.NSCPASSWORD }}
}
{% endif %}

