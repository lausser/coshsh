### Recipe

A recipe is the central configuration item in coshsh. It describes the ingredients used to "cook" a nagios configuration. It consists of the following settings:

1. datasources  
  This is where the raw data like host names, ip addreses, applications, locations etc. come from. A datasource in coshsh is a piece of python code which acts as an adaptor to cmdbs, excel sheets or any kind of inventory. A datasource's job is to open and read the inventories and to create Host and Application objects.
2. classes_dir  
  In a directory specified by the classes_dir attribute coshsh looks for small Python files describing certain types of applications. 
3. templates_dir
  In a directory specified by the templates_dir attribute coshsh looks for template files. These files contain predefined Nagios object definitions and Jinja2-code. Each type of application has one or more templates.
4. objects_dir  
  This attribute points to a directory where coshsh will write the final configuration files.


### Datasource

Code inside a datasource (later)

Datasource reads an input line.
Something that has a host_name and an address is fed to the constructor Host().
This Host object will be added to the (internal) list of hosts.
```
    for row in database_or_csv_or_whatever:
        # row must have row["host_name"] and row["address"]
        h = Host(row)
        self.add(h)

```




### How a host object is created

#### Data collection
The recipe calls the read method of it's datasource(s). After this collection phase, the recipe has a list of objects of the class Host().

#### Rendering
In the path specified as templates_dir it looks for a file called host.tpl, which contains a nagios host definition where several attributes have jinja2-variables as their values. It looks roughly like this:
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
  $objects_dir
      dynamic
          hosts
              <host1>
                  host.cfg
              <host2>
                  host.cfg
              <host3>
                  host.cfg
```

