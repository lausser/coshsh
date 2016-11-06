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

Coshsh just created a nagios configuration consisting of one host. Let's look into this in detail.

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

