define host {
{% if host.templates %}
    use                             {{ host.templates }}
{% endif %}
    host_name                       {{ host.host_name }}
    address                         {{ host.address }}
    alias                           {{ host.alias }}
{% if host.hostgroups %}
    hostgroups                      {{ host.hostgroups }}
{% endif %}
{% if host.contact_groups %}
    contact_groups                  {{ host.contact_groups }}
{% endif %}
{% if host.check_period %}
    check_period                    {{ host.check_period }}
{% endif %}
{% if host.notification_period %}
    notification_period             {{ host.notification_period }}
{% endif %}
    check_command                   check_host_alive
    _SSH_PORT                       {{ host.ports[-1] }}
}

{#todo
contactgroups only? use both contactgroups and contacts?
#}

