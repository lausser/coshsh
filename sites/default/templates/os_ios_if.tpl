{% if application.loginsnmpv3 is defined %}
{%   set snmpauth = application.loginsnmpv3.securitylevel + ":" +
application.loginsnmpv3.securityname + ":" +
application.loginsnmpv3.authprotocol + ":" +
application.loginsnmpv3.authkey  %}
{% else %}
{% for interface in application.interfaces %}
{{ application|service("os_ios_if_" + interface.name + "_check_usage") }}
    host_name                       {{ application.host_name }}
    use                             os_ios_if,srv-pnp
    check_command                   check_nwc_health_v2!\
        $HOSTADDRESS$!60!{{ application.loginsnmpv2.community }}!\
        interface-usage --name '{{ interface.name }}'
}

{{ application|service("os_ios_if_" + interface.name + "_check_errors") }}
    host_name                       {{ application.host_name }}
    use                             os_ios_if,srv-pnp
    check_command                   check_nwc_health_v2!\
        $HOSTADDRESS$!60!{{ application.loginsnmpv2.community }}!\
        interface-errors --name '{{ interface.name }}'
}

{% endfor %}
{% endif %}
