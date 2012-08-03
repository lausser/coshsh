{{ application|service("os_windows_default_check_unittest") }}
  host_name                       {{ application.host_name }}
  use                             os_windows_default
  check_command                   check_nrpe_arg!60!this_is_part_of_the_coshsh_unittest
}

{{ application|service("os_windows_default_check_nsclient") }}
  host_name                       {{ application.host_name }}
  use                             os_windows_default
  check_command                   check_nrpe_arg!60!checkUpTime!MinWarn=5m MinCrit=1m
}

{{ application|service("os_windows_default_check_cpu") }}
  host_name                       {{ application.host_name }}
  use                             os_windows_default,srv-pnp
  max_check_attempts              10
  check_command                   check_nrpe_arg!60!checkCPU!warn=80 crit=90 time=5m time=1m time=30s
}

{{ application|service("os_windows_default_check_mem") }}
  host_name                       {{ application.host_name }}
  use                             os_windows_default,srv-pnp
  check_command                   check_nrpe_arg!60!checkMem!MaxWarn=80% MaxCrit=90% ShowAll=long type=physical type=virtual type=paged
}

{{ application|service("os_windows_default_check_autosvc") }}
  host_name                       {{ application.host_name }}
  use                             os_windows_default
  check_command                   check_nrpe_arg!60!CheckServiceState!CheckAll
}

{#
{{ application|service("os_windows_default_check_ntp") }}
  host_name                       {{ application.host_name }}
  use                             os_windows_default
  check_command                   windows-check_time!3600!360000
}
#}

define servicedependency {
  name                             dependency_os_windows_default_check_nsclient_uc_{{ application.host_name }}
  host_name                        {{ application.host_name }}
  service_description              os_windows_default_check_nsclient
  execution_failure_criteria       u,c
  notification_failure_criteria    u,c
  dependent_service_description    os_windows_.*,\
                                   !os_windows_default_check_nsclient
}
