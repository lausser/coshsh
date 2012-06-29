{{ application|service("app_mqs_gmw_default_check_proc") }}
    host_name                       {{ application.host_name }}
{% if application.name %}
{% elif application.id > 1 %}
{% else %}
{% endif %}
    use                             app_mqs_gmw_default
{% for process in application.processes %}
    check_command                   check_by_ssh!60!$USER10$/lib/nagios/plugins/check_procs --ereg-argument-array {{ process.name }} -w {{ process.warning }} -c {{ process.critical }}
{% endfor %}
}

