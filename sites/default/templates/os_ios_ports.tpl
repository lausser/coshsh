{% if application.loginsnmpv3 is defined %}
{%   set snmpauth = application.loginsnmpv3.securitylevel + ":" +
application.loginsnmpv3.securityname + ":" +
application.loginsnmpv3.authprotocol + ":" +
application.loginsnmpv3.authkey  %}
{% else %}
{% for port in application.ports %}
{{ application|service("os_ios_ports_" + + "_check_usage") }}
    host_name                       {{ application.host_name }}
    use                             os_ios_ports
    check_command                   check_nwc_health_v2!\
        $HOSTADDRESS$!60!{{ application.loginsnmpv2.community }}!\
        interface-usage --name {{ port }}
}
{% endfor %}
{% endif %}
