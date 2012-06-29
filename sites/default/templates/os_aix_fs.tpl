{#
fs.path
fs.warning
fs.critical
fs.units
#}
{% for fs in application.filesystems %}

{{ application|service("os_aix_fs_check_{{ fs.path }}") }}
    host_name                       {{ application.host_name }}
{% if fs.units == "%" %}
    check_command                   check_by_ssh!60!$USER10$/lib/nagios/plugins/check_disk --warning {{ fs.warning }}% --critical {{ fs.critical }}% --path {{ fs.path }}
{% else %}
    check_command                   check_by_ssh!60!$USER10$/lib/nagios/plugins/check_disk --warning {{ fs.warning }} --critical {{ fs.critical }} --units {{ fs.units }} --path {{ fs.path }}
{% endif %}
}
{% endfor %}

