# Coshsh Comprehensive Documentation

{:toc}

## Introduction

Coshsh is a versatile and powerful configuration generator (pronounced like "cosh-sh" with a 'ts' sound as in 'cats' at the beginning, a short 'o' as in 'cot', and ending with a sustained 'sh' sound, similar to the 'sh' in 'wish' but drawn out, as if saying 'wi-shhhh'; IPA: /tsɔʃː/).

It's primarily designed to automate the creation of configurations for monitoring systems such as Nagios, Icinga, and Naemon. Its flexible architecture also allows it to generate configurations for other systems, like Prometheus (e.g., via `datarecipient_prometheus_snmp.py` for SNMP exporter targets) or any other text-based configuration format.

### Naming Origin
The name Coshsh originated when its creator was a co-author of Shinken, a Nagios fork. While it possibly stands for 'COnfigurations for Services and Hosts for SHinken' – a plausible explanation for its origin – the exact details are humorously elusive. It's also quipped that Coshsh might simply have been the result of a search for a unique name that didn't yet exist in search engine results.

In Coshsh terminology:
*   A **Cookbook** is an INI-style configuration file (or set of files) that contains one or more "recipes." It's the top-level plan defining what Coshsh should generate.
*   A **Recipe**, much like in cooking, outlines a specific generation task. It lists its "ingredients" – which are primarily datasources (to get raw data), specialized Python classes (to process and model different types of data like specific OSes or applications), and Jinja2 templates (to define how the final configuration output should be formatted). When a recipe is processed ("cooked"), the result is a set of configuration files or other outputs.

### Purpose and Benefits
The core purpose of Coshsh is to streamline and automate the management of complex configurations, particularly in environments where inventory data, host attributes, and service definitions are spread across multiple or diverse sources. These sources can range from simple CSV files to comprehensive CMDBs (like ServiceNow) or infrastructure management platforms (like NetBox), which can be integrated via custom or provided datasources.

**Key Benefits of using Coshsh:**

*   **Consistency:** Ensures uniformity across all generated configuration files, reducing discrepancies that can arise from manual editing.
*   **Reduced Manual Effort & Errors:** Automates repetitive tasks, significantly cutting down the time spent on configuration and minimizing human errors.
*   **Scalability:** Efficiently manages large-scale environments with thousands of hosts and services by defining them through data and reusable logic rather than individual manual configurations.
*   **Flexibility & Extensibility:** Highly adaptable through custom Python classes for datasources (to fetch data from any source), application/OS types (to model specific behaviors and templates), and monitoring details (to add granular information).
*   **Version Control Friendly:** Configuration logic (Python classes, Jinja2 templates) and input data (e.g., CSV files) can be easily version controlled using systems like Git, providing history, auditability, and easier collaboration.

**High-Level Capabilities Overview:**

*   **Cookbook-Based Configuration:** Uses INI-style cookbook files (`*.cfg`) to define the overall setup, including datasources, recipes, and global parameters.
*   **Recipe-Driven Generation:** Each configuration generation task is encapsulated in a "recipe," which specifies the data sources, processing classes, templates, and output destinations.
*   **Dynamic Datasources:** Employs a plugin system to dynamically load datasource handlers (Python classes) that fetch raw data from various systems (e.g., CSV files, NetBox API, ServiceNow API).
*   **Class-Based Specialization:** Allows for the definition of specialized Python classes for different types of configuration items (hosts, applications, operating systems). These classes can have unique properties and determine which templates are used for them.
*   **Powerful Templating with Jinja2:** Leverages the Jinja2 templating engine to generate configuration files from the processed data, allowing for complex logic, loops, conditionals, and custom extensions within templates.
*   **Extensible Architecture:** Provides clear extension points for creating custom Python classes to handle new data sources, define new types of applications or services, model specific monitoring details, and even customize output generation (datarecipients).

## Simple Example

This example walks through creating a minimal Coshsh setup to generate Nagios configuration for a single host and one of its operating system services.

Let's assume you have a project directory structure like this:

