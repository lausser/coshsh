# coshsh Config-Generator for Shinken / Nagios /Icinga

## What is coshsh?

Coshsh is a framework which helps you producing configuration files for open source monitoring systems.

## Features

* coshsh is very fast. (~60000 services in 10 seconds)
* coshsh can be extended easily.
* coshsh reads only hosts and applications. Services are added later.

## Why should you use it?
Because others use it too.
* The city of Munich. https://bit.ly/2QhNCOJ
* A car manufacturer in Munich with three letters. 
* A global storage company with three letters. (they were bought and now have four letters)
* Lidl/Kaufland. https://bit.ly/2L459nH
* A chinese car manufacturer in Shenyang.
* An austrian company producing crystal products.
* A world-wide operating consulting firm.
* A venerable hanseatic bank.

and many more companies which eliminated manual tasks in monitoring.

## Download

http://labs.consol.de/nagios/coshsh

## Support

Professional support and consulting is available via [www.consol.de](http://www.consol.de/open-source-monitoring/support)

## Changelog

The changelog is available on
[github](https://github.com/lausser/coshsh/blob/master/Changelog)

## How does it work

coshsh reads one or many datasources (which can be files, databases, ldap...) and transforms their contents into host/service/contact-configuration files. Host- and service-definitions are created by filling placeholders in template-files.


In the beginning there are hosts and applications. There are no host and service definitions. Why? Because your server admins don't care about. Your windows admin simply wants to enter his new machine in a cmdb. He has no time to configure check_periods or commands or services. He even doesn't want to know what it is.  
The only thing he knows is name, address and model of his new server and the applications he installed.  

For example, your datasource is a database table with a column names "type". If you want to handle a value of "windows" or "windows 2008" all you need is a class file for it:

```python
import coshsh

def __mi_ident__(params={}):
    if coshsh.util.compare_attr("type", params, ".*windows.*"):
        return Windows


class Windows(coshsh.application.Application):
    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None,
            template="os_windows_default"),
        coshsh.templaterule.TemplateRule(needsattr="filesystems",
            template="os_windows_fs"),
    ]
```

The class file will be automatically registered to coshsh. Now whenever a record of type "windows" comes out of your datasource, an object of class Windows is created. (Inside coshsh. You actually won't notice it and you don't have to know about it)
The only thing you need to know is the relationship between an application's class and some template files. Like this one here:

```
{{ application|service("os_windows_default_check_nsclient") }}
  host_name                       {{ application.host_name }}
  use                             os_windows_default
  check_command                   check_nrpe_arg!60!checkUpTime!MinWarn=5m MinCrit=1m
}

{{ application|service("os_windows_default_check_cpu") }}
  host_name                       {{ application.host_name }}
  use                             os_windows_default,srv-pnp
  max_check_attempts              10
  check_command                   check_nrpe_arg!60!checkCPU!warn=80 crit=90 time=5m time=1m time=30s
}

{{ application|service("os_windows_default_check_mem") }}
  host_name                       {{ application.host_name }}
  use                             os_windows_default,srv-pnp
  check_command                   check_nrpe_arg!60!checkMem!MaxWarn=80% MaxCrit=90% ShowAll=long type=physical type=virtual type=paged
}

{{ application|service("os_windows_default_check_autosvc") }}
  host_name                       {{ application.host_name }}
  use                             os_windows_default
  check_command                   check_nrpe_arg!60!CheckServiceState!CheckAll
}

{#
{{ application|service("os_windows_default_check_ntp") }}
  host_name                       {{ application.host_name }}
  use                             os_windows_default
  check_command                   windows-check_time!3600!360000
}
#}

define servicedependency {
  name                             dependency_os_windows_default_check_nsclient_uc_{{ application.host_name }}
  host_name                        {{ application.host_name }}
  service_description              os_windows_default_check_nsclient
  execution_failure_criteria       u,c
  notification_failure_criteria    u,c
  dependent_service_description    os_windows_.*,\
                                   !os_windows_default_check_nsclient
}
```

Only a nagios admin will ever see these template files and will have to edit them.

[![Coverage Status](https://coveralls.io/repos/github/lausser/coshsh/badge.svg?branch=master)](https://coveralls.io/github/lausser/coshsh?branch=master)
