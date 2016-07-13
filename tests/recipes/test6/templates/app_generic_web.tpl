 {#
  ------------------------------------------------------------------------------
  * URL-Check für APP's
  ------------------------------------------------------------------------------
 #}

 {% for url in application.urls %}
 {#### HTTP / HTTPS ####}
   {% if url.scheme is re_match("htt*") %}
     {# HTTPS #}
     {% set ssl = '--ssl' if url.scheme == "https" else "" %}
     {# PATH #}
     {% set path = url.path if url.path else "/" %}
     {# QUERY #}
     {% set query = "?" + url.query if url.query else "" %}
     {# FRAGMENT #}
     {% set fragment = "#" + url.fragment if url.fragment else "" %}
     {# PORT #}
     {% set port = "-p " +  url.port|string if url.port else "" %}
     {# LOGIN #}
     {% set login = "--authorization '" + url.username + ":" + url.password + "'" if url.username and url.password else "" %}
     {# EXPECT #}
     {% set expect = "-e " + url.url_expect if url.url_expect else "" %}
     {# FLEX #}
     {% set flex = url.url_flexible if url.url_flexible else "" %}

 {{ application|service("os_appliance_default_" + (loop.index|string) + "_" + application.name + "_check_" + url.scheme + "_response") }}
   host_name                       {{ application.host_name }}
   use                             app_web_apache_default,srv-perf
 {% if application.proxy %}
   check_command                   check_http_generic!60!{{ application.proxy }}!{{ url.hostname }}!'{{ url.scheme }}://{{ url.hostname }}{{ path }}{{ query }}{{ fragment }}'!{{ url.warning }}!{{ url.critical }}!{{ port }} {{ expect }} {{ flex }}
 {% else %}
   check_command                   check_http_generic!60!$HOSTADDRESS$!{{ url.hostname }}!{{ path }}{{ query }}{{ fragment }}!{{ url.warning }}!{{ url.critical }}!{{ ssl }}     {{ port }} {{ login }} {{ expect }} {{ flex }}
 {% endif %}
 }
 {% endif %}
 {% endfor %}

