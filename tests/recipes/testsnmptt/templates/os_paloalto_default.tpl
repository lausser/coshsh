{# brauchen wir fuer den test nicht
{{ application|service("os_paloalto_default_check_......") }}
    host_name                       {{ application.host_name }}
    use                             generic-service
    check_command                   check_neues_command....
}
#}

