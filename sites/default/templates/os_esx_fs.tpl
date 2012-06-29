{% for fs in filesystems %}
# fs.path
# fs.warn
# fs.crit
{{ application|service("os_esx_fs_check_{{ fs }}") }}
    host_name                       {{ application.host_name }}
}
{% endfor %}

