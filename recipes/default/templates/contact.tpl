define contact {
  contact_name        {{ application.contact_name }}
{% if application.can_submit_commands %}
  can_submit_commands 1
{% else %}
  can_submit_commands 0
{% endif %}
{% if application.pager %}
  pager               {{ application.pager }}
{% endif %}
{% if application.email %}
  email               {{ application.email }}
{% endif %}
{% if application.contactgroups %}
  contactgroups       {{ application.contactgroups }}
{% endif %}
  host_notification_period {{ application.host_notification_period }}
  service_notification_period {{ application.service_notification_period }}
  host_notification_options {{ application.host_notification_options }}
  service_notification_options {{ application.service_notification_options }}
  host_notification_commands {{ application.host_notification_commands }}
  service_notification_commands {{ application.service_notification_commands }}
}

