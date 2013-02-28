define contact {
  contact_name        {{ contact.contact_name }}
{% if contact.can_submit_commands %}
  can_submit_commands 1
{% else %}
  can_submit_commands 0
{% endif %}
{% if contact.pager %}
  pager               {{ contact.pager }}
{% endif %}
{% if contact.email %}
  email               {{ contact.email }}
{% endif %}
{% if contact.contactgroups %}
  contactgroups       {{ contact.contactgroups }}
{% endif %}
  host_notification_period {{ contact.host_notification_period }}
  service_notification_period {{ contact.service_notification_period }}
  host_notification_options {{ contact.host_notification_options }}
  service_notification_options {{ contact.service_notification_options }}
  host_notification_commands {{ contact.host_notification_commands }}
  service_notification_commands {{ contact.service_notification_commands }}
}

