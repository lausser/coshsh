{{ application|service("app_infra_dns_default_check_named") }}
    use                             app_infra_dns_default
    host_name                       {{ application.host_name }}
    check_command                   check_by_ssh!60!$USER10$/lib/nagios/plugins/check_procs -w :1 -c 1: -C named
}

{% for url in application.urls %}
{% set basedn = url.path | re_sub("^/", "", "i", 1) %}
{% set origbasedn = basedn %}
{% set basedn = basedn | re_sub("=", "_") %}

{% if basedn == application.host_name %}
{{ application|service("app_infra_dns_default_check_self") }}
    use                             app_infra_dns_default
    host_name                       {{ application.host_name }}
    check_command                   check_dns_server!$HOSTADDRESS$!1!2!$HOSTNAME$
}
{% else %}
{{ application|service("app_infra_dns_default_check_" + basedn) }}
    use                             app_infra_dns_default
    host_name                       {{ application.host_name }}
    check_command                   check_dns_server!$HOSTADDRESS$!1!2!{{ url.url }}
}
{% endif %}
{% endfor %}


