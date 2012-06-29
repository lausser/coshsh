{#
 one section for processes
 one section for filesystems
 one section for ports
 one section for urls
 app_{{ application.name }}_default_{{ application.type }}...
 name lohmmonrrdc, type rrdcache -> app_rrdcache_default_lhmmonrrdc_check_proc_rrdcached
#}
{% for port in application.ports %}

{% endfor %}
{% for process in application.processes %}
{{ application|service("app_" + application.type + "_default_" + application.name + "_check_proc_" + process.alias) }}
    host_name                       {{ application.host_name }}
    use                             app
    check_command                   check_by_ssh!60!$USER10$/lib/nagios/plugins/check_procs --ereg-argument-array {{ process.name }} -w {{ process.warning }} -c {{ process.critical }}
}
{% endfor %}

