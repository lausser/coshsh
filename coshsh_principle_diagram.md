```mermaid
graph TD
    subgraph External World
        ExtData["External Data Sources (CMDB, CSV, API)"]
        User["User / Operator"]
    end

    subgraph CoshshConfiguration["Coshsh Configuration"]
        Cookbook["Cookbook (.cfg)"]
        DS_Classes["Datasource Classes (Python in classes_dir)"]
        AppOS_Classes["Application/OS Classes (Python in classes_dir)"]
        TRules["Template Rules (defined in AppOS_Classes)"]
        Templates["Templates (Jinja2 .tpl in templates_dir)"]
    end

    subgraph CoshshExecution["Coshsh Execution"]
        Engine["Coshsh Engine (coshsh-cook)"]
        Recipe["Recipe (section in Cookbook)"]
        ProcessedItems["Processed/Specialized Data Items (App/OS Class Instances)"]
    end

    subgraph MonitoringSystem["Target Monitoring System"]
        direction LR
        Output["Output Directory (objects_dir)"]
        MonitoringCore["Monitoring Core (Nagios, Icinga, Prometheus, etc.)"]
    end

    User -- Invokes & Edits --> Cookbook
    Cookbook -- Defines --> Recipe
    Cookbook -- Configures --> DS_Classes
    Cookbook -- Specifies paths for --> AppOS_Classes
    Cookbook -- Specifies paths for --> Templates

    Recipe -- Uses --> DS_Classes
    Recipe -- References paths for --> AppOS_Classes
    Recipe -- References paths for --> Templates
    Recipe -- Specifies --> Output

    ExtData -- Pulled by --> DS_Classes
    DS_Classes -- Feeds raw data items --> Engine

    Engine -- Executes --> Recipe
    Engine -- "Instantiates & Specializes items using" --> AppOS_Classes
    AppOS_Classes -- "Contain" --> TRules
    AppOS_Classes -- "Yield" --> ProcessedItems

    Engine -- "Processes" --> ProcessedItems
    ProcessedItems -- "Have associated" --> TRules
    Engine -- "Consults" --> TRules
    Engine -- "Selects & Uses based on rules" --> Templates

    Templates -- "Render item's data into config string" --> Engine
    Engine -- "Writes generated files" --> Output
    Output -- "Consumed by" --> MonitoringCore
```
