{{ contact|contact }}
  use {{ contact.templates }}
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
}


