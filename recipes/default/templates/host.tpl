define host {
{% if host.templates %}
    use                             {{ host.templates }}
{% endif %}
    host_name                       {{ host.host_name }}
    address                         {{ host.address }}
    alias                           {{ host.alias }}
{% if host.parents %}
    parents                         {{ host.parents }}
{% endif %}
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
{% if host.is_bp %}
    check_command                   check_business_process
    notification_options            d,r
{% else %}
    check_command                   check_host_alive
    notification_options            d,u,r
    _SSH_PORT                       {{ host.ports[-1] }}
{% endif %}
{% if host.icon_image %}
    icon_image                      {{ host.icon_image }}
{% endif %}
{{ host|custom_macros() }}}

