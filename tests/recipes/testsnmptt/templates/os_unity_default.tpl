{# hier kommt der check mit dem api
{{ application|service("os_unity_default_check_......") }}
    host_name                       {{ application.host_name }}
    use                             generic-service
    check_command                   check_neues_command....
}
#}

