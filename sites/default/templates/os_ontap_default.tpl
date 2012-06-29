
{% if application.loginsnmpv3 is defined %}
{%   set snmpauth = application.loginsnmpv3.securitylevel + ":" +
application.loginsnmpv3.securityname + ":" +
application.loginsnmpv3.authprotocol + ":" +
application.loginsnmpv3.authkey  %}
{% else %}

{{ application|service("os_ontap_default_check_hw") }}
  host_name                       {{ application.host_name }}
  use                             os_ontap_default
  check_command                   check_naf_v2!$HOSTADDRESS$!60!{{ application.loginsnmpv2.community }}!environment
}

{{ application|service("os_ontap_default_check_disks") }}
  host_name            {{ application.host_name }}
  use                  os_ontap_default,srv-pnp
  check_command        check_naf_v2!$HOSTADDRESS$!60!{{ application.loginsnmpv2.community }}!disk,failed
}

{{ application|service("os_ontap_default_check_cpu") }}
  host_name            {{ application.host_name }}
  use                  os_ontap_default,srv-pnp
  check_command        check_naf_v2!$HOSTADDRESS$!60!{{ application.loginsnmpv2.community }}!cpu
}

{{ application|service("os_ontap_default_check_cluster") }}
  host_name            {{ application.host_name }}
  use                  os_ontap_default
  check_command        check_naf_v2!$HOSTADDRESS$!60!{{ application.loginsnmpv2.community }}!cluster
}

{{ application|service("os_ontap_default_check_ops") }}
  host_name            {{ application.host_name }}
  use                  os_ontap_default,srv-pnp
  check_command        check_naf_v2!$HOSTADDRESS$!60!{{ application.loginsnmpv2.community }}!ops
}

{{ application|service("os_ontap_default_check_nvram") }}
  host_name            {{ application.host_name }}
  use                  os_ontap_default
  check_command        check_naf_v2!$HOSTADDRESS$!60!{{ application.loginsnmpv2.community }}!nvram
}

{{ application|service("os_ontap_default_check_io") }}
  host_name            {{ application.host_name }}
  use                  os_ontap_default,srv-pnp
  check_command        check_naf_v2!$HOSTADDRESS$!60!{{ application.loginsnmpv2.community }}!io
}

{% endif %}

