{% if application.loginsnmpv3 is defined %}
{%   set snmpauth = application.loginsnmpv3.securitylevel + ":" +
application.loginsnmpv3.securityname + ":" +
application.loginsnmpv3.authprotocol + ":" +
application.loginsnmpv3.authkey  %}
{% else %}

{% for volume in application.volumes %}
{{ application|service("os_ontap_fs_check_vol_"+ volume.name) }}
   host_name                       {{ application.host_name }}
   use                             os_ontap_fs,srv-pnp
   check_interval                  15
   retry_interval                  15
   check_command                   check_naf_v2!$HOSTADDRESS$!60!{{ application.loginsnmpv2.community }}!vol_data,{{ volume.name }},{{ volume.warning}}{{ volume.units}},{{ volume.critical }}{{ volume.units }}
}

{{ application|service("os_ontap_fs_check_volsnap_"+ volume.name) }}
   host_name                       {{ application.host_name }}
   use                             os_ontap_fs,srv-pnp
   check_interval                  15
   retry_interval                  15
   check_command                   check_naf_v2!$HOSTADDRESS$!60!{{ application.loginsnmpv2.community }}!vol_snap,{{ volume.name }},{{ volume.warning}}{{ volume.units}},{{ volume.critical }}{{ volume.units }}
}

{{ application|service("os_ontap_fs_check_inodes_"+ volume.name) }}
   host_name                       {{ application.host_name }}
   use                             os_ontap_fs,srv-pnp
   check_interval                  15
   retry_interval                  15
   check_command                   check_naf_v2!$HOSTADDRESS$!60!{{ application.loginsnmpv2.community }}!vol_inode,{{ volume.name }},{{ volume.warning}}{{ volume.units}},{{ volume.critical }}{{ volume.units }}
}

{{ application|service("os_ontap_fs_check_files_"+ volume.name) }}
   host_name                       {{ application.host_name }}
   use                             os_ontap_fs,srv-pnp
   check_interval                  15
   retry_interval                  15
   check_command                   check_naf_v2!$HOSTADDRESS$!60!{{ application.loginsnmpv2.community }}!vol_files,{{ volume.name }},{{ volume.warning}}{{ volume.units}},{{ volume.critical }}{{ volume.units }}
}

{% endfor %}
{% endif %}
