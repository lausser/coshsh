#
# Template with unique attributes for the database {{ application.name }}
#
define service {
    register               0
    name                   app_db_mysql_{{ application.name }}
    host_name              {{ application.host_name }}
    servicegroups          mysql_{{ application.name }}
    _mysql_host            {{ application.host_name }}
    _mysql_port            {{ application.port }}
    _mysql_socket          {{ application.socket }}
{% if application.login %}
    _mysql_user            {{ application.login.username }}
    _mysql_pass            {{ application.login.password }}
{% else %}
    _mysql_user            {{ "" }}
    _mysql_pass            {{ "" }}
{% endif %}
    use                    srv-pnp
}

#
# A servicegroup which holds all services of the {{ application.name }} database
#
define servicegroup {
    servicegroup_name      mysql_{{ application.name }}
}

#
# Templates which merge mysql templates with {{ application.name }} attributes
#
define service {
    register               0
    name                   app_db_mysql_logs_{{ application.name }}
    use                    app_db_mysql_logs,app_db_mysql_{{ application.name }}
}

define service {
    register               0
    name                   app_db_mysql_default_{{ application.name }}
    use                    app_db_mysql_default,app_db_mysql_{{ application.name }}
}

define service {
    register               0
    name                   app_db_mysql_tbs_{{ application.name }}
    use                    app_db_mysql_tbs,app_db_mysql_{{ application.name }}
}

define service {
    register               0
    name                   app_db_mysql_perf_{{ application.name }}
    use                    app_db_mysql_perf,app_db_mysql_{{ application.name }}
}

#
# The services of service profile app_db_mysql_default
#
{{ application|service("app_db_mysql_default_" + application.name + "_check_login") }}
    use                    app_db_mysql_default_{{ application.name }}
    check_command          check_mysql_health_{{ application.access }}!connection-time
}

{{ application|service("app_db_mysql_default_" + application.name + "_check_uptime") }}
    use                    app_db_mysql_default_{{ application.name }}
    check_command          check_mysql_health_{{ application.access }}!uptime
}

#
# The services of service profile app_db_mysql_perf
#
{{ application|service("app_db_mysql_perf_" + application.name + "_check_threads_conn") }}
    use                    app_db_mysql_perf_{{ application.name }}
    check_command          check_mysql_health_{{ application.access }}!threads-connected
}

{{ application|service("app_db_mysql_perf_" + application.name + "_check_threadcache_hits") }}
    use                    app_db_mysql_perf_{{ application.name }}
    check_command          check_mysql_health_{{ application.access }}!threadcache-hitrate
}

{{ application|service("app_db_mysql_perf_" + application.name + "_check_index_usage") }}
    use                    app_db_mysql_perf_{{ application.name }}
    check_command          check_mysql_health_{{ application.access }}!index-usage
}

{{ application|service("app_db_mysql_perf_" + application.name + "_check_qcache_hits") }}
    use                    app_db_mysql_perf_{{ application.name }}
    check_command          check_mysql_health_{{ application.access }}!qcache-hitrate
}

{{ application|service("app_db_mysql_perf_" + application.name + "_check_qcache_prunes") }}
    use                    app_db_mysql_perf_{{ application.name }}
    check_command          check_mysql_health_{{ application.access }}!qcache-lowmem-prunes          
}

{{ application|service("app_db_mysql_perf_" + application.name + "_check_myis_kcache_hits") }}
    use                    app_db_mysql_perf_{{ application.name }}
    check_command          check_mysql_health_{{ application.access }}!myisam-keycache-hitrate       
}

{{ application|service("app_db_mysql_perf_" + application.name + "_check_inno_bpool_hits") }}
    use                    app_db_mysql_perf_{{ application.name }}
    check_command          check_mysql_health_{{ application.access }}!innodb-bufferpool-hitrate     
}

{{ application|service("app_db_mysql_perf_" + application.name + "_check_inno_bpool_waits") }}
    use                    app_db_mysql_perf_{{ application.name }}
    check_command          check_mysql_health_{{ application.access }}!innodb-bufferpool-wait-free   
}

{{ application|service("app_db_mysql_perf_" + application.name + "_check_inno_log_waits") }}
    use                    app_db_mysql_perf_{{ application.name }}
    check_command          check_mysql_health_{{ application.access }}!innodb-log-waits
}

{{ application|service("app_db_mysql_perf_" + application.name + "_check_tcache_hits") }}
    use                    app_db_mysql_perf_{{ application.name }}
    check_command          check_mysql_health_{{ application.access }}!tablecache-hitrate
}

{{ application|service("app_db_mysql_perf_" + application.name + "_check_table_lock_cont") }}
    use                    app_db_mysql_perf_{{ application.name }}
    check_command          check_mysql_health_{{ application.access }}!table-lock-contention         
}

{{ application|service("app_db_mysql_perf_" + application.name + "_check_slow_queries") }}
    use                    app_db_mysql_perf_{{ application.name }}
    check_command          check_mysql_health_{{ application.access }}!slow-queries
}

{{ application|service("app_db_mysql_perf_" + application.name + "_check_temp_tables") }}
    use                    app_db_mysql_perf_{{ application.name }}
    check_command          check_mysql_health_{{ application.access }}!tmp-disk-tables
}

{{ application|service("app_db_mysql_perf_" + application.name + "_check_longrunners") }}
    use                    app_db_mysql_perf_{{ application.name }}
    check_command          check_mysql_health_{{ application.access }}!long-running-procs
}

#
# Dependencies. If database login is not possible, then
# do not execute any other check. (use_regexp_matching=1)
#
define servicedependency {
    name                            dep_app_db_mysql_{{ application.name }}
    register                        0
}

define servicedependency {
    name                             dependency_{{ application.host_name }}_connection_uc         
    host_name                        {{ application.host_name }}
    service_description              app_db_mysql_default_{{ application.name }}_check_login   
    execution_failure_criteria       u,c
    notification_failure_criteria    u,c
    dependent_service_description    app_db_mysql_default_{{ application.name }}_check_uptime,app_db_mysql_perf_{{ application.name }}_*
}

