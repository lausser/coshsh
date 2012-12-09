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
