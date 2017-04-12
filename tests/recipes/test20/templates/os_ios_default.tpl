{% set protocol = application.loginsnmpv2.protocol %}
# check_nwc_health_v{{ protocol }}
{{ application|service("os_ios_default_check_uptime") }}
    host_name                       {{ application.host_name }}
    use                             os_ios_default
    check_command                   check_nwc_health_v{{ protocol }}!\
        $HOSTADDRESS$!30!$_HOSTCOMMUNITY$!\
        uptime!--warning 0: --critical 0:
}

{{ application|service("os_ios_default_check_hardware") }}
    host_name                       {{ application.host_name }}
    use                             os_ios_default,srv-perf
    check_command                   check_nwc_health_v{{ protocol }}!\
        $HOSTADDRESS$!60!$_HOSTCOMMUNITY$!\
        hardware-health
    check_interval                  30
}

{{ application|service("os_ios_default_check_memory") }}
    host_name                       {{ application.host_name }}
    use                             os_ios_default,srv-perf
    check_command 
    check_command                   check_nwc_health_v{{ protocol }}!\
        $HOSTADDRESS$!30!$_HOSTCOMMUNITY$!\
        memory-usage!--warning 95 --critical 95
}

{{ application|service("os_ios_default_check_cpu") }}
    host_name                       {{ application.host_name }}
    use                             os_ios_default,srv-perf
    check_command 
    check_command                   check_nwc_health_v{{ protocol }}!\
        $HOSTADDRESS$!30!$_HOSTCOMMUNITY$!\
        cpu-load!--warning 95 --critical 95
}

{% if not "cisco_wlc" in application.host.hostgroups %}
{{ application|service("os_ios_default_check_chassis") }}
    host_name                       {{ application.host_name }}
    use                             os_ios_default,srv-perf
    check_command                   check_nwc_health_v{{ protocol }}!\
        $HOSTADDRESS$!60!$_HOSTCOMMUNITY$!\
        chassis-hardware-health --mitigation ok
    check_interval                  30
}
{% endif %}

define servicedependency {
  name                             dependency_os_ios_default_check_uptime{{ application.host_name }}
  host_name                        {{ application.host_name }}
  service_description              os_ios_default_check_uptime
  # not u,c (u usually means: no snmp connect)
  execution_failure_criteria       u,p
  notification_failure_criteria    u
  dependent_service_description    os_ios_.*,\
                                   !os_ios_default_check_uptime
}

{#
{{ application|service("os_ios_default_check_wireless") }}
    host_name                       {{ application.host_name }}
    use                             os_ios_default
    check_command                   check_nwc_health_v{{ protocol }}!\
        $HOSTADDRESS$!30!$_HOSTCOMMUNITY$!\
        accesspoint-status
    # {{ application.type }}
}
#}
