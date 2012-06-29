# http://www.itefix.no/i2/check_ad
{{ application|service("") }}
{% if application.host.re_match(r'2008') %}
  check_command  check_ad!--dc --noeventlog --dfsr
{% else %}
  check_command  check_ad!--dc --noeventlog
{% endif %}
}
