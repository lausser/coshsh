define service {
  host_name                       {{ host.host_name }}
  service_description             renderr_good_check
  use                             generic-service
  check_command                   check_dummy!0!this_is_part_of_the_coshsh_unittest
}
