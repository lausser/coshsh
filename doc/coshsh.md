* auto-gen TOC:
{:toc}

In this tutorial you will learn how to automatically create Nagios configuration files from your own inventory data.  
In order to reproduce the examples described here you should install [OMD Labs Edition](https://labs.consol.de/omd) and create a site called _cotu_ (coshsh tutorial).

### Recipe

A recipe is the central configuration item in coshsh. It describes the ingredients used to "cook" a nagios configuration. It consists of the following settings:

1. datasources  
  This is where the raw data like host names, ip addreses, applications, locations etc. come from. A datasource in coshsh is a piece of python code which acts as an adaptor to cmdbs, excel sheets or any kind of inventory.
2. classes_dir  
  In a directory specified by the classes_dir attribute coshsh looks for small Python files describing certain types of applications. 
3. templates_dir  
  In a directory specified by the templates_dir attribute coshsh looks for template files. These files contain predefined Nagios object definitions and Jinja2-code. Each type of application has one or more templates.
4. objects_dir  
  This attribute points to a directory where coshsh will write the final configuration files.

First you have to create a config file for coshsh:
```
[recipe_tutorial]
# this can also be a comma-separated list if you read from multiple sources
datasources = mysource 
classes_dir =  %OMD_ROOT%/etc/coshsh/recipes/tutorial/classes
templates_dir =  %OMD_ROOT%/etc/coshsh/recipes/tutorial/templates
objects_dir = %OMD_ROOT%/var/coshsh/configs/tutorial
```
It will be saved to _~/etc/coshsh/conf.d/tutorial.cfg_. Then run the command **coshsh-cook** for the first time: 
```
OMD[cotu]:~$ coshsh-cook --cookbook etc/coshsh/conf.d/tutorial.cfg --recipe tutorial
2016-11-06 18:28:53,030 - INFO - recipe tutorial init
2016-11-06 18:28:53,030 - INFO - recipe tutorial classes_dir /omd/sites/cotu/etc/coshsh/recipes/tutorial/classes,/omd/sites/cotu/share/coshsh/recipes/default/classes
2016-11-06 18:28:53,030 - INFO - recipe tutorial templates_dir /omd/sites/cotu/etc/coshsh/recipes/tutorial/templates,/omd/sites/cotu/share/coshsh/recipes/default/templates
2016-11-06 18:28:53,052 - INFO - recipe tutorial objects_dir /omd/sites/cotu/var/coshsh/configs/tutorial
2016-11-06 18:28:53,053 - INFO - load items to datarecipient_coshsh_default
2016-11-06 18:28:53,054 - INFO - recipe datarecipient_coshsh_default dynamic_dir /omd/sites/cotu/var/coshsh/configs/tutorial/dynamic does not exist
2016-11-06 18:28:53,054 - INFO - recipient datarecipient_coshsh_default dynamic_dir /omd/sites/cotu/var/coshsh/configs/tutorial/dynamic
2016-11-06 18:28:53,054 - INFO - number of files before: 0 hosts, 0 applications
2016-11-06 18:28:53,054 - INFO - number of files after:  0 hosts, 0 applications
```
Nothing happens here, because the datasource mysource does not exist yet.

### Datasource

A datasource's job is to open and read the inventories and to create Host and Application objects. It's code has to be put in a file with a name starting with _datasource__. The actual datasource is a Python class. In order to be found by a recipe, the datasource file has to implement an interface function _\__ds_ident\___.

```
#!/usr/bin/env python
#-*- encoding: utf-8 -*-

import logging
import coshsh
from coshsh.datasource import Datasource, DatasourceNotAvailable
from coshsh.host import Host
from coshsh.application import Application
from coshsh.item import Item
from coshsh.contactgroup import ContactGroup
from coshsh.contact import Contact
from coshsh.monitoringdetail import MonitoringDetail
from coshsh.templaterule import TemplateRule
from coshsh.util import compare_attr

logger = logging.getLogger('coshsh')

def __ds_ident__(params={}):
    if coshsh.util.compare_attr("type", params, "mycmdb"):
        return MyCMDBClass

class MyCMDBClass(coshsh.datasource.Datasource):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__(**kwargs)
        self.username = kwargs["username"]
        self.password = kwargs["password"]
        self.hostname = kwargs["hostname"]
```

In order to use this code, the datasource has to be registered in the config file. Remember the _datasources = mysource_ in the recipe's section. It references the section _datasource_mysource_.

```
[datasource_mysource]
type = mycmdb
hostname = cmdb.mycorp.com
username = coshshuser
password = c0$h$h
```

These settings do not point directly to the Python-file above. Coshsh instead scans the directory _classes_dir_ for _datasource\_*_-files and calls the _\__ds_ident\___-functions found in these until one returns a Python class. Now coshsh knowns which class is the right one to handle datasources of type _mycmdb_.
Such a class has to implement the methods _\__init___, _open_, _read_ and _close_. 

```
    def open(self):
        logger.info('open datasource %s' % self.name)
        # open a database or a xls-sheet
        ...
```

The most important method is _read_, this is where Host and Application objects are created.

```
    def read(self, filter=None, objects={}, force=False, **kwargs):
        self.objects = objects
        ...
        for row in database_or_csv_or_whatever:
            # row must have row["host_name"] and row["address"]
            h = Host(row)
            # this host object will be added to the (internal) list of hosts
            self.add('hosts', h)
        ...
```

Imagine there was one host in the datasource. If you run **coshsh-cook** again, the result will look like:
```
OMD[cotu]:~$ coshsh-cook --cookbook etc/coshsh/conf.d/tutorial.cfg --recipe tutorial
2016-11-06 22:07:41,920 - INFO - recipe tutorial init
2016-11-06 22:07:41,920 - INFO - recipe tutorial classes_dir /omd/sites/cotu/etc/coshsh/recipes/tutorial/classes,/omd/sites/cotu/share/coshsh/recipes/default/classes
2016-11-06 22:07:41,921 - INFO - recipe tutorial templates_dir /omd/sites/cotu/etc/coshsh/recipes/tutorial/templates,/omd/sites/cotu/share/coshsh/recipes/default/templates
2016-11-06 22:07:41,943 - INFO - recipe tutorial objects_dir /omd/sites/cotu/var/coshsh/configs/tutorial
2016-11-06 22:07:41,944 - INFO - open datasource mysource
2016-11-06 22:07:41,944 - INFO - recipe tutorial read from datasource mysource 1 hosts
2016-11-06 22:07:41,964 - INFO - load template host
2016-11-06 22:07:41,964 - INFO - load items to datarecipient_coshsh_default
2016-11-06 22:07:41,964 - INFO - recipe datarecipient_coshsh_default dynamic_dir /omd/sites/cotu/var/coshsh/configs/tutorial/dynamic does not exist
2016-11-06 22:07:41,964 - INFO - recipient datarecipient_coshsh_default dynamic_dir /omd/sites/cotu/var/coshsh/configs/tutorial/dynamic
2016-11-06 22:07:41,965 - INFO - number of files before: 0 hosts, 0 applications
2016-11-06 22:07:41,965 - INFO - number of files after:  1 hosts, 0 applications

```

Coshsh just created a nagios configuration consisting of one host. For demonstration purposes you can simply add this line to the sample code above:

```
        database_or_csv_or_whatever = [
            { 'host_name': 'server-nr1', 'address': '192.168.14.1',
              'location': 'muenchen-ost', 'customer': 'meier.und.co',
              'datacenter': 'rz2', 'location_code': 'muc-80-2',
              'sn': '37HX23463Z' },
        ]
```

Let's look into the process of config generation in detail.

### How a host object is created

#### Data collection
The recipe calls the read method of it's datasource(s). After this collection phase, the recipe has a list of objects of the class Host().

#### Rendering
In the path specified as *templates_dir* (even it's not mentioned in the config file, there is a hidden default *templates_dir*, which is installed along with coshsh) it looks for a file called *host.tpl*, which contains a nagios host definition where several attributes have jinja2-variables as their values. It looks roughly like this:
```
define host {
    use                         generic-host
    host_name                   {{ host.host_name }}
    address                     {{ host.address }}
{% if host.hostgroups %}
    hostgroups                  {{ host.hostgroups }}
{% endif %}
    check_command               check_host_alive
    notification_options        d,u,r
    ...
```
Now for every host object this template is rendered and the jinja2-variables are replaced by the actual attributes of the object.
The result is a string which is added as another attribute to the host object.

#### Config generation
Then the list of host objects is sent to the datarecipient(s). If no datarecipients have been defined in a recipe (which is the normal case), an internal default recipient will handle the host objects. It takes the recipe parameter _objects_dir_ and first creates a directory _dynamic_ inside it if it does not exist already. Then, for every host object it creates a subdirectory _dynamic/hosts/<host_name>_ and writes the rendered string to a file host.cfg

When coshsh-cook exits we now have a directory structure with host configs.

```
OMD[cotu]:~$ find var/coshsh/configs/
var/coshsh/configs/
var/coshsh/configs/tutorial
var/coshsh/configs/tutorial/dynamic
var/coshsh/configs/tutorial/dynamic/hosts
var/coshsh/configs/tutorial/dynamic/hosts/server-nr1
var/coshsh/configs/tutorial/dynamic/hosts/server-nr1/host.cfg

```

If your datasource provides more information for a host than name and address, you can use it for hostgroups or custom macros.

```
            h.hostgroups.append('customer_' + row['customer'].lower())
            h.hostgroups.append('location_' + row['location_code'].lower())
            h.macros = {
                '_CUSTOMER': row['customer'],
                '_DATACENTER': row['datacenter'],
                '_LOCATION_CODE': row['location_code'],
                '_SERIAL': row['sn'],
            }
```

After you run **coshsh-cook** again, there are config files for hostgroups, too.

```
OMD[cotu]:~$ find var/coshsh/configs/
var/coshsh/configs/
var/coshsh/configs/tutorial
var/coshsh/configs/tutorial/dynamic
var/coshsh/configs/tutorial/dynamic/hostgroups
var/coshsh/configs/tutorial/dynamic/hostgroups/hostgroup_location_muc-80-2.cfg
var/coshsh/configs/tutorial/dynamic/hostgroups/hostgroup_customer_meier.und.co.cfg
var/coshsh/configs/tutorial/dynamic/hosts
var/coshsh/configs/tutorial/dynamic/hosts/server-nr1
var/coshsh/configs/tutorial/dynamic/hosts/server-nr1/host.cfg
```

The host definition now looks like
```
OMD[cotu]:~$ cat var/coshsh/configs/tutorial/dynamic/hosts/server-nr1/host.cfg
define host {
    host_name                       server-nr1
    address                         192.168.14.1
    alias                           server-nr1
    hostgroups                      customer_meier.und.co,location_muc-80-2
    check_command                   check_host_alive
    notification_options            d,u,r
    _SSH_PORT                       22
  _LOCATION_CODE                  muc-80-2
  _CUSTOMER                       meier.und.co
  _SERIAL                         37HX23463Z
  _DATACENTER                     rz2
}

```

Remember, in the datasource code we passed a dict to the constructor of the Host class. Every item of this dict will be an attribute of the resulting host object and can be used in the tpl-file to modify the rendered cfg-file.
Copy _share/coshsh/recipes/default/templated/host.tpl_ to _etc/coshsh/recipes/tutorial/templates_.
You can now edit the template-file and implement two variants of the host-check.

```
{% if 'location_southpole' in host.hostgroups %}
    check_command                   check_host_alive!--timeout 60
{% else %}
    check_command                   check_host_alive!--timeout 10
{% endif %}
```

Alternatively you could write

```
    check_command                   check_host_alive!--timeout {{ host.ping_timeout }}
```

and in the datasource

```
    if row["location"] == "southpole":
        row["ping_timeput"] = 60
    else:
        row["ping_timeput"] = 10
```


### How coshsh handles applications and creates services

First it is important to emphasize that coshsh does not know about Nagios services. Instead it has the concept of applications. (Of course there will be services in the end, as we will see later)
As coshsh was meant to work with input sources like cmdbs, meaning systems which have no idea of Nagios' service definitions, it expects hosts and applications. The operating system or firmware is also seen as an application.

#### Data collection
Let's go back to the datasource. Like we provided a dict with a host_name and an address to the Host() constructor, we will do the same with applications.  
For example, if we want to add a Windows operating system to a server, we achive this with the following code:

~~~
    ...
        # this is just for demonstration purposes
        # These data are supposed to come out of a database etc.
        database_or_csv_or_whatever = [
            { 'host_name': 'server-nr1', 'address': '192.168.14.1',
              'location': 'muenchen-ost', 'customer': 'meier.und.co',
              'datacenter': 'rz2', 'location_code': 'muc-80-2',
              'sn': '37HX23463Z', 'system': 'Windows2012', 'layout': 'fileserver'},
        ]
        for row in database_or_csv_or_whatever:
            # row must have row["host_name"] and row["address"]
            h = Host(row)
            # this host object will be added to the (internal) list of hosts
            self.add('hosts', h)
            row['name'] = 'os'
            row['type'] = row['system']
            a = Application(row)
            self.add('applications', a)
            ...
~~~

The minimum of information we must feed into an Application constructor is *host_name*, *name* and *type*, where *name* is a string which describes best the purpose of an application. (For example *type = Apache*, *name = Intranet* or *type = Oracle*, *name = BillingDB*)
The magic happens inside the Application constructor. We saw that a datasource-file has a function *__ds_ident_\_* which returns a Datasource-like class.
The same applies to applications. In the *classes_dir*, coshsh looks for files called _os\_\*.py_ or _app\_\*.py_ respectively *__mi_ident_\_*-functions inside them.
If an application matching the row["type"] is known to coshsh, then one of the *__mi_ident_\_* will return the suitable class. Out of the generic Application constructor comes an instance of a more specific class.
Adding applications to coshsh is as easy as putting a small Python file *os_windows.py* in the *classes_dir*. For example, the file handling Windows looks like this:

~~~
from application import Application
from templaterule import TemplateRule
from util import compare_attr

def __mi_ident__(params={}):
    if compare_attr("type", params, ".*windows.*"):
        return Windows


class Windows(Application):
    template_rules = [
        TemplateRule(needsattr=None,
            template="os_windows_default"),
        TemplateRule(needsattr="filesystems",
            template="os_windows_fs"),
    ]
~~~

In the above example...
~~~
            a = Application(row)
            self.add('applications', a)
            print "application is", a.__class__.__name__
            # application is Windows
~~~

This is a minimalistic example which does nothing more than to point coshsh to two files, *os_windows_default.tpl* and *os_windows_fs.tpl*. They are expected to live in the *templates_dir*.

And here we find the Nagios services.

~~~
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
...
~~~
Now, as we added an application to an alreday existing host, if you run **coshsh-cook** again, the result will look like:
```
OMD[cotu]:~$ coshsh-cook --cookbook etc/coshsh/conf.d/tutorial.cfg --recipe tutorial
2016-11-06 22:19:41,920 - INFO - recipe tutorial init
2016-11-06 22:19:41,920 - INFO - recipe tutorial classes_dir /omd/sites/cotu/etc/coshsh/recipes/tutorial/classes,/omd/sites/cotu/share/coshsh/recipes/default/classes
2016-11-06 22:19:41,921 - INFO - recipe tutorial templates_dir /omd/sites/cotu/etc/coshsh/recipes/tutorial/templates,/omd/sites/cotu/share/coshsh/recipes/default/templates
2016-11-06 22:19:41,943 - INFO - recipe tutorial objects_dir /omd/sites/cotu/var/coshsh/configs/tutorial
2016-11-06 22:19:41,944 - INFO - open datasource mysource
2016-11-06 22:19:41,944 - INFO - recipe tutorial read from datasource mysource 1 hosts
2016-11-06 22:19:41,964 - INFO - load template host
2016-11-06 22:19:41,964 - INFO - load items to datarecipient_coshsh_default
2016-11-06 22:19:41,964 - INFO - recipe datarecipient_coshsh_default dynamic_dir /omd/sites/cotu/var/coshsh/configs/tutorial/dynamic does not exist
2016-11-06 22:19:41,964 - INFO - recipient datarecipient_coshsh_default dynamic_dir /omd/sites/cotu/var/coshsh/configs/tutorial/dynamic
2016-11-06 22:19:41,965 - INFO - number of files before: 1 hosts, 0 applications
2016-11-06 22:19:41,965 - INFO - number of files after:  1 hosts, 1 applications
```
Remember the *template_rules* in *os_windows.py*. They tell coshsh which tpl-files are to be completed and written as cfg-files. Now we have:
```
OMD[cotu]:~$ find var/coshsh/configs/
var/coshsh/configs/
var/coshsh/configs/tutorial
...
var/coshsh/configs/tutorial/dynamic/hosts
var/coshsh/configs/tutorial/dynamic/hosts/server-nr1
var/coshsh/configs/tutorial/dynamic/hosts/server-nr1/host.cfg
var/coshsh/configs/tutorial/dynamic/hosts/server-nr1/os_windows_default.cfg
```

#### fine-tune applications
So far every os_windows_default.cfg will exactly look the same as all the others, except for *host_name*. In very rare cases all of your Windows servers look excatly the same. A good example where the might differ are the filesystems/partitions. That's where application details play a role. With application details you can add extra attributes to the application object and use them in the tpl-files to render individual cfg-files.
There are a lot of predefined application details. In the following example we use the filesystem detail. We saw the creation of an application:
```
            row['host_name'] = row['host_name']
            row['name'] = 'os'
            row['type'] = row['system'] # Windows2012
            a = Application(row)
            self.add('applications', a)
```
Let's add a drive C: and a drive D: with their respective thresholds.

```
            row['monitoring_type'] = 'FILESYSTEM'
            row['monitoring_0'] = 'FILESYSTEM'
            row['monitoring_1'] = 'C'   # drive name
            row['monitoring_2'] = '75'  # warning threshold
            row['monitoring_3'] = '85'  # critical threshold
            d = MonitoringDetail(a)
            a.monitoring_details.append(d)
            row['monitoring_1'] = 'D'
            row['monitoring_2'] = '5:'
            row['monitoring_3'] = '2:'
            row['monitoring_4'] = 'GB'  # unit
            d = MonitoringDetail(a)
            a.monitoring_details.append(d)
```

The detail _FILESYSTEM_ can be added multiple times to an application. Before the configuration files are rendered, coshsh processes all the details attached to an application. In the _FILESYSTEM_'s case we then have an attribute _application.filesystems_ which is of type list. When the application's tpl-file is rendered, this list can be used to create several Nagios services, one for each filesystem.

```
{% for fs in application.filesystems %}
{{ application|service("os_windows_fs_check_" + fs.path) }}
  host_name                       {{ application.host_name }}
  use                             os_windows,srv-perf
  check_interval                  15
  check_command                   check_nscrestc!60!check_drives!\
      "crit=free<{{ fs.critical }}{{ fs.units }}" \
      "crit=free<{{ fs.critical }}{{ fs.units }}" \
      "drive={{ fs.path }}" 
}
{% endfor %}
```

The _FILESYSTEM_ detail is a list-type. The same is true for _PORT_, _INTERFACE_, _DATASTORE_, _TABLESPACE_ and _URL_. They all appear as arrays _application.ports_ etc. which can be processed with jinja2-for-loops.
There are also scalar application details. Only one of each type can be added to an application. (Adding them twice, they would overwrite each other). Examples are _LOGIN_ and _LOGINSNMPV2_. The latter is used for SNMP communities. Think about a Cisco switch. It will have an application with a name "os" and a type like "ios 12". If all your network devices have the same community, you can hard-code it. But if they differ, then you add a detail in the datasource.

```
            row['host_name'] = row['host_name']
            row['name'] = 'os'
            row['type'] = row['system'] # ios 12
            a = Application(row)
            self.add('applications', a)
            d = MonitoringDetail({
                'host_name': a.host_name,
                'name': a.name,
                'type': a.type,
                'monitoring_type': 'LOGINSNMPV2',
                'monitoring_0': 'xxxsecretxxx',
            })
            a.monitoring_details.append(d)
```

Now you can use a placeholder _{{ application.snmpv2.community }} in the _os\_ios_-template-file.
In the example above the dict parameter for the constructor was written as key-value pairs with values coming from the application. You can write the datasource code as you want, but the preferred way is to have a detail table in the cmdb and reading it with a simple _d = MonitoringDetail(row)_ like in the application example.











