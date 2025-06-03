# Coshsh Comprehensive Documentation

{:toc}

## Introduction

Coshsh (Configuration SHell SHaper) is a versatile and powerful configuration generator, primarily designed to automate the creation of configurations for monitoring systems such as Nagios, Icinga, and Naemon. Its flexible architecture also allows it to generate configurations for other systems, like Prometheus (e.g., via `datarecipient_prometheus_snmp.py` for SNMP exporter targets) or any other text-based configuration format.

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
    host_name,address,os_type
    server01,192.168.1.10,myos
    ```
*   `my_simple_coshsh_project/data/inventory_apps.csv`:
    ```csv
    host_name,app_name,app_type
    server01,os,myos
    ```
    *(Note: `app_name` is often "os" for operating system type applications, and `app_type` matches the `os_type` from the hosts file or a more specific OS version).*

**Step 2: Create Custom OS Class**

*   `my_simple_coshsh_project/example_classes/os_myos.py`:
    ```python
    import coshsh
    from coshsh.application import Application
    from coshsh.templaterule import TemplateRule

    # This function helps Coshsh identify which class to use for which application type
    def __mi_ident__(params={}):
        if params.get("type") == "myos": # 'myos' comes from our CSV data
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
    [datasource_example_csv]
    type = csv
    # Define which CSV files this datasource should read.
    # The part before '_hosts.csv' or '_applications.csv' should match the datasource name
    # or be explicitly mapped if filenames differ. Here, we'll assume the default
    # datasource_csvfile.py will look for files based on the 'dir' and its own name.
    # For more explicit control, you can use:
    # csv_hosts_file = ../data/inventory_hosts.csv
    # csv_applications_file = ../data/inventory_apps.csv
    dir = ../data
    # This tells the csv datasource to look for inventory_hosts.csv, inventory_apps.csv, etc.
    # if we name the datasource [datasource_inventory]
    # For simplicity here, we'll assume the default CSV handler might pick up any CSVs
    # or one might need to be more specific in a real setup (e.g., by naming files
    # example_csv_hosts.csv or using explicit file parameters in the datasource section).
    # Let's assume for this example, we'll rename our CSV files to:
    # example_csv_hosts.csv and example_csv_applications.csv in the ../data directory.

    # Corrected for clarity and explicit file naming for the CSV datasource:
    # Ensure your files in ../data are named example_csv_hosts.csv and example_csv_applications.csv
    csv_hosts_file = ../data/inventory_hosts.csv
    csv_applications_file = ../data/inventory_apps.csv
    # If your actual CSV files are named inventory_hosts.csv etc., and you want to use
    # [datasource_inventory] then set:
    # name_for_files = inventory

    [recipe_simple_example]
    datasources = example_csv
    classes_dir = ../example_classes
    templates_dir = ../example_templates
    objects_dir = ../output_configs
    # By default, Coshsh uses classes from recipes/default/classes.
    # The paths here are relative to the cookbook file's location.
    # For a real setup, you might also include default paths:
    # classes_dir = ../example_classes,%(OMD_ROOT)/share/coshsh/recipes/default/classes
    # templates_dir = ../example_templates,%(OMD_ROOT)/share/coshsh/recipes/default/templates
    ```
    *Self-correction for the example.cfg: The default CSV datasource handler (`datasource_csvfile.py`) typically expects files named `<datasourcename>_hosts.csv`, etc. or specific parameters like `csv_hosts_file`. The example will be clearer if we specify `csv_hosts_file` and `csv_applications_file`.*

    Let's refine `my_simple_coshsh_project/cookbook/example.cfg` assuming our CSV files are `inventory_hosts.csv` and `inventory_apps.csv`:
    ```ini
    [datasource_inventory_data]
    type = csv
    dir = ../data
    # Explicitly point to the CSV files
    csv_hosts_file = inventory_hosts.csv
    csv_applications_file = inventory_apps.csv
    # Optional: if your detail files follow a pattern like inventory_applicationdetails.csv
    csv_applicationdetails_file = inventory_applicationdetails.csv # Add if you have this file

    [recipe_simple_example]
    datasources = inventory_data
    classes_dir = ../example_classes
    templates_dir = ../example_templates
    objects_dir = ../output_configs
    # To include Coshsh default classes and templates (recommended):
    # classes_dir = ../example_classes,recipes/default/classes
    # templates_dir = ../example_templates,recipes/default/templates
    # (Adjust paths to defaults based on your Coshsh installation if not using OMD)
    ```

**Step 5: Run Coshsh-Cook**

Navigate to the `my_simple_coshsh_project/cookbook/` directory (or ensure your paths in `example.cfg` are correct relative to where you run the command):

```bash
coshsh-cook --cookbook example.cfg --recipe simple_example
```
*(If you're not in an OMD environment, you might need to ensure `coshsh-cook` is in your PATH and Coshsh library is in PYTHONPATH, or adjust relative paths in the cookbook to absolute paths for `classes_dir` and `templates_dir` to point to `recipes/default` if you want to use them).*

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
    *   **Role:** Python classes are used to define the specific behavior, attributes, and template associations for different types of configuration items, particularly applications and operating systems. They allow you to model your infrastructure elements in an object-oriented way.
    *   **Location:** These classes are typically stored in Python files (e.g., `os_linux.py`, `app_apache.py`) within a `classes_dir` specified by a recipe.
    *   **`__mi_ident__(params={})` Function:** Each such Python module must contain this "Managed Item Identifier" function. When Coshsh processes an item (e.g., an application defined in a CSV row), it calls `__mi_ident__` with the item's parameters (like `params['type']`). The function returns the specific Python class (e.g., `return LinuxOS`) if it's designed to handle that type of item, or `None` otherwise. This allows Coshsh to dynamically select and instantiate the correct class for each item.
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

*   **Purpose:** A null datasource that, when its `read()` method is called, does not add any `Host`, `Application`, or other items to the Coshsh recipe.
*   **Cookbook Configuration (`type = discard`):**
    ```ini
    [datasource_no_data_source]
    type = discard
    # This datasource takes no parameters.
    ```
*   **Use Cases:**
    *   Testing recipes that might generate purely static configurations without dynamic inventory data.
    *   Temporarily disabling a data source in a recipe without removing its section from the cookbook.
    *   Testing specific phases of a recipe (like template rendering with dummy objects, or datarecipient logic) where the data input part is not relevant for that particular test.

These default datasources provide essential capabilities for getting started with Coshsh and handling common scenarios. For more complex needs, you would typically write your own datasource class.

## Writing Your Own Datasource
*   Structure of a Datasource Python File
*   The `__ds_ident__` Function
*   Implementing `open()`, `read()`, and `close()`
*   Creating `Host` and `Application` Objects

## Writing Classes and Templates for New Application Types
*   Structure of an `app_*.py` or `os_*.py` File
*   The `__mi_ident__` Function
*   Defining `template_rules`
*   Creating Corresponding `.tpl` Template Files
*   Using `MonitoringDetail`

## Reference Manual
*   Interacting with Recipe Data (Adding and Accessing Items)
*   `coshsh.util` Module Functions
*   Writing Custom Jinja2 Extensions

## Advanced Topics

## Troubleshooting

## Contributing (Placeholder)
