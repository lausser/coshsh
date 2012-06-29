{% for url in application.urls %}
{{ application|service("app_web_apache_default_" + application.name + "_check_http_response") }}
   host_name                       {{ application.host_name }}
   use                             app_web_apache_default
{% if application.login %}
   check_command                   check_http_connect_auth!60!{{ url.url }}!{{ url.warning }}!{{ url.critical }}!{{ application.login.username }}!{{ application.login.password }}
{% else %}
{% if url.url_expect %}
   check_command                   check_http_content!60!{{ url.url }}!{{ url.warning }}!{{ url.critical }}!{{ url.url_expect }}
{% else %}
   check_command                   check_http_connect!60!{{ url.url }}!{{ url.warning }}!{{ url.critical }}
{% endif %}
{% endif %}
}
{% endfor %}
