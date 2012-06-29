#
# Template with unique attributes for the database {{ application.sid }}
#
define service {
    register               0
    name                   app_db_oracle_{{ application.host_name }}_{{ application.sid }}
    host_name              {{ application.host_name }}
    servicegroups          oracle_{{ application.host_name }}_{{ application.sid }}
#    _oracle_sid            {{ application.sid }}
{% if application.ports %}
    _oracle_sid            {{ application.host_name }}:{{ application.ports[0].port }}/{{ application.sid }}
{% else %}
    _oracle_sid            {{ application.sid }}
{% endif %}
    _oracle_user           {{ application.login.username }}
    _oracle_pass           {{ application.login.password }}
    use                    srv-pnp
}

#
# A servicegroup which holds all services of the {{ application.name }} database
#
define servicegroup {
    servicegroup_name      oracle_{{ application.host_name }}_{{ application.sid }}
}

{{ application|service("app_db_oracle_default_" + application.sid + "_check_login") }}
  use                             app_db_oracle_default,app_db_oracle_{{ application.host_name }}_{{ application.sid }}
  check_command                   check_oracle_health!connection-time!--method sqlplus
}

{% if application.tags|length > 0 %}
define servicedependency {
  name                         dependency_{{ application.host_name }}_{{ application.sid }}_uc
  host_name                    {{ application.host_name }}
  execution_failure_criteria      u,c
  notification_failure_criteria   u,c
  register                        0
}

define servicedependency {
  use                          dependency_{{ application.host_name }}_{{ application.sid }}_uc
  service_description          app_db_oracle_default_{{ application.sid }}_check_login
  dependent_service_description \
      app_db_oracle_.*_{{ application.sid }}_.*,!app_db_oracle_default_{{ application.sid }}_check_login
}
{% endif %}
