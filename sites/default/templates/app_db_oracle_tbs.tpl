{% for tbs in application.tablespaces %}
{{ application|service("app_db_oracle_tbs_" + application.sid + "_" + tbs.name + "_check_free") }}
  use                             app_db_oracle_tbs,app_db_oracle_{{ application.host_name }}_{{ application.sid }}
  check_command                   check_oracle_health!tablespace-free!--name {{ tbs.name }} --warning {{ tbs.warning }}: --critical {{ tbs.critical }}: --method sqlplus
  check_interval                  30
}
{% endfor %}

{{ application|service("app_db_oracle_tbs_" + application.sid + "_check_maxdatafiles") }}
  use                             app_db_oracle_tbs,app_db_oracle_{{ application.host_name }}_{{ application.sid }}
  check_command                   check_oracle_health!datafiles-existing!--warning 90 --critical 95 --method sqlplus
  check_interval                  60
}

{{ application|service("app_db_oracle_tbs_" + application.sid + "_check_fragmentation") }}
  use                             app_db_oracle_tbs,app_db_oracle_{{ application.host_name }}_{{ application.sid }}
  check_command                   check_oracle_health!tablespace-fragmentation!--method sqlplus
  check_interval                  60
}

{{ application|service("app_db_oracle_tbs_" + application.sid + "_check_remaining") }}
  use                             app_db_oracle_tbs,app_db_oracle_{{ application.host_name }}_{{ application.sid }}
  check_command                   check_oracle_health!tablespace-remaining-time!--method sqlplus
  check_interval                  60
}

