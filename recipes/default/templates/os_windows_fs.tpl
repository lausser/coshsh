{#
fs.path
fs.warning
fs.critical
fs.units
#}
{% for fs in application.filesystems %}

{{ application|service("os_windows_fs_check_" + fs.path) }}
  host_name                       {{ application.host_name }}
  use                             os_windows,srv-perf
  check_interval                  15
  check_command                   check_nsc_web!30!check_drivesize 'warning=used > {{ fs.warning }}' 'crit=used > {{ fs.critical }}' "drive={{ fs.path }}" "show-all"
  {{ application|custom_macros }}
{#
example 0.5.0
check_drivesize show-all "warn=free < 5%" "crit=free < 2%" drive=c:
#}
}
{% endfor %}

