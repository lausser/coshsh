{% if application.loginsnmpv3 is defined %}
{%   set snmpauth = application.loginsnmpv3.securitylevel + ":" + 
application.loginsnmpv3.securityname + ":" + 
application.loginsnmpv3.authprotocol + ":" + 
application.loginsnmpv3.authkey  %}
{% else %}
{{ application|service("os_ios_default_check_hw") }}
    host_name                       {{ application.host_name }}
    use                             os_ios_default
    check_command                   check_nwc_health_v2!\
        $HOSTADDRESS$!60!{{ application.loginsnmpv2.community }}!\
        hardware-health
}

{{ application|service("os_ios_default_check_mem") }}
    host_name                       {{ application.host_name }}
    use                             os_ios_default,srv-pnp
    check_command 
    check_command                   check_nwc_health_v2!\
        $HOSTADDRESS$!60!{{ application.loginsnmpv2.community }}!\
        memory-usage
}

{{ application|service("os_ios_default_check_cpu") }}
    host_name                       {{ application.host_name }}
    use                             os_ios_default,srv-pnp
    check_command 
    check_command                   check_nwc_health_v2!\
        $HOSTADDRESS$!60!{{ application.loginsnmpv2.community }}!\
        cpu-load
}

{#% if not application.interfaces %#}
{% if False %}
{{ application|service("os_ios_ports_check_usage") }}
    host_name                       {{ application.host_name }}
    use                             os_ios_default,srv-pnp
    check_command 
    check_command                   check_nwc_health_v2!\
        $HOSTADDRESS$!60!{{ application.loginsnmpv2.community }}!\
        interface-usage
}
{% endif %}
{% endif %}