```
my_simple_coshsh_project/
|-- cookbook/
|   `-- example.cfg
|-- data/
|   |-- inventory_hosts.csv
|   `-- inventory_apps.csv
|-- example_classes/
|   `-- os_myos.py
|-- example_templates/
|   |-- host.tpl
|   `-- os_myos_default.tpl
`-- output_configs/  # Coshsh will create this
```

**Step 1: Create Data Files**

*   `my_simple_coshsh_project/data/inventory_hosts.csv`:
    ```csv
    host_name,address,type,alias
    server01,192.168.1.10,generic_server,My First Server
    ```
    *(Note: The `type` column here is a general categorization for the host, like 'server', 'network_switch'. It can be used by custom host classes or for hostgrouping. It's distinct from the application/OS type defined next.)*

*   `my_simple_coshsh_project/data/inventory_apps.csv`:
    ```csv
    host_name,name,type
    server01,os,myos_distro
    ```
    *(Note: For an OS application, `name` is typically "os". The `type` ("myos_distro" here) is what your custom `os_myos.py` class will look for via `__mi_ident__` to specialize this OS application).*

**Step 2: Create Custom OS Class**

*   `my_simple_coshsh_project/example_classes/os_myos.py`:
    ```python
    import coshsh
    from coshsh.application import Application
    from coshsh.templaterule import TemplateRule

    # This function helps Coshsh identify which class to use for which application type
    def __mi_ident__(params={}):
        if params.get("type") == "myos_distro": # Matches the 'type' in inventory_apps.csv
            return MyOS
        return None

    class MyOS(Application):
        # This rule tells Coshsh to use 'os_myos_default.tpl' for any 'MyOS' application
        template_rules = [
            TemplateRule(template="os_myos_default")
        ]

        def __init__(self, params={}):
            super().__init__(params)
            # You can set default attributes for your OS type here
            # For example, self.snmp_community = "public_os"
    ```

**Step 3: Create Templates**

*   `my_simple_coshsh_project/example_templates/host.tpl`:
    ```jinja
    define host {
        use         generic-host    ; Name of host template to use
        host_name   {{ host.host_name }}
        address     {{ host.address }}
        alias       {{ host.alias | default(host.host_name) }}
        # Add other host attributes here
    }
    ```
    *(Note: `{{ host.alias | default(host.host_name) }}` uses a Jinja2 filter to default the alias to the host_name if not provided in the data.)*

*   `my_simple_coshsh_project/example_templates/os_myos_default.tpl`:
    ```jinja
    define service {
        use                 generic-service ; Name of service template to use
        host_name           {{ application.host_name }}
        service_description OS_{{ application.type }}_ping
        check_command       check_ping!100.0,20%!500.0,60%
        # Add other service attributes here
    }
    ```

**Step 4: Create Cookbook File**

*   `my_simple_coshsh_project/cookbook/example.cfg`:
    ```ini
    [datasource_myinventory]
    type = csv
    dir = ../data
    # Tells the csv datasource to look for files like:
    # myinventory_hosts.csv, myinventory_applications.csv, etc.
    # For this example, ensure your CSV files in ../data are named:
    # inventory_hosts.csv --> rename to myinventory_hosts.csv
    # inventory_apps.csv  --> rename to myinventory_applications.csv
    # OR explicitly define the filenames:
    # csv_hosts_file = inventory_hosts.csv
    # csv_applications_file = inventory_apps.csv

    # For this example, we will use explicit filenames:
    csv_hosts_file = inventory_hosts.csv
    csv_applications_file = inventory_apps.csv

    [recipe_simple_server_config]
    datasources = myinventory
    classes_dir = ../example_classes
    templates_dir = ../example_templates
    objects_dir = ../output_configs
    # Optional: To include Coshsh default classes and templates (recommended for real use):
    # Ensure correct relative or absolute paths if your project is not in the Coshsh root.
    # classes_dir = ../example_classes,../../recipes/default/classes
    # templates_dir = ../example_templates,../../recipes/default/templates
    ```

**Step 5: Run Coshsh-Cook**

Navigate to the `my_simple_coshsh_project/cookbook/` directory (or ensure paths in `example.cfg` are correct, especially if using relative paths for default classes/templates):

```bash
coshsh-cook --cookbook example.cfg --recipe simple_server_config
```
*(If you're not in an OMD environment, you might need to ensure `coshsh-cook` is in your PATH and Coshsh library is in PYTHONPATH. For simplicity, this example assumes `example_classes` and `example_templates` are sufficient. In a real setup, you'd often want to include Coshsh's default paths too, e.g., `classes_dir = ../example_classes,path/to/coshsh/recipes/default/classes`)*.

**Step 6: Inspect Generated Output**

Coshsh will generate configuration files in `my_simple_coshsh_project/output_configs/dynamic/`. You should find:

*   `output_configs/dynamic/hosts/server01/host.cfg`:
    ```nagios
    define host {
        use         generic-host    ; Name of host template to use
        host_name   server01
        address     192.168.1.10
        alias       server01
        # Add other host attributes here
    }
    ```

*   `output_configs/dynamic/hosts/server01/os_myos_default.cfg` (filename might vary slightly based on `unique_config` defaults in `TemplateRule` if not specified):
    ```nagios
    define service {
        use                 generic-service ; Name of service template to use
        host_name           server01
        service_description OS_myos_ping
        check_command       check_ping!100.0,20%!500.0,60%
        # Add other service attributes here
    }
    ```

This simple example demonstrates the fundamental workflow:
1.  Data is defined externally (CSV files).
2.  A cookbook (`example.cfg`) defines a recipe that links the data to processing logic and templates.
3.  Custom Python classes (`os_myos.py`) define how specific types of data are handled and which templates they use.
4.  Jinja2 templates (`host.tpl`, `os_myos_default.tpl`) define the structure of the output configuration.
5.  `coshsh-cook` orchestrates the process.
6.  Configuration files are generated in the specified output directory.

## Core Concepts

Coshsh achieves its flexibility through several interconnected core concepts:

*   **Templates:**
    *   **Role:** Templates define the structure and content of the final configuration files that Coshsh generates. They are the blueprints for your output.
    *   **Format:** Coshsh uses the powerful [Jinja2 templating engine](https://jinja.palletsprojects.com/). Template files typically have a `.tpl` extension and are stored in a `templates_dir` specified by a recipe.
    *   **Data Access:** Inside a template, you can access attributes of the `Host`, `Application`, or other `Item` objects that Coshsh processes. For example, `{{ host.host_name }}`, `{{ application.name }}`, or `{{ application.custom_attribute }}`.
    *   **Logic:** Jinja2 allows for loops (e.g., `{% for fs in application.filesystems %}` to iterate over filesystem details), conditionals (`{% if host.is_virtual %}`), and filters (`{{ my_string | upper }}`).
    *   **Custom Extensions:** Coshsh provides custom Jinja2 filters and tests (defined in `coshsh/jinja2_extensions.py`) like `|service` for formatting service definitions or `|re_sub` for regex substitutions, making templates more concise and powerful.

*   **Classes (Application/OS Specialization):**
    *   **Role:** Python classes are used to define the specific behavior, attributes, and template associations for different types of configuration items, particularly applications and operating systems. They allow you to model your infrastructure elements in an object-oriented way. An application where `name='os'` (often paired with a `type` like "linux", "windows", "ios", "junos") is typically unique per system and represents its base operating system, firmware, or core appliance software. Other applications might represent user-facing software like "apache", "mysql", etc., or other logical services.
    *   **Location:** These classes are typically stored in Python files (e.g., `os_linux.py`, `app_apache.py`) within a `classes_dir` specified by a recipe.
    *   **`__mi_ident__(params={})` Function:** Each such Python module must contain this "Managed Item Identifier" function. When Coshsh processes an item (e.g., an application defined in a CSV row), it calls `__mi_ident__` with the item's parameters (like `params['type']`). The function returns the specific Python class (e.g., `return LinuxOS`) if it's designed to handle that type of item, or `None` otherwise. This allows Coshsh to dynamically select and instantiate the correct class for each item. Users can iteratively create new class files with `__mi_ident__` functions to gradually cover all their application types; Coshsh will use `GenericApplication` for any types not yet covered by a custom class, making the system approachable even for complex environments.
    *   **`template_rules` Attribute:** A crucial attribute within these classes. It's a list of `coshsh.templaterule.TemplateRule` objects. Each `TemplateRule` links the class to one or more `.tpl` files and specifies:
        *   The name of the template file (e.g., `template="os_linux_base_checks"`).
        *   Conditions for using the template (e.g., `needsattr="has_db_role"` means the template is only used if the application object has an attribute `has_db_role` that evaluates to true).
        *   How the output configuration file should be named (using `unique_config` and `unique_attr`).
        *   Optional metadata like `suffix` (e.g., ".json") or `for_tool` (e.g., "prometheus") for specialized datarecipients.
    *   **Custom Logic:** Classes can have `__init__` methods to set default attributes for that type, or other methods (like `wemustrepeat`) that are called during specific phases of the recipe execution to perform custom logic.

*   **Datasources:**
    *   **Role:** Datasources are Python classes responsible for fetching raw inventory data from various external systems or files. They act as the input mechanism for Coshsh.
    *   **Implementation:** They typically inherit from `coshsh.datasource.Datasource` and are located in a `classes_dir` (often named `datasource_*.py`).
    *   **`__ds_ident__(params={})` Function:** Similar to `__mi_ident__` for applications, this "DataSource Identifier" function in a datasource module is used by Coshsh to select the correct datasource class. It receives the datasource configuration from the cookbook (e.g., `params['type']` like "csv", "netboxlabsnetbox") and returns the class if it can handle that type.
    *   **Multiple Datasources & Shared Object Registry:** When a recipe lists multiple datasources, they are processed in the order they appear in the `datasources` attribute of the recipe. Each datasource's `read()` method operates on the same shared internal collection of objects (available as `recipe.objects` or `self.objects` within the datasource). This means a later datasource can add new objects, or even retrieve and modify objects created by an earlier datasource in the same recipe run, allowing for data aggregation or enrichment from different sources.
    *   **Key Methods:**
        *   `open()`: To establish connections (e.g., to a database or API).
        *   `read()`: The core method that fetches data and then instantiates `coshsh.Host`, `coshsh.Application`, and `coshsh.MonitoringDetail` objects, adding them to the recipe's central object store.
        *   `close()`: To close connections and clean up resources.

*   **Cookbooks & Recipes:**
    *   **Cookbooks:** These are INI-style configuration files (e.g., `etc/coshsh/conf.d/my_configs.cfg` or `coshsh.cfg`). They act as the main configuration entry point for Coshsh. A cookbook can define:
        *   One or more `[recipe_<recipe_name>]` sections.
        *   `[datasource_<datasource_name>]` sections detailing how to connect to and query data sources.
        *   `[datarecipient_<datarecipient_name>]` sections for custom output handlers.
        *   `[defaults]` section for global parameters like default `classes_dir`, `templates_dir`, `log_dir`, etc.
        *   `[mapping_<map_name>]` sections for simple key-value lookups usable within other configurations.
    *   **Recipes (`coshsh.recipe.Recipe`):** A recipe is a named configuration block within a cookbook that defines a single, specific configuration generation task. It ties together all other core concepts:
        *   `datasources`: Specifies which configured datasources to use for fetching data.
        *   `classes_dir`: Path(s) to directories where custom Python classes (for datasources, applications, details, etc.) are located.
        *   `templates_dir`: Path(s) to directories containing the Jinja2 `.tpl` template files.
        *   `objects_dir`: The default output directory where generated configuration files will be written if using the `datarecipient_coshsh_default`.
        *   Other parameters like `filter`, `max_delta`, `git_init` control specific behaviors of the recipe.
        *   The recipe object orchestrates the phases: collecting data from its datasources, assembling items (which involves applying specialized classes), rendering the associated templates, and finally passing the rendered output to datarecipients.

*   **Generator (`coshsh.generator.Generator`):**
    *   **Role:** The `Generator` is the central engine that drives the entire Coshsh process.
    *   **Functionality:**
        1.  It reads and parses one or more cookbook files.
        2.  It initializes `Recipe` objects based on the definitions in the cookbooks, including setting up their datasources and datarecipients.
        3.  When its `run()` method is called (typically by the `coshsh-cook` script), it iterates through the selected recipes.
        4.  For each recipe, it manages execution, including PID file protection (to prevent concurrent runs of the same recipe) and then calls the recipe's `collect()`, `assemble()`, `render()`, and `output()` methods in sequence.

*   **Monitoring Details (`coshsh.monitoringdetail.MonitoringDetail`):**
    *   **Role:** Details provide a way to add fine-grained, often structured and repetitive, information to `Host` or (more commonly) `Application` objects. This allows for detailed customization of checks without overly complicating the primary host or application data.
    *   **Creation:** They are typically created by a datasource during its `read()` method. For example, if a CSV file has rows defining filesystems for an OS application, the datasource would create `MonitoringDetail` instances for each filesystem row, setting `monitoring_type="FILESYSTEM"`.
    *   **Processing:** During the `Recipe.assemble()` phase, the `Item.resolve_monitoring_details()` method is called on each host and application. This method processes the attached raw details.
    *   **Attribute Population:** Based on the `monitoring_type` and the logic in the corresponding `detail_*.py` class (e.g., `recipes/default/classes/detail_filesystem.py`), the detail's data is transformed and attached to the parent item. For example, `detail_filesystem.py` has `property = "filesystems"` and `property_type = list`. This means all filesystem details for an application will be available as a list under `application.filesystems`. Each element in this list would be an object with attributes like `.path`, `.warning`, `.critical`. Similarly, a `LOGINSNMPV2` detail might populate `application.loginsnmpv2` with an object containing `.community` and `.protocol`.
    *   **Usage in Templates:** Templates can then easily access this structured information, e.g., `{% for fs in application.filesystems %} check {{ fs.path }} ... {% endfor %}`.

*   **Datarecipients (`coshsh.datarecipient.Datarecipient`):**
    *   **Role:** Datarecipients are responsible for taking the final rendered configuration strings (produced by `Item.render()`) and handling their output.
    *   **Default Behavior:** The `datarecipient_coshsh_default` (from `recipes/default/classes/`) is the most common. It writes the rendered configurations to files within the recipe's `objects_dir`, creating a structured directory layout (e.g., `dynamic/hosts/<hostname>/<config_name>.cfg`).
    *   **Customization:** Datarecipients can be customized to output data in different formats (e.g., JSON, XML, directly to an API) or to different locations. The `datarecipient_prometheus_snmp.py` (generates JSON for Prometheus) and `datarecipient_atomic.py` (generates `check_logfiles` configs for SNMPTT example) illustrate this.
    *   **Dynamic Loading:** Custom datarecipients are defined in `[datarecipient_<name>]` sections in the cookbook and loaded via a `__dr_ident__(params={})` function in their Python module (located in a `classes_dir`).

These core concepts work together to provide a powerful and data-driven approach to configuration management.

## Writing Configuration (`etc/coshsh/conf.d/*.cfg`)

Coshsh uses INI-style configuration files, typically located in a `conf.d` directory (e.g., `etc/coshsh/conf.d/` in a standard installation, or a project-specific path). These files are often referred to as "cookbooks" and can contain definitions for multiple recipes, datasources, datarecipients, and global settings.

### Introduction to Cookbook Files

*   **Format:** Standard INI file syntax (sections in `[square_brackets]`, `key = value` pairs).
*   **Location:** Commonly `etc/coshsh/conf.d/some_config.cfg`. Multiple `.cfg` files can be used and will be parsed together by `coshsh-cook` if specified.
*   **Role:** They define the entire configuration generation plan: what data to get, how to process it, what recipes to run, and where output should go.
*   **Comments:** Lines starting with `#` or `;` are treated as comments.
*   **Variable Substitution:** Coshsh supports environment variable substitution using `%(ENV_VAR_NAME)%` (e.g., `%(OMD_ROOT)%)` and also custom mapping substitution using `@MAPPING_MAPNAME[key]%` if `[mapping_mapname]` sections are defined.

### Recipe Definition (`[recipe_<your_recipe_name>]`)

This section defines a specific configuration generation task. The name of the recipe follows `recipe_`.

*   **Format:** `[recipe_my_linux_servers]`
*   **Key Parameters:**
    *   `datasources`: (Required) Comma-separated list of datasource section names (without the `datasource_` prefix) that this recipe will use.
        *   Example: `datasources = cmdb_linux, local_overrides_csv`
    *   `classes_dir`: (Optional) Comma-separated list of paths to directories containing custom Python classes (for applications, OS types, datasources, datarecipients, details). Paths can use environment variables like `%(OMD_ROOT)%`. Coshsh will also search in `recipes/default/classes` by default; these paths are typically prepended.
        *   Example: `classes_dir = %(OMD_ROOT)/local/etc/coshsh/my_classes, %(OMD_ROOT)/share/coshsh/recipes/custom_apps/classes`
    *   `templates_dir`: (Optional) Comma-separated list of paths to directories containing Jinja2 templates (`.tpl` files). Similar to `classes_dir`, these are prepended to default paths.
        *   Example: `templates_dir = /opt/my_app/coshsh_templates`
    *   `objects_dir`: (Required if no datarecipients are specified or if the default datarecipient `>>>` is used) The base directory where the default datarecipient (`datarecipient_coshsh_default`) will write its output (e.g., Nagios configuration files).
        *   Example: `objects_dir = %(OMD_ROOT)/etc/nagios/conf.d/generated_configs_linux`
    *   `datarecipients`: (Optional) Comma-separated list of datarecipient section names (without the `datarecipient_` prefix). If specified, these handlers will be used for output. The special name `>>>` can be used to explicitly include the default file-writing datarecipient that uses `objects_dir`.
        *   Example: `datarecipients = >>>, prometheus_output, audit_log_db`
    *   `filter`: (Optional) A string defining filters to be applied to datasources. The syntax can vary but often allows specifying conditions for specific datasources, e.g., `filter = main_cmdb(os_type=~linux.*, status=active), other_source(tag=prod)`. The interpretation of the filter string is up to the individual datasource's `read()` method.
    *   `git_init`: (Optional, boolean, defaults to `yes` or `true` as per `Recipe.__init__`) If true, Coshsh will attempt to initialize a Git repository in the output directory (`objects_dir/dynamic` for the default datarecipient) if one doesn't exist. This is useful for tracking changes to generated configurations. Set to `no` to disable.
        *   Example: `git_init = no`
    *   `max_delta`: (Optional) Defines thresholds for changes in the number of generated objects (hosts, applications/services) to prevent accidental large-scale changes. Format: `max_hosts_percent:max_services_percent` (e.g., `10:20` for 10% host change and 20% service change) or a single value for both (e.g., `15` for 15% on both). A negative value (e.g. `-10:-10`) means the check is for growth, not shrinkage. The `max_delta_action` parameter (e.g., `git_reset_hard_and_clean`) specifies what to do if the delta is exceeded. This is primarily handled by datarecipients that support it (like the default one).
        *   Example: `max_delta = 10:15`
        *   Example: `max_delta = -20` (checks for growth beyond 20%)
    *   `log_file`: (Optional) Path to a specific log file for this recipe. Overrides global log settings for this recipe.
        *   Example: `log_file = %(OMD_ROOT)/var/log/coshsh/my_linux_servers.log`
    *   `pid_dir`: (Optional) Directory for this recipe's PID file. Overrides the global `pid_dir`.
    *   `force`: (Optional, boolean) Recipe-specific override for the `--force` command-line option. `yes` or `no`.
    *   `safe_output`: (Optional, boolean) Recipe-specific override for the `--safe-output` command-line option. `yes` or `no`.
    *   `ENV_<VARNAME>`: (Optional) Any parameter starting with `ENV_` will cause Coshsh to set an environment variable named `<VARNAME>` with the given value during the execution of this recipe.
        *   Example: `ENV_MY_CUSTOM_PATH = /opt/special_tools` will set `os.environ["MY_CUSTOM_PATH"]`.

### Datasource Sections (`[datasource_<your_datasource_name>]`)

This section defines a specific source of data. The name after `datasource_` is used in the recipe's `datasources` parameter.

*   **Format:** `[datasource_production_cmdb]`
*   **Key Parameters:**
    *   `type`: (Required) A string identifier for the type of datasource. This value is used by the `__ds_ident__` function in datasource Python modules (found in `classes_dir`) to select the correct class to handle this datasource.
        *   Example: `type = csv` (for the default CSV handler)
        *   Example: `type = netboxlabsnetbox` (for the NetBox datasource)
        *   Example: `type = custom_api_v1` (for a user-defined datasource)
    *   **Type-Specific Parameters:** All other parameters in this section are specific to the datasource `type` and are passed to the `__init__` method of the selected datasource class.
        *   For `type = csv` (using `recipes/default/classes/datasource_csvfile.py`):
            *   `dir`: (Required) Directory containing the CSV files.
            *   `csv_hosts_file`: (Optional) Specific filename for the hosts CSV file (defaults to `<datasource_name>_hosts.csv` or `<name_for_files>_hosts.csv`).
            *   `csv_applications_file`: (Optional) Specific filename for applications CSV.
            *   `csv_applicationdetails_file`: (Optional) Specific filename for details CSV.
            *   `csv_contacts_file`, `csv_contactgroups_file`, etc.
            *   `name_for_files`: (Optional) If specified, overrides `<datasource_name>` when constructing default CSV filenames (e.g., if set to `inventory`, files like `inventory_hosts.csv` are expected).
            *   `csv_delimiter`: (Optional, defaults to `,`) Delimiter used in CSV files.
        *   For `type = netboxlabsnetbox` (using `contrib/classes/datasource_netbox.py`):
            *   `netbox_url`: URL of the NetBox API.
            *   `api_token`: API token for NetBox.
            *   `netbox_host`: (Optional) Host header override for SSH tunneling.
            *   `insecure_skip_verify`: (Optional, "yes" or "no")
        *   For `type = svcnow_cmdb_ci` (using `contrib/classes/datasource_svcnow_cmdb_ci.py`):
            *   `instance_url`: URL of the ServiceNow instance.
            *   `username`, `password`: Credentials for ServiceNow.
            *   `insecure_skip_verify`: (Optional, "yes" or "no")

### Datarecipient Sections (`[datarecipient_<your_datarecipient_name>]`)

This section defines an output handler. The name after `datarecipient_` is used in the recipe's `datarecipients` parameter.

*   **Format:** `[datarecipient_prometheus_json_output]`
*   **Key Parameters:**
    *   `type`: (Required) A string identifier for the type of datarecipient. This is used by the `__dr_ident__` function in datarecipient Python modules to select the correct class.
        *   Example: `type = datarecipient_coshsh_default` (for the default file writer)
        *   Example: `type = snmp_exporter` (for the custom one in `tests/recipes/test20/`)
    *   **Type-Specific Parameters:** Other parameters depend on the datarecipient type.
        *   For `type = datarecipient_coshsh_default`:
            *   It implicitly uses the `objects_dir` from its associated recipe.
            *   Can also have `dynamic_dir`, `static_dir`, `max_delta`, `max_delta_action` if these need to be different from recipe defaults or for more granular control if multiple default-like recipients were used (though less common).
        *   For `type = atomic` (from `tests/recipes/testsnmptt/classes/datarecipient_atomic.py`):
            *   `items`: Comma-separated list of item types this datarecipient should process (e.g., `mibconfigs`).
            *   `objects_dir`: Specific output directory for this datarecipient.

### Global Settings (`[defaults]` section)

This optional section defines global default values that apply to all recipes unless overridden within a specific recipe section.

*   **Format:** `[defaults]`
*   **Common Parameters:**
    *   `recipes`: Comma-separated list of recipe names (without the `recipe_` prefix) to be executed if the `coshsh-cook` command is run without a specific `--recipe` argument.
        *   Example: `recipes = all_linux, all_windows, network_devices`
    *   `classes_dir`: Global default path(s) for `classes_dir`. Recipe-specific `classes_dir` are typically prepended to this.
    *   `templates_dir`: Global default path(s) for `templates_dir`. Recipe-specific `templates_dir` are prepended.
    *   `log_dir`: Default base directory for Coshsh log files.
        *   Example: `log_dir = %(OMD_ROOT)/var/coshsh/logs`
    *   `pid_dir`: Default directory for recipe PID files.
        *   Example: `pid_dir = %(OMD_ROOT)/tmp/run/coshsh`
    *   `log_level`: Default logging level (e.g., `INFO`, `DEBUG`).
    *   `backup_count`: Default number of old log files to keep during rotation.
    *   `force`: (boolean, `yes`/`no`) Global default for forcing datasource reads.
    *   `safe_output`: (boolean, `yes`/`no`) Global default for safe output mode.

### Other Special Sections

*   **`[mapping_<map_name>]`:**
    *   Allows defining simple key-value mappings that can be referenced in other parts of the configuration using `@{MAPPING_MAP_NAME[key]}` syntax (note the `@` prefix). This is useful for centralizing common string replacements or short values.
    *   Example:
        ```ini
        [mapping_regions]
        de = germany
        us = united_states

        [recipe_some_recipe]
        description = Server for region @{MAPPING_REGIONS[de]}
        ```

*   **`[prometheus_pushgateway]`:**
    *   Configures the integration for sending Coshsh execution metrics to a Prometheus Pushgateway.
    *   Parameters:
        *   `address`: The address of the Pushgateway (e.g., `127.0.0.1:9091`).
        *   `job`: (Optional) The job name for metrics (defaults to "coshsh").
        *   `username`, `password`: (Optional) For basic authentication with the Pushgateway.
    *   Example:
        ```ini
        [prometheus_pushgateway]
        address = my-pushgateway.internal:9091
        job = coshsh_prod_generator
        ```

By combining these sections, users can create powerful and flexible cookbooks to manage their configuration generation workflows with Coshsh.

## Using Default Datasources (`recipes/default/classes/datasource_*.py`)

Coshsh comes with several built-in datasource handlers located in `recipes/default/classes/`. These provide out-of-the-box capabilities for common data input scenarios.

### `datasource_csvfile`

*   **Purpose:** This is one of the most commonly used datasources. It reads host, application, monitoring detail, and other configuration item data from a set of Comma-Separated Value (CSV) files.
*   **Cookbook Configuration (`type = csv`):**
    ```ini
    [datasource_my_inventory]
    type = csv
    dir = /path/to/my/csv_data_directory  # Required: Directory containing the CSV files

    # Optional: Specify exact filenames if they don't follow the default naming convention
    # Default convention is <datasource_name>_<item_type>.csv or <name_for_files>_<item_type>.csv
    csv_hosts_file = my_custom_hosts.csv
    csv_applications_file = my_custom_apps.csv
    csv_applicationdetails_file = my_custom_details.csv
    # Other potential files:
    # csv_contacts_file = my_custom_contacts.csv
    # csv_contactgroups_file = my_custom_cgroups.csv
    # csv_hostgroups_file = my_custom_hgroups.csv # Note: Hostgroups are often derived, but can be defined

    # Optional: If your CSV filenames are prefixed differently than the datasource section name
    # For example, if files are "master_hosts.csv", "master_applications.csv"
    name_for_files = master

    csv_delimiter = ;  # Optional: Defaults to comma (,)
    # csv_encoding = latin1 # Optional: Defaults to system default, often utf-8
    # csv_strip_attributes = yes # Optional: Defaults to no/false. If yes, strips whitespace from values.
    # csv_lower_attributes = yes # Optional: Defaults to no/false. If yes, converts CSV headers (attribute names) to lowercase.
    ```
*   **Data File Format:**
    *   Each CSV file should have a header row defining the attribute names.
    *   **`*_hosts.csv`:**
        *   Required columns: `host_name`, `address`.
        *   Common optional columns: `alias`, `os_type` (used to determine the OS application type), `parents`, `contact_groups`, `hostgroups` (comma-separated if multiple). Any other column becomes an attribute of the `Host` object.
        *   Example (`my_custom_hosts.csv`):
            ```csv
            host_name,address,alias,os_type,location,role
            server01,192.168.1.10,Main Web Server,linux,dc1,production_web
            filesrv01,192.168.1.11,Primary File Server,windows,dc1,production_file
            ```
    *   **`*_applications.csv`:**
        *   Required columns: `host_name` (to link to a host), `app_name` (a unique name for the application instance on that host, e.g., "os", "prod_database"), `app_type` (used by `__mi_ident__` to select an application class, e.g., "linux", "apache", "oracle").
        *   Any other column becomes an attribute of the `Application` object.
        *   Example (`my_custom_apps.csv`):
            ```csv
            host_name,app_name,app_type,version,criticality
            server01,os,linux,,high
            server01,website_main,apache,2.4,high
            filesrv01,os,windows,2019,medium
            ```
    *   **`*_applicationdetails.csv`:**
        *   Required columns: `host_name`, `monitoring_type`.
        *   `app_name` and `app_type` (optional): If provided, the detail is associated with a specific application on the host. If omitted, it might be associated with the host itself or a default application (behavior can vary).
        *   `monitoring_type`: Key field that determines which `MonitoringDetail` class will handle this row (e.g., "FILESYSTEM", "PORT", "KEYVALUES", "LOGINSNMPV2").
        *   `monitoring_0`, `monitoring_1`, ... `monitoring_N`: These columns provide the actual data for the detail. Their meaning depends on the `monitoring_type`. For example, for "FILESYSTEM", `monitoring_0` might be the path, `monitoring_1` the warning threshold, `monitoring_2` the critical threshold.
        *   Example (`my_custom_details.csv`):
            ```csv
            host_name,app_name,app_type,monitoring_type,monitoring_0,monitoring_1,monitoring_2,monitoring_3
            server01,os,linux,FILESYSTEM,/,85%,95%
            server01,os,linux,FILESYSTEM,/var,80%,90%
            server01,website_main,apache,URL,http://localhost/server-status,My Web Status,30,WARNING
            filesrv01,os,windows,KEYVALUES,admin_contact,john.doe@example.com,,
            ```

### `datasource_simplesample`

*   **Purpose:** Provides a very basic, often hardcoded, set of sample data directly within its Python class (`recipes/default/classes/datasource_simplesample.py`). It's primarily intended for testing Coshsh itself, simple demonstrations, or as a starting point for creating more complex datasources.
*   **Cookbook Configuration (`type = simplesample`):**
    ```ini
    [datasource_sample_data]
    type = simplesample
    # This datasource typically does not require any parameters from the cookbook,
    # as its data is defined within its read() method in Python.
    # If the class were modified, it could accept parameters, e.g.:
    # number_of_hosts = 5
    # base_ip_prefix = 10.0.1
    ```
*   **Data Definition:** The data is generated within the `read()` method of the `SimpleSample` class in `datasource_simplesample.py`. It usually creates a few `Host` objects with some `Application` and `MonitoringDetail` objects attached.
*   **Use Cases:**
    *   Running initial Coshsh tests without needing external CSV files.
    *   Providing a minimal dataset for tutorials or quick feature checks.
    *   Serving as a template for developers creating new datasource classes.

### `datasource_discard`

*   **Purpose:** A null datasource. When its `read()` method is called, it effectively **wipes out the entire internal object registry** (`recipe.objects`) that might have been populated by preceding datasources in the same recipe. It does not add any new items itself.
*   **Cookbook Configuration (`type = discard`):**
    ```ini
    [datasource_clear_all]
    type = discard
    # This datasource takes no parameters.
    ```
*   **Use Cases:**
    *   **Debugging/Selective Output:** If `datasource_discard` is the *last* datasource in a recipe's list, it allows preceding datasources to perform their actions (which might include debugging output, custom processing with side effects on already collected objects, or interactions with external systems) without any of the collected objects then being rendered or written to the `objects_dir` by the default datarecipient. This can be useful if the goal of a recipe is, for example, only to populate a database via a custom datasource and not generate config files.
    *   **Recipe Reset:** In complex scenarios, it could be used to intentionally clear all previously collected objects before a subsequent datasource (in a different recipe or a more advanced conditional setup) repopulates the registry, though this is a less common use case.
    *   Testing recipe logic that doesn't depend on having items for rendering (e.g., testing global pre/post scripts if such hooks existed).

These default datasources provide essential capabilities for getting started with Coshsh and handling common scenarios. For more complex needs, you would typically write your own datasource class.

## Writing Your Own Datasource

While Coshsh provides default datasources like `datasource_csvfile`, you'll often need to fetch data from other sources like databases, CMDB APIs (e.g., NetBox, ServiceNow, as shown in `contrib/classes/`), or custom file formats. This is achieved by writing your own datasource class.

### Introduction

A custom datasource is a Python class that you create, typically inheriting from `coshsh.datasource.Datasource`. Its primary role is to connect to your specific data source, retrieve the necessary inventory information, and then translate that information into Coshsh `Host`, `Application`, and `MonitoringDetail` objects.

You would need a custom datasource if:
*   Your inventory is in a relational database or NoSQL store.
*   You need to pull data from a proprietary or third-party API.
*   Your data is in a specific file format not handled by defaults (e.g., XML, custom JSON structures).
*   You need to perform complex logic during data retrieval or initial processing that's beyond simple CSV parsing.

### Structure of a Datasource Python File

A typical custom datasource file (e.g., `datasource_mycmdb.py`) would look like this:

1.  **Imports:** Include necessary modules like `logging`, `coshsh` (for `Host`, `Application`, etc.), the base `Datasource` class, and any libraries needed to connect to your data source (e.g., `requests` for APIs, database connectors).
2.  **`__ds_ident__` Function:** A top-level function to help Coshsh identify this datasource.
3.  **Datasource Class Definition:** Your custom class inheriting from `coshsh.datasource.Datasource`.

**File Naming and Location:**
*   Conventionally, name your file `datasource_<sourcename>.py` (e.g., `datasource_mycompany_cmdb.py`).
*   Place this file in a directory that is specified in your recipe's `classes_dir` parameter. Coshsh will scan these directories to find and load your datasource.

### The `__ds_ident__(params={})` Function

This function is the entry point for Coshsh to recognize your custom datasource.

*   **Purpose:** Coshsh calls this function for every Python module found in the `classes_dir` that matches the datasource module prefix (usually "datasource\_"). It's used to determine if the current Python module contains the datasource class that can handle the `type` specified in a `[datasource_...]` section of your cookbook.
*   **Parameters:**
    *   `params`: A dictionary containing all key-value pairs from the specific `[datasource_<your_datasource_name>]` section in your cookbook.
*   **Logic:** Inside this function, you'll typically check `params.get('type')` against a unique string that you've chosen for your datasource type.
*   **Return Value:**
    *   If `params['type']` matches what your datasource handles, return your custom datasource class (e.g., `return MyCMDBDataSource`).
    *   If it doesn't match, return `None`.

**Example `__ds_ident__`:**
```python
# In datasource_mycmdb.py
import coshsh # Required for coshsh.util.compare_attr if used
# ... other imports for MyCMDBDataSource ...

def __ds_ident__(params={}):
    # 'my_company_cmdb' is the value you'd set for 'type' in the cookbook
    if params.get('type') == 'my_company_cmdb':
        return MyCMDBDataSource
    # For more flexible matching, you can use coshsh.util.compare_attr
    # if coshsh.util.compare_attr("type", params, "^my_company_cmdb_v[12]$"): # Matches regex
    #     return MyCMDBDataSource
    return None

class MyCMDBDataSource(coshsh.datasource.Datasource):
    # ... class implementation ...
    pass
```

### The `__init__(self, **kwargs)` Method

This is the constructor for your datasource class.

*   **Purpose:** Initializes instances of your datasource.
*   **Parameters:**
    *   `**kwargs`: Coshsh passes all parameters defined in the `[datasource_<your_datasource_name>]` section of the cookbook as keyword arguments to `__init__`.
*   **Common Tasks:**
    1.  Call the superclass constructor: `super().__init__(**kwargs)`. This is important as the base `Datasource` (and its parent `CoshshDatainterface`) handles some initial setup, including the re-blessing mechanism if your class was dynamically chosen by `get_class`.
    2.  Store necessary configuration parameters (like API endpoints, credentials, file paths, query filters from `kwargs`) as instance attributes (e.g., `self.api_url = kwargs.get('api_url')`, `self.username = kwargs.get('user')`).
    3.  Perform any other initial setup specific to your datasource.

**Example `__init__`:**
```python
class MyCMDBDataSource(coshsh.datasource.Datasource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs) # Important first step
        self.api_endpoint = kwargs.get('api_url')
        self.api_token = kwargs.get('token')
        self.default_os_type = kwargs.get('default_os', 'linux')
        self.timeout = int(kwargs.get('timeout', 60))
        # Initialize any internal structures if needed
        self.client = None
```

### The `open(self)` Method

*   **Purpose:** Called once by the recipe before the `read()` method. It's the designated place to establish connections to your data source or open any long-lived resources.
*   **Examples:**
    *   Authenticating to an API and storing a session object.
    *   Establishing a database connection.
    *   Opening a large file if it needs to be read multiple times or kept open during the `read` phase (though often, file handling is done within `read` itself).
*   **Return Value:** Should ideally return `True` on success or raise an appropriate `coshsh.datasource` exception (e.g., `DatasourceNotAvailable`) or return `False` if the connection cannot be established.

**Example `open()`:**
```python
# Assuming self.api_endpoint and self.api_token were set in __init__
# and some_api_library is imported

class MyCMDBDataSource(Datasource):
    # ... __init__ ...
    def open(self):
        logger.info(f"Connecting to CMDB at {self.api_endpoint}")
        try:
            # self.client = some_api_library.connect(
            #     endpoint=self.api_endpoint,
            #     token=self.api_token,
            #     timeout=self.timeout
            # )
            # self.client.test_connection() # Or similar to verify
            logger.info("Successfully connected to CMDB.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to CMDB: {e}")
            # from coshsh.datasource import DatasourceNotAvailable
            # raise DatasourceNotAvailable(f"CMDB connection failed: {e}")
            return False
```

### The `read(self, filter=None, objects={}, force=False, **kwargs)` Method

This is the heart of your datasource, where data is fetched and translated into Coshsh objects.

*   **Parameters:**
    *   `filter`: (Optional) A filter string passed from the recipe's configuration (`filter = ...`). Your `read` method can interpret this string to filter the data it fetches or processes.
    *   `objects`: (Required) This is a direct reference to the recipe's central object dictionary (e.g., `recipe.objects`). You **must** use this dictionary to store the `Host`, `Application`, and `MonitoringDetail` objects you create. The `self.objects` attribute in the base `Datasource` class is typically assigned to this dictionary.
    *   `force`: (Optional, boolean) A flag indicating if cached data should be ignored and data should be fetched fresh. Your datasource should respect this if it implements caching.
    *   `**kwargs`: Additional keyword arguments (less commonly used here).
*   **Tasks:**
    1.  **Fetch Raw Data:** Connect to your source (using resources from `open()`) and retrieve the inventory data. This might involve API calls, database queries, parsing files, etc.
    2.  **Process and Iterate:** Loop through your raw data records.
    3.  **Create Coshsh Objects:** For each logical entity (server, application, service detail):
        *   Prepare a dictionary of parameters that matches the attributes expected by `coshsh.host.Host`, `coshsh.application.Application`, or `coshsh.monitoringdetail.MonitoringDetail` constructors.
        *   Instantiate the objects:
            *   `host_obj = coshsh.host.Host(host_params_dict)`
            *   `app_obj = coshsh.application.Application(app_params_dict)`
            *   `detail_obj = coshsh.monitoringdetail.MonitoringDetail(detail_params_dict)`
        *   **Add to Registry:** Use the `self.add(item_type_plural, item_instance)` method to add the newly created objects to the shared object registry. This method is provided by the base `Datasource` class.
            *   `self.add('hosts', host_obj)`
            *   `self.add('applications', app_obj)`
            *   `self.add('details', detail_obj)` (Note: For details, you add them to this global list. The `Item.resolve_monitoring_details()` method called during the recipe's `assemble` phase will then correctly associate these details with their parent hosts/applications based on `host_name`, `app_name`, etc. in the detail's parameters).
            *   You can also directly append to `app_obj.monitoring_details.append(detail_obj)` if you have the application object handy, but adding to `self.objects['details']` is also a valid approach handled by the core system.
    4.  **Logging:** Include informative log messages about progress, number of items fetched, or any issues encountered.
*   **Return Value:** Should return `True` if data was read successfully, or `False` (or raise an exception like `DatasourceCorrupt`) if a significant error occurred.

### The `close(self)` Method

*   **Purpose:** Called once after the `read()` method has completed (regardless of whether `read` was successful). Use it to close any open connections, release resources, or perform cleanup tasks.
*   **Example:** Closing database connections, logging out from APIs.

**Example `close()`:**
```python
class MyCMDBDataSource(Datasource):
    # ... __init__, open, read ...
    def close(self):
        logger.info("MyCustomDataSource: Closing resources and connections.")
        # if self.client:
        #     self.client.logout()
        # if self.db_connection:
        #     self.db_connection.close()
        return True
```

### Skeletal Example of a Custom Datasource

```python
import logging
import coshsh # For coshsh.host.Host, coshsh.application.Application, etc.
from coshsh.datasource import Datasource, DatasourceNotAvailable, DatasourceCorrupt # Base class and exceptions

logger = logging.getLogger('coshsh')

def __ds_ident__(params={}):
    # This function is crucial for Coshsh to identify your datasource.
    # 'mycustomsource' should match the 'type' in your cookbook's datasource section.
    if params.get('type') == 'mycustomsource':
        return MyCustomDataSource
    return None

class MyCustomDataSource(Datasource):
    def __init__(self, **kwargs):
        # Always call the superclass __init__
        super().__init__(**kwargs)
        logger.info(f"Initializing MyCustomDataSource with params: {kwargs}")

        # Store necessary parameters from the cookbook's datasource section
        self.api_endpoint = kwargs.get('api_endpoint', 'http://localhost/api')
        self.api_key = kwargs.get('api_key')
        self.timeout = int(kwargs.get('timeout', 30))
        # Example: Initialize an API client instance variable
        # self.client = None

    def open(self):
        logger.info(f"MyCustomDataSource: Opening connection to {self.api_endpoint}...")
        # Example: Initialize API client, connect to DB, open files
        # try:
        #     self.client = SomeAPIClientLibrary(endpoint=self.api_endpoint, key=self.api_key, timeout=self.timeout)
        #     self.client.authenticate()
        #     logger.info("MyCustomDataSource: Connection opened successfully.")
        #     return True
        # except Exception as e:
        #     logger.error(f"MyCustomDataSource: Failed to open connection - {e}")
        #     raise DatasourceNotAvailable(f"Connection to {self.api_endpoint} failed.")
        return True # Placeholder

    def read(self, filter=None, objects={}, force=False, **kwargs):
        logger.info("MyCustomDataSource: Reading data...")
        # 'self.objects' is already set by the base class to the 'objects' argument,
        # which is the recipe's shared object dictionary.

        # --- Example: Fetching host data ---
        # try:
        #     raw_hosts_data = self.client.get_all_servers() # Replace with actual data fetching
        # except Exception as e:
        #     logger.error(f"MyCustomDataSource: Error fetching host data - {e}")
        #     raise DatasourceCorrupt("Failed to fetch host data from API.")

        # # Dummy data for demonstration:
        raw_hosts_data = [
            {'id': 'srv1', 'hostname': 'web01.example.com', 'ip_address': '10.0.0.1', 'os': 'Linux', 'role': 'webserver'},
            {'id': 'srv2', 'hostname': 'db01.example.com', 'ip_address': '10.0.0.2', 'os': 'Linux', 'role': 'database_server'},
        ]

        for host_entry in raw_hosts_data:
            host_params = {
                'host_name': host_entry.get('hostname'),
                'address': host_entry.get('ip_address'),
                'alias': host_entry.get('hostname'), # Default alias to hostname
                'os_type': host_entry.get('os'),     # To help create an 'os' application
                # Add any other attributes for the host from host_entry
                'custom_cmdb_id': host_entry.get('id'),
                'role': host_entry.get('role'),
            }
            # Remove None values to avoid issues with templates expecting strings
            host_params = {k: v for k, v in host_params.items() if v is not None}

            h = coshsh.host.Host(host_params)
            self.add('hosts', h) # Adds to self.objects['hosts']
            logger.debug(f"MyCustomDataSource: Added host {h.host_name}")

            # --- Example: Create a basic 'os' application for each host ---
            os_app_params = {
                'host_name': h.host_name,
                'name': 'os', # Convention for the main OS application
                'type': host_entry.get('os', 'unknown_os').lower().replace(' ', '_'), # e.g., 'linux', 'windows_server'
            }
            os_app = coshsh.application.Application(os_app_params)
            self.add('applications', os_app)
            logger.debug(f"MyCustomDataSource: Added OS application for {h.host_name}")

            # --- Example: Adding a Monitoring Detail (e.g., a custom check based on role) ---
            # if host_entry.get('role') == 'webserver':
            #     detail_params = {
            #         'host_name': h.host_name,
            #         'name': 'os', # Associate with the 'os' application, or could be host-level
            #         'monitoring_type': 'CUSTOM_WEB_CHECK', # You'd define a detail_custom_web_check.py
            #         'monitoring_0': '/health_status',     # e.g., URL path for the check
            #         'monitoring_1': '8080',               # e.g., Port for the check
            #     }
            #     md = coshsh.monitoringdetail.MonitoringDetail(detail_params)
            #     # Details are typically added to the global list and resolved later,
            #     # or can be directly appended if the app object is available:
            #     # if not hasattr(os_app, 'monitoring_details'): os_app.monitoring_details = []
            #     # os_app.monitoring_details.append(md)
            #     self.add('details', md) # Recommended way
            #     logger.debug(f"MyCustomDataSource: Added CUSTOM_WEB_CHECK detail for {h.host_name}")

        logger.info(f"MyCustomDataSource: Processed {len(raw_hosts_data)} hosts.")
        return True # Indicate success

    def close(self):
        logger.info("MyCustomDataSource: Closing resources...")
        # Example:
        # if self.client:
        #     self.client.disconnect()
        return True
```

This skeletal example provides a starting point. You'll need to replace the dummy data fetching and processing with logic specific to your actual data source. Remember to handle potential errors during API calls or data parsing gracefully.

## Writing Classes and Templates for New Application Types

While Coshsh offers default classes for common operating systems like Linux and Windows, a key strength of the system is its ability to model and generate configurations for any specific application, OS variant, or any other type of configuration item you need. This is achieved by creating custom Python classes and associated Jinja2 templates.

### Introduction

You'll want to create a custom "Application Class" (or OS class, which is structurally similar) when:
*   You need to monitor a specific application (e.g., Apache, MySQL, your custom in-house software) or a particular OS/firmware type not handled by defaults.
*   The item type requires specific default attributes or needs to process incoming data in a unique way.
*   You want to associate this item type with a distinct set of configuration templates (`.tpl` files).
*   There's custom logic required during the data assembly phase for items of this type (e.g., dynamically creating hostgroups based on application properties).

These classes, combined with their templates, define the "personality" of a monitored component within Coshsh.

### Structure of an Application/OS Class File

1.  **File Naming and Location:**
    *   **Convention:** Name your files descriptively, typically prefixed with `app_` for applications (e.g., `app_mywebserver.py`, `app_oracle_db.py`) or `os_` for operating systems/firmwares (e.g., `os_custom_linux.py`, `os_cisco_ios.py`).
    *   **Location:** Place these Python files in a directory specified by the `classes_dir` parameter in your recipe. Coshsh scans these directories to find your custom classes.

2.  **General Layout:**
    ```python
    # Standard library imports
    import logging

    # Coshsh specific imports
    import coshsh
    from coshsh.application import Application # Or coshsh.item.Item for more generic items
    from coshsh.templaterule import TemplateRule
    # from coshsh.util import compare_attr # Useful for __mi_ident__

    logger = logging.getLogger('coshsh')

    # 1. The __mi_ident__ function (see below)
    def __mi_ident__(params={}):
        # ... logic to identify if this module handles the item ...
        pass

    # 2. The custom class definition
    class MyCustomApplication(Application): # Or MyCustomOS(Application)
        # ... class attributes and methods ...
        pass
    ```

### The `__mi_ident__(params={})` Function

This "Managed Item Identifier" function is crucial for Coshsh's dynamic class loading mechanism.

*   **Purpose:** When an `Application(item_data_dict)` is instantiated by a datasource (or any `Item`), Coshsh's internal factory mechanism calls `__mi_ident__` for each Python module found in the configured `classes_dir` (that matches the `app_` or `os_` prefix). This function's job is to determine if the class defined in *this* module is the correct specialized handler for the item described by `item_data_dict`.
*   **Parameters:**
    *   `params`: A dictionary containing the attributes of the item being processed. This usually comes directly from a row in your datasource (e.g., a row from `*_applications.csv` or a dictionary created from an API response). The `params['type']` key is conventionally used as the primary discriminator.
*   **Logic:**
    *   You typically inspect `params.get('type')` or other distinguishing attributes within `params`.
    *   You can use simple string comparison or more complex logic, including regular expressions via `coshsh.util.compare_attr(attribute_name, params_dict, regex_pattern_or_string)`.
*   **Return Value:**
    *   If your class should handle this item, return the class itself (e.g., `return MyCustomApplication`).
    *   If not, return `None`.

**Example `__mi_ident__`:**
```python
# In classes/app_mywebserver.py
def __mi_ident__(params={}):
    # Check if the 'type' attribute from the data is 'my_web_server' or 'apache_variant'
    if params.get('type') == 'my_web_server' or \
       coshsh.util.compare_attr("type", params, "apache_variant"):
        return MyWebServer
    return None

class MyWebServer(coshsh.application.Application):
    # ...
    pass
```

### The Custom Class Definition

This is where you define the specific behavior and characteristics of your application or OS type.

*   **Inheritance:** Typically, your class will inherit from `coshsh.application.Application`. If you are modeling something that isn't strictly an application (e.g., the `MIB` items in the SNMPTT example), you might inherit directly from `coshsh.item.Item`.
*   **`__init__(self, params={})` Method:**
    *   The constructor for your class. It receives the `params` dictionary (the item's data from the datasource).
    *   **Always call `super().__init__(params)` first.** This initializes the base class and processes standard attributes.
    *   You can then add custom attributes to `self` based on the input `params`, set default values, or perform initial data transformation. These attributes become available in your Jinja2 templates.
    ```python
    class MyWebServer(Application):
        def __init__(self, params={}):
            super().__init__(params) # Call base class constructor
            self.port = params.get('port', '80') # Set from data or default
            self.ssl_enabled = params.get('enable_ssl', 'false').lower() == 'true'
            self.admin_email = "webmaster@example.com" # A hardcoded default
            # Any self.attribute is available in templates as {{ application.attribute }}
    ```
*   **`template_rules` Class Attribute:**
    *   This is a list of `coshsh.templaterule.TemplateRule` objects. It's fundamental for linking your class to its Jinja2 templates and defining how output files are generated.
    *   Each `TemplateRule` instance can take several arguments:
        *   `template` (String, required): The base name of the `.tpl` file to use (e.g., `"app_mywebserver_http"` refers to `app_mywebserver_http.tpl`).
        *   `needsattr` (String, optional): The rule only applies if the application instance has this attribute, and its value is considered true (e.g., not None, not False, not an empty list/dict). Example: `needsattr="vhosts"` means this template is for webservers that have vhosts defined.
        *   `needsnotattr` (String, optional): The rule only applies if the application instance *does not* have this attribute.
        *   `valueofattr` (Dict, optional): A dictionary where keys are attribute names and values are expected attribute values. The rule applies if all specified attributes on the instance match these values. Example: `valueofattr={'environment': 'production', 'critical': True}`.
        *   `unique_attr` (List of strings, optional): A list of attribute names from the application object whose values will be used to form a unique part of the output configuration filename. Defaults typically include `name` and `type`.
        *   `unique_config` (String, optional): A format string for the output filename (e.g., `app_%s_%s_customconfig.cfg`). The `%s` placeholders are filled by the values of attributes specified in `unique_attr`.
        *   `suffix` (String, optional): The suffix for the generated configuration file (defaults to `.cfg`). Useful for generating other file types like `.json`.
        *   `for_tool` (String, optional): Metadata to tag this configuration for a specific tool or purpose. Custom datarecipients can use this to process only certain generated files (e.g., `for_tool="prometheus"` as seen in `tests/recipes/test20/`).
        *   `prio` (Integer, optional): A priority for the rule, which can influence processing order if ever needed (rarely used).
    *   **Example `template_rules`:**
        ```python
        class MyWebServer(Application):
            template_rules = [
                TemplateRule(template="app_mywebserver_base_listeners"),
                TemplateRule(template="app_mywebserver_vhost_config", needsattr="vhosts"),
                TemplateRule(template="app_mywebserver_ssl_config", needsattr="ssl_certificate_path"),
                TemplateRule(template="app_mywebserver_status_page", valueofattr={'monitoring_level': 'full'}),
            ]
            # ...
        ```

### Creating Corresponding `.tpl` Template Files

For each `template` name specified in your `template_rules`, you need a corresponding Jinja2 template file.

*   **Location:** These `.tpl` files must be placed in a directory specified in your recipe's `templates_dir`.
*   **Naming:** The filename must match the `template` string from the `TemplateRule` (e.g., `app_mywebserver_base_listeners.tpl`).
*   **Content & Data Access:**
    *   Write the desired configuration output (e.g., Nagios `define service` blocks, Apache vhost configurations, etc.).
    *   Use Jinja2 syntax to access attributes of the application object: `{{ application.attribute_name }}`. This includes attributes directly from the input data, those set in the `__init__` of your custom class, and those added by `MonitoringDetail` objects.
    *   If your item is a `Host`, you'd use `{{ host.attribute_name }}`.
    *   Access to the parent host from an application is via `{{ application.host.attribute_name }}` (e.g. `{{ application.host.address }}`).

**Example Template (`templates/app_mywebserver_base_listeners.tpl`):**
```jinja
{# This service checks the main listener for the webserver #}
{{ application|service("webserver_" + application.name + "_http_listener") }}
    use                     generic-service
    host_name               {{ application.host_name }}
    check_command           check_tcp!{{ application.port | default(80) }}
    _instance_name          {{ application.name }}
    _port                   {{ application.port | default(80) }}
}

{% if application.ssl_enabled %}
{{ application|service("webserver_" + application.name + "_https_listener") }}
    use                     generic-service
    host_name               {{ application.host_name }}
    check_command           check_tcp!{{ application.ssl_port | default(443) }}
    _instance_name          {{ application.name }}
    _port                   {{ application.ssl_port | default(443) }}
}
{% endif %}
```

### Using `MonitoringDetail` with Custom Classes

Data added by `MonitoringDetail` objects (see "Core Concepts" and "Writing Your Own Datasource") becomes readily available as attributes on your custom application (or host) instances.

*   **Availability:** If a `detail_filesystem.py` (which defines `property = "filesystems"`) processes details for your application, your application instance will have an attribute `application.filesystems` (a list of filesystem detail objects).
*   **In `template_rules`:** You can use these attributes in conditions:
    ```python
    template_rules = [
        TemplateRule(template="app_generic_filesystems", needsattr="filesystems"),
        TemplateRule(template="app_generic_ports", needsattr="ports")
    ]
    ```
*   **In Templates:** You can iterate over or access these attributes:
    ```jinja
    {% if application.filesystems %}
    # Filesystem Checks for {{ application.name }}
    {% for fs_detail in application.filesystems %}
    {{ application|service("fs_" + fs_detail.path | re_sub('[^a-zA-Z0-9_-]', '_')) }}
        host_name           {{ application.host_name }}
        check_command       check_disk!{{ fs_detail.warning }}!{{ fs_detail.critical }}!{{ fs_detail.path }}
        use                 generic-service
    }
    {% endfor %}
    {% endif %}
    ```

By defining custom classes and their associated templates, you can precisely control how Coshsh models your infrastructure and generates configurations for any technology or service.

## Reference Manual

This section provides more detailed information on specific Coshsh modules and functionalities that are useful when extending Coshsh or understanding its internals.

### Interacting with Recipe Data (Adding and Accessing Items)

*   **Overview:**
    *   The core of a `Recipe` object's data is its collection of configuration items (hosts, applications, contacts, custom items, etc.).
    *   This collection is stored in the `recipe.objects` attribute. This attribute is an `OrderedDict` where keys are item type strings (e.g., "hosts", "applications", "details") and values are themselves `OrderedDict`s containing the actual item instances, keyed by their unique fingerprint.
    *   Example structure:
        ```
        recipe.objects = {
            'hosts': {
                'host_fingerprint1': <HostObject1>,
                'host_fingerprint2': <HostObject2>,
            },
            'applications': {
                'app_fingerprint1': <ApplicationObject1>,
                # ...
            },
            'details': {
                'detail_fingerprint1': <MonitoringDetailObject1>,
                # ...
            }
            # ... other item types
        }
        ```

*   **Adding Items (Primarily within Datasources):**
    *   Items are primarily added to this collection within the `read()` method of a datasource class (a subclass of `coshsh.datasource.Datasource`).
    *   The `Datasource` base class provides a helper method: `self.add(item_type_plural, item_instance)`.
        *   `item_type_plural`: A string identifying the type of item, e.g., `"hosts"`, `"applications"`, `"contacts"`, `"details"`, `"mibconfigs"`.
        *   `item_instance`: The actual `Host`, `Application`, `MonitoringDetail`, or custom `Item` object.
    *   The `add` method stores the item in `self.objects[item_type_plural][item_instance.fingerprint()]`.
    *   The `item_instance.fingerprint()` method (defined in `coshsh.item.Item` and potentially overridden by subclasses) generates a unique string key for that specific item instance. For `Host` objects, it's typically just `host.host_name`. For `Application` objects, it's usually a combination like `host_name+app_name+app_type`.
    *   Within a `Datasource`'s `read()` method, `self.objects` is typically a direct reference to the `recipe.objects` dictionary, so additions are made to the central collection.

    **Example (inside a Datasource's `read()` method):**
    ```python
    # self.objects refers to recipe.objects
    # ...
    host_params = {'host_name': 'server01', 'address': '192.168.1.1'}
    h = coshsh.host.Host(host_params)
    self.add('hosts', h) # Adds to self.objects['hosts']['server01']

    app_params = {'host_name': 'server01', 'name': 'os', 'type': 'linux'}
    a = coshsh.application.Application(app_params)
    self.add('applications', a) # Adds to self.objects['applications']['server01+os+linux']

    detail_params = {'host_name': 'server01', 'name': 'os', 'type': 'linux',
                     'monitoring_type': 'FILESYSTEM', 'monitoring_0': '/'}
    md = coshsh.monitoringdetail.MonitoringDetail(detail_params)
    self.add('details', md) # Adds to self.objects['details'][<detail_fingerprint>]
    ```

*   **Accessing Items:**
    *   Once populated by datasources, `recipe.objects` can be accessed to retrieve items. This might be done by other datasources in a chain, during the `assemble` phase, or for custom processing.
    *   **General Access:**
        *   `all_hosts_dict = recipe.objects.get('hosts', {})`
        *   `specific_host = recipe.objects.get('hosts', {}).get('some_host_fingerprint')`
    *   **Datasource Helper Methods:** The `Datasource` class provides convenience methods for accessing items from the `self.objects` collection (which, again, usually points to `recipe.objects`):
        *   `specific_host = self.get('hosts', 'hostname_fingerprint')`
        *   `all_application_objects_list = self.getall('applications')`
        *   `is_present = self.find('hosts', 'hostname_fingerprint')`
    *   **Item Fingerprints:** The `fingerprint()` method is crucial for unique identification. It's a class method on `Item` and its subclasses (e.g., `Host.fingerprint(params)`, `Application.fingerprint(params)`). This method is called by `self.add()` to generate the key for storing the item. When retrieving, you'd typically use the same parameters to generate the fingerprint for lookup if you don't have the exact fingerprint string.

*   **Modifying Items:**
    *   Since `recipe.objects` holds direct references to the item objects, you can modify items after they've been added:
        1.  Retrieve an item (e.g., `my_host = self.get('hosts', 'hostname')`).
        2.  Change its attributes directly (e.g., `my_host.alias = "New Alias"` or `my_host.custom_macros['_EXTRAINFO'] = 'Updated Value'`).
    *   This technique is useful if a later datasource needs to enrich or alter data provided by an earlier one, or if complex logic in the `Recipe.assemble()` phase needs to adjust item properties.

*   **Object Lifecycle Overview:**
    1.  **Collect Phase (`recipe.collect()`):** Datasources are called in sequence. Each datasource's `read()` method populates `recipe.objects` with `Host`, `Application`, `MonitoringDetail`, and other `Item` instances.
    2.  **Assemble Phase (`recipe.assemble()`):**
        *   `MonitoringDetail` objects from `recipe.objects['details']` are resolved and attached to their parent `Host` or `Application` objects.
        *   The `wemustrepeat()` method is called on items, allowing for custom logic.
        *   `create_templates()` method is called on items, processing their `template_rules` to decide which templates to render.
    3.  **Render Phase (`recipe.render()`):** The `render()` method is called on each item, which uses Jinja2 to process its selected templates and generate configuration strings. These strings are stored in the item's `config_files` attribute.
    4.  **Output Phase (`recipe.output()`):** Datarecipients are called. They receive the `recipe.objects` (containing all items with their rendered `config_files`) and write the configurations to their target (e.g., files, APIs).

Understanding this internal data flow is key for writing advanced datasources, custom item classes, or complex recipe logic.

### `coshsh.util` Module Functions

The `coshsh.util` module provides a collection of helper functions that are used internally by Coshsh and can also be beneficial for developers writing custom datasources, application classes, or complex template logic. Here are some of the key functions:

*   **`compare_attr(attr_name, params_dict, value_to_compare, ignorecase=False)`**
    *   **Purpose:** Flexibly compares the value of an attribute in a dictionary (`params_dict`) or an object against a specified `value_to_compare`.
    *   **Parameters:**
        *   `attr_name` (str): The name of the attribute/key to check in `params_dict`.
        *   `params_dict` (dict or object): The dictionary or object containing the attribute.
        *   `value_to_compare` (str or regex pattern): The value or regex pattern to compare against. If it starts with `~`, it's treated as a regex match. If it starts with `!~`, it's a negative regex match. If it starts with `!`, it's a negative exact match. Otherwise, it's an exact string match.
        *   `ignorecase` (bool, optional): If `True`, performs case-insensitive comparison (especially for regex). Defaults to `False`.
    *   **Return Value:** `True` if the comparison is successful, `False` otherwise. Returns `False` if `attr_name` is not in `params_dict`.
    *   **Example Usage:**
        ```python
        # In __mi_ident__ or __ds_ident__
        # params = {'type': 'LinuxServer', 'name': 'web01'}
        if coshsh.util.compare_attr('type', params, 'linux.*', ignorecase=True):
            # Matches if type is 'LinuxServer', 'linux_server', etc.
            pass
        if coshsh.util.compare_attr('name', params, '!~temp_.*'):
            # Matches if name does not start with 'temp_'
            pass
        ```

*   **`is_attr(attr_name, params_dict, value_to_compare, ignorecase=False)`**
    *   **Purpose:** A simplified version of `compare_attr` that essentially checks if an attribute exists and equals a certain value (exact match only, not regex). This function seems to be an older or less flexible counterpart to `compare_attr`. For new development, `compare_attr` is generally preferred due to its regex capabilities.
    *   **Parameters:** Same as `compare_attr`, but `value_to_compare` is typically a direct string.
    *   **Return Value:** `True` if the attribute exists and its string representation matches `value_to_compare` (case-insensitively if `ignorecase` is `True`).

*   **`substenv(text_string)`**
    *   **Purpose:** Substitutes environment variables referenced in a string with their actual values.
    *   **Parameters:**
        *   `text_string` (str): The string containing environment variable placeholders. Placeholders are in the format `%(ENV_VAR_NAME)%` or `%ENV_VAR_NAME%`.
    *   **Return Value:** The string with environment variables substituted. If an environment variable is not found, the placeholder might be left as is or replaced with an empty string, depending on internal handling (testing recommended for exact behavior).
    *   **Example Usage:**
        ```python
        # In a cookbook (.cfg) file:
        # log_dir = %(OMD_ROOT)/var/mylogs

        # In Python (Coshsh does this internally when parsing configs):
        # path = "%(OMD_ROOT)/var/log"
        # resolved_path = coshsh.util.substenv(path)
        # # if OMD_ROOT is /opt/omd, resolved_path becomes /opt/omd/var/log
        ```

*   **`str2bool(value)`**
    *   **Purpose:** Converts common string representations of boolean values (e.g., "yes", "true", "on", "1", "no", "false", "off", "0") into actual Python booleans (`True` or `False`).
    *   **Parameters:**
        *   `value` (any): The value to convert. If it's a string, it's checked against known boolean representations. If already a boolean, it's returned as is.
    *   **Return Value:** `True` or `False`. Non-boolean, non-string inputs might lead to `False` or errors.
    *   **Example Usage:**
        ```python
        # ssl_enabled_str = "yes" # from a config file or data
        # use_ssl = coshsh.util.str2bool(ssl_enabled_str) # use_ssl becomes True
        ```

*   **`setup_logging(logdir=None, logfilename=None, scrnloglevel=logging.INFO, fileloglevel=logging.DEBUG, backup_count=7)`**
    *   **Purpose:** Configures Coshsh's logging system. Sets up handlers for screen (console) output and file output.
    *   **Parameters:**
        *   `logdir` (str, optional): Directory where log files will be stored.
        *   `logfilename` (str, optional): Specific name for the log file. If `None`, a default name (like `coshsh.log`) might be used within `logdir`.
        *   `scrnloglevel` (int, optional): Logging level for console output (e.g., `logging.DEBUG`, `logging.INFO`). Defaults to `logging.INFO`.
        *   `fileloglevel` (int, optional): Logging level for file output. Defaults to `logging.DEBUG`.
        *   `backup_count` (int, optional): Number of old log files to keep when rotating. Defaults to 7.
    *   **Notes:** This is usually called internally by `Generator` based on cookbook settings or defaults.

*   **`switch_logging(logdir=None, logfile=None, scrnloglevel=None, fileloglevel=None, backup_count=None)`**
    *   **Purpose:** Allows changing the logging configuration dynamically, often used by a `Recipe` to switch to a recipe-specific log file.
    *   **Parameters:** Similar to `setup_logging`, allowing specific aspects of logging to be overridden.
*   **`restore_logging()`**
    *   **Purpose:** Restores a previously saved logging configuration. Used in conjunction with `switch_logging` to revert to a prior logging setup.

*   **`odict()` (Deprecated - Standard `dict` is ordered since Python 3.7)**
    *   **Purpose (Historically):** Provided an `OrderedDict` implementation. In modern Python (3.7+), standard dictionaries maintain insertion order, making a custom `odict` less critical. Coshsh uses it internally for `recipe.objects` to maintain a predictable order of item types.
    *   **Usage:** If you need ordered dictionaries for compatibility with older Python versions or for specific Coshsh internal structures, it might be used. However, for new code targeting Python 3.7+, `dict` itself is often sufficient.

*   **Dynamic Module Loading (Internal Utilities):**
    *   Functions like `load_python_module(name, _path)` are used internally by the `CoshshDatainterface` (and thus by Datasources, Items, etc.) to dynamically load Python modules from `classes_dir` paths. While powerful, users typically don't call these directly; they rely on the `__ds_ident__` and `__mi_ident__` mechanisms which use these utilities under the hood.

When developing custom Coshsh components, these utilities, especially `compare_attr` and `substenv`, can be very helpful.

### Writing Custom Jinja2 Extensions

Coshsh leverages the Jinja2 templating engine. You can extend Jinja2's capabilities by writing your own custom filters, tests, and global functions/variables, making them available within your `.tpl` templates.

Coshsh itself provides a set of useful extensions in `coshsh/jinja2_extensions.py`. These serve as good examples and are automatically available.

**How Coshsh Loads Custom User Extensions:**

If you want to add your *own* extensions, beyond those provided by Coshsh:
1.  **Create a Python Module:** Write a Python module (e.g., `my_project_jinja_ext.py`) that defines your custom filter, test, or global functions.
2.  **Place the Module:** Ensure this Python module is in a directory that is part of Python's `sys.path` when Coshsh runs. Often, placing it in one of the `classes_dir` specified in your recipe is sufficient, as these directories are typically added to `sys.path`.
3.  **Configure in Recipe:** In your recipe definition within the cookbook (`.cfg` file), use the `my_jinja2_extensions` parameter. This parameter should be a comma-separated list of strings, where each string specifies `module_name.function_name` or `module_name.class_name` for your extensions.
    *   Coshsh will attempt to import the specified module and then retrieve the function/class.
    *   **Naming Convention for Auto-Registration:** For Coshsh to automatically register them correctly with Jinja2:
        *   Custom filters should have names starting with `filter_` (e.g., `filter_mycustomfilter`). In the template, you'll use it as `{{ myvariable | mycustomfilter }}`.
        *   Custom tests should have names starting with `is_` (e.g., `is_customtest`). In the template, you'll use it as `{% if myvariable is customtest %}`.
        *   Custom globals (functions or variables) should have names starting with `global_` (e.g., `global_myhelperfunction`). In the template, you'll use it as `{{ myhelperfunction() }}` or `{{ myglobalvariable }}`.

**Example of Creating and Using Custom Extensions:**

1.  **Create `my_project_jinja_ext.py` (e.g., in a `classes_dir`):**
    ```python
    # my_project_jinja_ext.py

    # Custom Filter
    def filter_append_world(value):
        return f"{value} World"

    # Custom Test
    def is_even(number):
        return number % 2 == 0

    # Custom Global Function
    def global_site_prefix():
        return "SITE_A"

    # Custom Global Variable (less common to define directly like this for Jinja globals,
    # usually functions are preferred, or they are added directly to env.globals)
    # global_my_constant = "SOME_CONSTANT_VALUE"
    ```

2.  **Configure in your recipe (e.g., `my_cookbook.cfg`):**
    ```ini
    [recipe_my_special_recipe]
    datasources = some_data
    classes_dir = path/to/where_my_project_jinja_ext_is_located
    templates_dir = path/to/my_templates
    objects_dir = path/to/my_output
    my_jinja2_extensions = my_project_jinja_ext.filter_append_world, my_project_jinja_ext.is_even, my_project_jinja_ext.global_site_prefix
    ```

3.  **Use in a template (`.tpl` file):**
    ```jinja
    {# Using custom filter #}
    <p>{{ "Hello" | append_world }}</p>
    {# Output: <p>Hello World</p> #}

    {# Using custom test #}
    {% set my_number = 4 %}
    {% if my_number is even %}
    <p>{{ my_number }} is an even number.</p>
    {% else %}
    <p>{{ my_number }} is an odd number.</p>
    {% endif %}
    {# Output: <p>4 is an even number.</p> #}

    {# Using custom global function #}
    <p>Default Prefix: {{ site_prefix() }}</p>
    {# Output: <p>Default Prefix: SITE_A</p> #}
    ```

**Built-in Coshsh Jinja2 Extensions (`coshsh.jinja2_extensions.py`):**

Coshsh provides several useful extensions out of the box:

*   **Filters:**
    *   `re_sub(value, regex_pattern, replacement)`: Performs a regular expression substitution on `value`.
    *   `re_escape(value)`: Escapes special characters in `value` so it can be used safely within a regular expression.
    *   `service(application_object, service_name_suffix)`: Helps in generating consistent `define service { ... }` lines and may handle unique service name generation or registration internally. The `application_object` is typically the `application` variable available in application-specific templates.
    *   `host(host_object, host_name_suffix)`: Similar to `service` but for `define host { ... }`.
    *   `contact(contact_object, contact_name_suffix)`: Similar to `service` but for `define contact { ... }`.
    *   `custom_macros(item_object)`: Formats the `_MACRO` attributes of an item (Host, Application, etc.) for Nagios configuration output.
    *   `rfc3986(value)`: URL-encodes a string according to RFC 3986.
    *   `neighbor_applications(application_object, name_filter=None, type_filter=None)`: Retrieves other applications associated with the same host as the given `application_object`, optionally filtering by name or type.
*   **Tests:**
    *   `is_re_match(value, regex_pattern)`: Tests if `value` matches the given `regex_pattern`. Used like `{% if myvar is re_match("pattern") %}`.
*   **Globals:**
    *   `environ`: Provides access to environment variables within templates (e.g., `{{ environ.OMD_SITE }}`).

By defining your own extensions or leveraging the built-in ones, you can significantly enhance the logic and reusability of your Jinja2 templates in Coshsh.

## Advanced Topics

This section delves into more complex use cases and advanced features of Coshsh, enabling users to tackle sophisticated configuration generation scenarios.

### Multi-Stage Configuration Generation & Complex Workflows

While Coshsh recipes are typically self-contained, complex scenarios might require a multi-stage approach where the output of one process feeds into another. Coshsh doesn't have a direct "recipe chaining" feature within a single `coshsh-cook` run, but such workflows can be achieved in several ways:

1.  **Sequential `coshsh-cook` Runs:**
    *   One recipe can generate intermediate files (e.g., a pre-processed data file, a specific tool's configuration).
    *   A subsequent `coshsh-cook` run, using a different recipe, can then use a datasource (e.g., `datasource_csvfile` or a custom one) to read these intermediate files and produce the next stage of configurations.

2.  **Custom Datasources Creating New Item Types for Specialized Datarecipients:**
    *   The `TESTsnmptt` example showcases this powerfully.
        *   The `datasource_snmptt` reads `.snmptt` (MIB definition) files and creates custom `Item` objects called `mibconfigs`. These `mibconfigs` are not standard Nagios objects but internal Coshsh items representing the structure of each MIB.
        *   This same datasource also enriches standard `Application` objects (e.g., for a network device) with a detail called `trap_events`, linking them to the MIBs they implement.
        *   The recipe then uses *two* datarecipients:
            *   The default datarecipient (`>>>`) processes the standard `Application` objects. Their templates (e.g., `os_paloalto_traps.tpl` which includes `common_traps.tpl`) use the `trap_events` detail to generate Nagios passive service definitions for each SNMP trap.
            *   A custom `datarecipient_atomic` (configured as `checklogfiles_mibs` in the cookbook) specifically looks for items of type `mibconfigs`. It uses a unique template (`check_logfiles_snmptt.tpl`) to render these `mibconfigs` into Perl configuration files for the `check_logfiles` Nagios plugin. These Perl scripts, in turn, monitor the SNMP trap log and submit results to the passive services generated by the default datarecipient.
    *   This illustrates how Coshsh can generate configurations for external tools that are part of the overall monitoring ecosystem, all driven from the same initial data sources and recipe execution.

3.  **Generating Configuration for Other Tools (e.g., Prometheus):**
    *   The `TEST20` example demonstrates using Coshsh to generate configuration for non-Nagios systems.
    *   The `os_cisco.py` application class has a `TemplateRule` with `for_tool="prometheus"` and `suffix="json"`. This rule uses `exporter.tpl` to generate a JSON configuration file.
    *   A custom `datarecipient_snmp_exporter.py` is configured in the recipe. Its `output()` method is designed to look for items with rendered configurations tagged for the "prometheus" tool and writes them to a specific directory structure, creating JSON files suitable for the Prometheus SNMP Exporter.
    *   This shows the use of `TemplateRule` metadata to control which datarecipient processes which rendered output from an item.

### Working with Multiple Datasources in a Single Recipe

A single Coshsh recipe can be configured to use multiple datasources.

*   **Aggregation:** When a recipe specifies multiple datasources (e.g., `datasources = cmdb_api, local_csv_additions, network_scan_tool`), Coshsh processes them in the order listed.
*   **Shared Object Registry:** All datasources within a single recipe operate on the same shared internal object registry (`recipe.objects`).
*   **Use Cases:**
    *   **Data Enrichment:** A primary datasource (e.g., a CMDB API) can create initial `Host` objects. Subsequent datasources (e.g., a CSV file or another API) can then retrieve these existing host objects (using `self.get('hosts', host_fingerprint)`) and add more applications, monitoring details, or update attributes.
    *   **Combining Inventories:** Data from entirely different inventory systems can be merged. For example, one datasource could provide server hardware information, while another provides software deployment details for those same servers.
*   **Conflict Handling:**
    *   If two datasources attempt to add an item with the exact same fingerprint (e.g., a `Host` with the same `host_name`), the one processed **last** will typically "win." The `Item.__init__` method often updates the existing object with attributes from the new data, so it's more of an attribute merge/override than a full object replacement, but the last datasource to provide attributes for an item has the final say on those attribute values. Careful planning of datasource order and data consistency is important.

### Using Multiple Datarecipients

A recipe can also be configured to use multiple datarecipients simultaneously.

*   **Configuration:** List multiple datarecipient section names in the recipe's `datarecipients` parameter:
    ```ini
    [recipe_multi_output]
    datasources = my_main_data
    classes_dir = ...
    templates_dir = ...
    objects_dir = /opt/coshsh/output/nagios_configs ; For the default datarecipient
    datarecipients = >>>, prometheus_json_files, audit_db_writer

    [datarecipient_prometheus_json_files]
    type = snmp_exporter_custom # Assuming a custom datarecipient
    output_path = /opt/coshsh/output/prometheus_targets

    [datarecipient_audit_db_writer]
    type = database_logger # Another custom datarecipient
    db_connection_string = ...
    ```
*   **Functionality:** After the `render` phase, the `recipe.output()` method will call the `output()` method of each configured datarecipient, passing them all the processed `recipe.objects`.
*   **Use Cases:**
    *   **Multi-Format Output:** Generate Nagios configuration files using the default datarecipient (`>>>`) while simultaneously generating JSON files for Prometheus (via a custom datarecipient like `snmp_exporter_custom`) and also logging audit information to a database (via another custom datarecipient like `database_logger`).
    *   **Targeted Output:** As seen in `TESTsnmptt`, one datarecipient handles general Nagios configs, while another (`datarecipient_atomic`) handles only specific item types (`mibconfigs`) to generate specialized `check_logfiles` configurations. This is often achieved by the custom datarecipient inspecting item types or `TemplateRule` metadata (like `for_tool`).

### Environment Variables in Configuration

Coshsh allows the use of environment variables within your cookbook configuration files (`.cfg`). This is particularly useful for defining paths that might change depending on the deployment environment (e.g., development, testing, production) or within an OMD (Open Monitoring Distribution) site.

*   **Syntax:** Use `%(ENV_VAR_NAME)%` or `%ENV_VAR_NAME%`.
*   **Example:**
    ```ini
    [defaults]
    # OMD_ROOT is typically set in an OMD site environment
    log_dir = %(OMD_ROOT)/var/coshsh/logs
    pid_dir = %(OMD_ROOT)/tmp/run/coshsh

    [recipe_my_app]
    classes_dir = %(MY_APP_BASE_PATH)/coshsh_classes, recipes/default/classes
    objects_dir = %(OMD_ROOT)/etc/nagios/conf.d/my_app
    ```
*   The `coshsh.util.substenv()` function is responsible for this substitution when configurations are loaded.

### Using `coshsh-create-template-tree` for Service Templates

While not strictly a configuration generation topic for `coshsh-cook`, the `coshsh-create-template-tree` script is a valuable utility for managing Nagios/Icinga service template inheritance.

*   **Purpose:** To quickly generate a hierarchical tree of service template configuration files. This promotes a DRY (Don't Repeat Yourself) approach to service definitions.
*   **Use Case:** Imagine you want a standard set of properties for all services, then more specific ones for application-related services, then even more specific ones for database services, and finally, unique settings for MySQL services. `coshsh-create-template-tree` can build this structure.
    If you run:
    ```bash
    coshsh-create-template-tree --cookbook your.cfg --recipe some_recipe --template app_db_mysql_specific_check
    ```
    It would create (in `<objects_dir_of_some_recipe>/static/service_templates/`):
    *   `app_db_mysql_specific_check.cfg` (using `app_db_mysql_specific`)
    *   `app_db_mysql_specific.cfg` (using `app_db_mysql`)
    *   `app_db_mysql.cfg` (using `app_db`)
    *   `app_db.cfg` (using `app`)
    *   `app.cfg` (potentially using a global template like `generic-service-template`)
*   Each file defines a service template (`register 0`) that `use`s its parent, allowing for cascading inheritance of monitoring parameters. This structure is then referenced in your actual service check templates (e.g., `use app_db_mysql_specific_check;`).

### Understanding Object Fingerprints (`item.fingerprint()`)

Each configuration item (`Host`, `Application`, etc., all inheriting from `coshsh.item.Item`) has a `fingerprint()`.

*   **Purpose:** This method generates a unique string identifier for that specific instance of an item.
*   **Generation:**
    *   For `Host` objects, the fingerprint is typically just the `host_name`.
    *   For `Application` objects, it's usually a combination like `host_name + "+" + application_name + "+" + application_type`.
    *   Subclasses can override the `fingerprint(params)` class method to define a custom fingerprinting scheme if needed.
*   **Importance:**
    *   **Unique Identification:** Used as the key when storing items in the `recipe.objects` dictionary, ensuring each distinct item is stored only once.
    *   **Data Merging/Updating:** If multiple datasources provide information for an item with the same fingerprint, Coshsh will typically update the existing item with attributes from the later datasource.
    *   **Preventing Duplicates:** Ensures that the same conceptual item isn't processed or generated multiple times if it appears in different data sources or different parts of the input data (assuming its identifying attributes are consistent).

Understanding these advanced topics allows for more sophisticated use of Coshsh, enabling complex data integrations, customized output workflows, and better management of large-scale monitoring configurations.

## Troubleshooting

This chapter provides guidance on common issues you might encounter while using Coshsh and tips for debugging them.

### General Debugging Steps

1.  **Enable Debug Logging:** This is often the first and most crucial step.
    *   **Command-Line:** Use the `--debug` flag with `coshsh-cook`:
        ```bash
        coshsh-cook --cookbook your_cookbook.cfg --recipe your_recipe --debug
        ```
    *   **Cookbook Configuration:** You can set a default more verbose log level in your cookbook's `[defaults]` section or a recipe-specific level:
        ```ini
        [defaults]
        log_level = DEBUG

        [recipe_specific_debug]
        # ... other params ...
        log_level = DEBUG
        # Ensure log_file is defined if you want recipe-specific log files
        log_file = %(OMD_ROOT)/var/log/coshsh/my_specific_recipe_debug.log
        ```
    *   **Log Locations:** Check the global log file (often `coshsh.log` in the `log_dir` specified in `[defaults]` or a system path like `/tmp` if not set) or the recipe-specific `log_file` if configured. In OMD environments, Coshsh logs might also appear in standard OMD log locations.

2.  **Isolate the Problem:**
    *   **Single Recipe:** If your cookbook has multiple recipes, try running only the problematic one using `coshsh-cook --recipe your_failing_recipe`.
    *   **Simplify Datasources:** If you suspect a datasource, try replacing it temporarily with `datasource_simplesample` or a very small, known-good CSV file to see if the rest of the recipe logic (classes, templates) works.
    *   **Simplify Templates:** Comment out sections of your `.tpl` files (using `{# Jinja2 comment #}`) to pinpoint which part is causing a rendering error. Start with a very minimal template and gradually add complexity.
    *   **Reduce Data:** If processing large datasets, try with a minimal subset of data that still reproduces the issue.

3.  **Validate Input Data:**
    *   **CSVs:** Check for correct delimiters, consistent column counts, proper quoting (if values contain delimiters or newlines), and correct header names. Ensure file encodings are consistent.
    *   **APIs/Databases:** If using custom datasources, verify API responses or database query results are as expected. Log the raw data fetched by your datasource.

### Common Issues & Solutions

*   **Configuration File Parsing Errors (`.cfg` files):**
    *   **Symptom:** `coshsh-cook` fails immediately, often with a Python `configparser` error message indicating issues in a `.cfg` file (e.g., "Source contains parsing errors: ...").
    *   **Solution:** Carefully check for INI syntax errors (e.g., missing `=`, incorrect section headers `[section_name]`), misspelled section names (e.g., `[recipe my_recipe]` instead of `[recipe_my_recipe]`), or misspelled parameter names. Ensure paths are correctly specified.

*   **Datasource Errors:**
    *   **`__ds_ident__` Not Returning Class / "Datasource X is unknown":**
        *   **Symptom:** Coshsh logs an error like "Datasource <your_ds_name> is unknown."
        *   **Solution:**
            1.  Verify the `type` parameter in your `[datasource_<your_ds_name>]` section in the cookbook matches the string your `__ds_ident__` function in the datasource Python module is checking for.
            2.  Ensure your datasource Python file (e.g., `datasource_mycmdb.py`) is located in one of the directories specified in the recipe's `classes_dir` (or a global `classes_dir`).
            3.  Check for Python import errors within your datasource file itself if it has external dependencies.
    *   **Errors in `open()` or `read()` (e.g., `DatasourceNotAvailable`, `DatasourceCorrupt`):**
        *   **Symptom:** Python exceptions originating from your datasource code, or specific Coshsh datasource exceptions.
        *   **Solution:** This usually points to issues within your custom datasource logic.
            *   `open()`: Problems connecting to external services (network issues, wrong endpoint, authentication failure).
            *   `read()`: Errors parsing data, unexpected data format from the source, logic errors in how you create `Host`/`Application`/`Detail` objects.
            *   Add detailed `logger.debug()` or `logger.error()` statements within your `open()` and `read()` methods to trace the execution flow and inspect data.
    *   **Data Not Being Read as Expected (e.g., from CSVs):**
        *   **Solution:**
            *   For `datasource_csvfile`, double-check `dir`, `csv_hosts_file` (and others like `csv_applications_file`, `csv_applicationdetails_file`), `name_for_files`, and `csv_delimiter` parameters in the cookbook.
            *   Ensure CSV filenames match what `datasource_csvfile` expects (e.g., `<name_for_files>_hosts.csv` or the exact name given in `csv_hosts_file`).
            *   Verify CSV header names match the keys you expect to use when creating `Host` and `Application` objects.

*   **Application/OS Class Loading Errors:**
    *   **`__mi_ident__` Not Returning Class:**
        *   **Symptom:** Application objects are treated as `GenericApplication` instead of your custom class, or expected templates are not applied.
        *   **Solution:**
            1.  Verify the `type` attribute of your application data (e.g., in `*_applications.csv` or from your API) matches what the `__mi_ident__` function in your `app_*.py` or `os_*.py` file is checking for. Remember that `type` values in application data are often converted to lowercase by Coshsh before `__mi_ident__` is called.
            2.  Ensure the class file is in a valid `classes_dir` for the recipe.
            3.  Check for Python import errors within your custom class file.
    *   **Errors in Custom Class `__init__` or other methods (e.g., `wemustrepeat`):**
        *   **Symptom:** Python tracebacks pointing to lines within your custom application/OS class.
        *   **Solution:** Standard Python debugging. Use logging within these methods to understand the state of `params` or `self`.

*   **Template Rendering Errors (Jinja2):**
    *   **Symptom:** Errors from Jinja2 like `jinja2.exceptions.TemplateNotFound`, `jinja2.exceptions.TemplateSyntaxError`, or `jinja2.exceptions.UndefinedError`. The `render_errors` count in the final log summary will also be greater than zero.
    *   **Solutions:**
        *   **`TemplateNotFound`**:
            1.  Check that the `template` name in your `TemplateRule` (e.g., `template="my_template"`) correctly matches the filename (e.g., `my_template.tpl`).
            2.  Verify the template file exists in one of the `templates_dir` paths configured for the recipe.
        *   **`TemplateSyntaxError`**: There's a syntax problem in your `.tpl` file (e.g., mismatched `{% %}` or `{{ }}`, incorrect filter usage). The error message usually gives a line number.
        *   **`UndefinedError: 'X' is undefined`**: The template is trying to use a variable `{{ X }}` or `{{ item.X }}` that doesn't exist on the object being rendered.
            *   This is very common. It means the data wasn't provided by the datasource as expected, an attribute name is misspelled in the template, or a `MonitoringDetail` that was supposed to populate that attribute didn't run or work correctly.
            *   **Debugging `UndefinedError`:**
                *   Temporarily add `{{ application | pprint }}` or `{{ host | pprint }}` (if you have `pprint` available as a filter, or add it as a custom extension) at the top of your template to dump all available attributes of the object.
                *   Add logging in your custom class's `__init__` or your datasource's `read()` method to verify the attribute is being set.
        *   **General Template Debugging:** Simplify complex templates by commenting out sections to isolate the problematic part.

*   **Output File Issues:**
    *   **Files Not Created:**
        *   Check `objects_dir` path in the recipe and ensure Coshsh has write permissions.
        *   If using custom datarecipients, check their logic and any `output_path` parameters.
        *   If `render_errors` is non-zero for an item, its configuration files might not be written.
    *   **Incorrect Content:** This usually traces back to issues in:
        1.  The data provided by the datasource.
        2.  The logic in custom Application/OS classes that might modify or set attributes.
        3.  The logic within the Jinja2 templates themselves.

*   **"Too many open files" errors:**
    *   **Symptom:** The Coshsh process crashes with this operating system error.
    *   **Cause:** This can happen in very large setups if Coshsh is trying to open/process an extremely large number of small files (e.g., many tiny template files per item, or datasources reading thousands of small data snippets individually).
    *   **Solution:**
        *   Increase the per-process file descriptor limit (`ulimit -n`) on the system running Coshsh.
        *   Review if your datasource or templating strategy can be optimized to handle files more in batches. (This is an advanced optimization).

*   **PID File Issues ("Recipe already running" or "Cannot write PID file"):**
    *   **Symptom:** Coshsh refuses to run a recipe, stating it's already running, or that it cannot write the PID file.
    *   **Solution:**
        *   **Already Running:** Check if another instance of `coshsh-cook` for that specific recipe is genuinely active.
        *   **Stale PID File:** If no other instance is running, the previous run might have exited uncleanly. Manually delete the relevant `.pid` file from the `pid_dir` (configured in `[defaults]` or the recipe, often in `tmp/run/` within an OMD site). The PID filename usually includes the recipe name.
        *   **Cannot Write:** Check permissions for Coshsh to write to the configured `pid_dir`.

### Interpreting Log Messages

Familiarize yourself with common Coshsh log patterns (especially with `--debug`):

*   `INFO - recipe <name> init`: A recipe is being initialized.
*   `INFO - recipe <name> classes_dir ...` / `templates_dir ...`: Shows the paths being used.
*   `INFO - open datasource <ds_name>`: A datasource's `open()` method is called.
*   `INFO - recipe <name> read from datasource <ds_name> X hosts, Y applications`: Successful data read.
*   `INFO - load items to datarecipient_coshsh_default`: Items are being prepared for the default output handler.
*   `INFO - number of files before: X hosts, Y applications` / `after: ...`: Useful for the default datarecipient to track changes.
*   `DEBUG - item ... uses ...`: Shows which class is being used for an item (helpful for `__mi_ident__` debugging).
*   `DEBUG - item ... create template ... using ...`: Shows which template rule is being matched for an item.
*   `ERROR - skipping recipe <name> (TemplateSyntaxError: ...)`: A template error occurred.
*   `INFO - recipe <name> completed with X problems`: Summary of rendering errors.

### When to Ask for Help

If you're stuck:
1.  **Check Existing Issues:** Look at the project's issue tracker on its hosting platform (e.g., GitHub issues) to see if someone has reported a similar problem.
2.  **Formulate a Good Question/Bug Report:**
    *   Clearly state the Coshsh version you are using.
    *   Provide relevant snippets of your cookbook file (`.cfg`).
    *   Show minimal, reproducible examples of your input data (e.g., CSV rows).
    *   Include the full error message and Python traceback if available.
    *   Describe what you expected to happen and what actually happened.
    *   Include relevant log output, especially with `--debug` enabled.

Clear and detailed reports make it much easier for others to help you.

## Contributing

Please refer to the `CONTRIBUTING.md` file for guidelines on how to contribute to Coshsh.
