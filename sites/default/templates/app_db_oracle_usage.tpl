{{ application|service("app_db_oracle_default_" + application.sid + "_check_users") }}
  use                             app_db_oracle_default,app_db_oracle_{{ application.host_name }}_{{ application.sid }}
  check_command                   check_oracle_health!connected-users!--method sqlplus
}

{{ application|service("app_db_oracle_default_" + application.sid + "_check_session_usage") }}
  use                             app_db_oracle_default,app_db_oracle_{{ application.host_name }}_{{ application.sid }}
  check_command                   check_oracle_health!session-usage!--method sqlplus
}

{{ application|service("app_db_oracle_default_" + application.sid + "_check_process_usage") }}
  use                             app_db_oracle_default,app_db_oracle_{{ application.host_name }}_{{ application.sid }}
  check_command                   check_oracle_health!process-usage!--method sqlplus
}

