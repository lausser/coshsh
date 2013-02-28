define contactgroup {
  contactgroup_name        {{ contactgroup.contactgroup_name }}
{% if application.members %}
  members                  {{ contactgroup.members }}
{% endif %}
}

