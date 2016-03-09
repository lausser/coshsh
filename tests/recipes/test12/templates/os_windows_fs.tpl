{#
fs.path
fs.warning
fs.critical
fs.units
#}
{% for fs in application.filesystems %}

{{ application|service("os_windows_fs_check_" + fs.path) }}
  host_name                       {{ application.host_name }}
  use                             os_windows,srv-pnp
  check_interval                  15
  check_command                   check_nrpe_arg!60!CheckDriveSize{{ fs.path }}
}
{% endfor %}

