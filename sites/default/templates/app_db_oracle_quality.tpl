{{ application|service("app_db_oracle_default_" + application.sid + "_check_invalid_objects") }}
  use                             app_db_oracle_default,app_db_oracle_{{ application.host_name }}_{{ application.sid }}
  check_command                   check_oracle_health!invalid-objects!--method sqlplus
}

{{ application|service("app_db_oracle_default_" + application.sid + "_check_stale_statistics") }}
  use                             app_db_oracle_default,app_db_oracle_{{ application.host_name }}_{{ application.sid }}
  check_command                   check_oracle_health!stale-statistics!--method sqlplus
}

