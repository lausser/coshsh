define contactgroup {
  contactgroup_name        {{ contactgroup.contactgroup_name }}
{% if contactgroup.members %}
  members                  {{ contactgroup.members }}
{% endif %}
}

