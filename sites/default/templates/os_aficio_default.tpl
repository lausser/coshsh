
{{ application|service("os_aficio_default_check_hw") }}
   host_name                       {{ application.host_name }}
   use                             {{ "os_aficio_default" }}
   check_command                   check_ricoh_printerstate!{{ application.loginsnmpv2.community }}
}

