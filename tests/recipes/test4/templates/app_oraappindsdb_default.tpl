{{ application|service("check_oracledings") }}
  check_command check_oracle_health!{{ recipe.datasources[0].sid }}!{{ recipe.datasources[0].username }}!{{ recipe.datasources[0].password|rfc3986() }} --sql "select 1 from dual"
}
