#
# Deliberately broken: the "{% if {#" below is a Jinja2 syntax error, so this
# template fails at LOAD time with TemplateSyntaxError. Modelled on
# tests/recipes/test10/templates_err/app_db_mysql_default.tpl, which is the
# existing exemplar for this failure kind. Do not "fix" it.
#
{% if {# this is a syntax error
define service {
  host_name                       {{ host.host_name }}
  service_description             renderr_broken_check
}
