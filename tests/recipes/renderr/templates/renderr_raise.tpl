#
# Fails at RENDER time, not at load time. This template is syntactically valid,
# so Jinja2 compiles it happily; the call below is what blows up, because
# host.this_attribute_does_not_exist is Undefined and Undefined is not callable.
#
# WHY a template is needed that fails this late: coshsh counts three failure
# paths, and this is the only one reachable *after* a template has compiled --
# the "except Exception" around template.render() in coshsh/item.py. A template
# with a syntax error never gets that far, so it cannot stand in for this case.
# Do not "fix" it.
#
define service {
  host_name                       {{ host.host_name }}
  service_description             renderr_raise_check
  check_command                   {{ host.this_attribute_does_not_exist() }}
}
