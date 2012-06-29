{{ application|service("app_db_oracle_perf_" + application.sid + "_check_databuf") }}
  use                             app_db_oracle_perf,app_db_oracle_{{ application.host_name }}_{{ application.sid }}
  check_command                   check_oracle_health!sga-data-buffer-hit-ratio!--method sqlplus
}

{{ application|service("app_db_oracle_perf_" + application.sid + "_check_redo_io") }}
  use                             app_db_oracle_perf,app_db_oracle_{{ application.host_name }}_{{ application.sid }}
  check_command                   check_oracle_health!redo-io-traffic!--method sqlplus
}

{{ application|service("app_db_oracle_perf_" + application.sid + "_check_switch_interval") }}
  use                             app_db_oracle_perf,app_db_oracle_{{ application.host_name }}_{{ application.sid }}
  check_command                   check_oracle_health!switch-interval!--method sqlplus
}

{{ application|service("app_db_oracle_perf_" + application.sid + "_check_inmemory_sorts") }}
  use                             app_db_oracle_perf,app_db_oracle_{{ application.host_name }}_{{ application.sid }}
  check_command                   check_oracle_health!pga-in-memory-sort-ratio!--method sqlplus
}

{{ application|service("app_db_oracle_perf_" + application.sid + "_check_libcache_gethits") }}
  use                             app_db_oracle_perf,app_db_oracle_{{ application.host_name }}_{{ application.sid }}
  check_command                   check_oracle_health!sga-library-cache-gethit-ratio!--method sqlplus
}

{{ application|service("app_db_oracle_perf_" + application.sid + "_check_libcache_pinhits") }}
  use                             app_db_oracle_perf,app_db_oracle_{{ application.host_name }}_{{ application.sid }}
  check_command                   check_oracle_health!sga-library-cache-pinhit-ratio!--method sqlplus
}

{{ application|service("app_db_oracle_perf_" + application.sid + "_check_dictcache") }}
  use                             app_db_oracle_perf,app_db_oracle_{{ application.host_name }}_{{ application.sid }}
  check_command                   check_oracle_health!sga-dictionary-cache-hit-ratio!--method sqlplus
}

{{ application|service("app_db_oracle_perf_" + application.sid + "_check_sharedpool_free") }}
  use                             app_db_oracle_perf,app_db_oracle_{{ application.host_name }}_{{ application.sid }}
  check_command                   check_oracle_health!sga-shared-pool-free!--method sqlplus
}

{{ application|service("app_db_oracle_perf_" + application.sid + "_check_softparse_ratio") }}
  use                             app_db_oracle_perf,app_db_oracle_{{ application.host_name }}_{{ application.sid }}
  check_command                   check_oracle_health!soft-parse-ratio!--method sqlplus
}

