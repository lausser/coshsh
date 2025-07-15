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
  check_command                   check_nrpe_arg!60!CheckDriveSize!ShowAll MinWarnFree={{ fs.warning }}{{ fs.units }} MinCritFree={{ fs.critical }}{{ fs.units }} Drive={{ fs.path }}:
}
{% endfor %}

{% for nbr in application|neighbor_applications %}
# {{ nbr }}
# name is {{ nbr.name }}
# type is {{ nbr.type }}
# class is {{ nbr.__class__.__name__ }}
{% endfor %}

{% for nbr in application|neighbor_applications_as_tuple %}
# {{ nbr }}
# tname is {{ nbr[1] }}
# ttype is {{ nbr[0] }}
# tclass is {{ nbr[2] }}
{% endfor %}

