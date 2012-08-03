define contactgroup {
  contactgroup_name        {{ application.contactgroup_name }}
{% if application.members %}
  members                  {{ application.members }}
{% endif %}
}

