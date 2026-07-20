{# coshsh Jinja2 template skeleton.
   File name conventions used by template_rules:
     host.tpl                    — emits host objects (referenced via |host filter)
     os_<type>_default.tpl       — base OS template
     app_<flavour>_<x>.tpl       — application-specific service definitions
   Templates live in a directory listed in the recipe's templates_dir.

   Scope variables in services/app templates:
     application — the current Application instance (re-blessed subclass)
     host        — application.host
     contact     — for contact templates only
#}

{# Example: a host.tpl that emits a Nagios host object #}
define host {
    use                     {{ host.os_type|default("generic-host") }}
    host_name               {{ host.host_name }}
    address                 {{ host.address }}
    {%- if host.alias %}
    alias                   {{ host.alias }}
    {%- endif %}
    {%- if host.hostgroups %}
    hostgroups              {{ host.hostgroups }}
    {%- endif %}
    {%- if host.contact_groups %}
    contact_groups          {{ host.contact_groups|join(",") }}
    {%- endif %}
    {{ host|custom_macros }}
}

{# Example: services rendered via |service for each filesystem #}
{% for fs in application.filesystems %}
{{ application|service("check_disk_" ~ (fs.path|re_sub("[^a-zA-Z0-9]","_"))) }}
    use                     generic-service
    check_command           check_disk!{{ fs.warning }}!{{ fs.critical }}!{{ fs.path }}
}
{% endfor %}

{# Example: URL checks #}
{% for url in application.urls %}
{{ application|service("check_url_" ~ url.name) }}
    use                     generic-service
    check_command           check_http!-H {{ host.address }} -u {{ url.url|rfc3986 }} --expect={{ url.expect|default("200") }}
}
{% endfor %}

{# Useful filter examples:
     {{ host       |host }}                        full host block
     {{ application|service("name") }}             "define service { ... host_name ... service_description name"
     {{ contact    |contact }}                     full contact block
     {{ host       |custom_macros }}               emits `_KEY value` lines from host.macros dict
     {{ "abc-def"  |re_sub("-", "_") }}            → "abc_def"
     {{ "a&b"      |rfc3986 }}                     URL-encode
     {{ "."        |re_escape }}                   regex-escape
   Loops:
     {% for app in application|neighbor_applications %}
       {# sibling apps on the same host #}
     {% endfor %}
#}
