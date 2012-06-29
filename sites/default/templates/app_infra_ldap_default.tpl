{% for url in application.urls %}
{% set basedn = url.path | re_sub("^/", "", "i", 1) %}
{% set origbasedn = basedn %}
{% set basedn = basedn | re_sub("=", "_") %}

{{ application|service("app_infra_ldap_default_check_connect_" + basedn) }}
    host_name                       {{ application.host_name }}
{% if url.scheme == "ldaps" %}
    check_command                   check_ldaps_connect!{{ url.hostname }}!{{ origbasedn }}!{{ url.warning }}!{{ url.critical }}
{% else %}
    check_command                   check_ldap_connect!{{ url.hostname }}!{{ origbasedn }}!{{ url.warning }}!{{ url.critical }}
{% endif %}
    use app_infra_ldap_default
}

{% endfor %}

