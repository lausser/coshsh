# Coshsh Plugin Development Guide

This document describes the plugin architecture and interfaces for extending coshsh functionality.

## Plugin Types

Coshsh uses a dynamic plugin loading system with several plugin types:

### Application Plugins (`app_*.py`)
Handle specific application monitoring logic.

**Required Interface:**
```python
from typing import Dict, Any

def __mi_ident__(params: Dict[str, Any]) -> bool:
    """
    Identify if this plugin handles the given CMDB data.
    
    Args:
        params: CMDB data dictionary with keys like 'name', 'type', 'component', etc.
        
    Returns:
        True if this plugin should handle this application, False otherwise
    """
    pass

class MyApplication(Application):
    """Custom application class inheriting from coshsh.application.Application"""
    pass
```

### Operating System Plugins (`os_*.py`)
Handle OS-specific monitoring configurations.

**Required Interface:**
```python
def __mi_ident__(params: Dict[str, Any]) -> bool:
    """
    Identify if this plugin handles the given OS type.
    
    Args:
        params: CMDB data dictionary, typically checking 'os' field
        
    Returns:
        True if this plugin should handle this OS, False otherwise
    """
    pass
```

### Datasource Plugins (`datasource_*.py`)
Handle reading data from specific CMDB systems.

**Required Interface:**
```python
def __ds_ident__(params: Dict[str, Any]) -> bool:
    """
    Identify if this datasource can handle the given configuration.
    
    Args:
        params: Configuration parameters for the datasource
        
    Returns:
        True if this datasource plugin should be used, False otherwise
    """
    pass

class MyDatasource(Datasource):
    """Custom datasource inheriting from coshsh.datasource.Datasource"""
    
    def read(self) -> None:
        """Read data from the source and populate self.objects"""
        pass
```

### Data Recipient Plugins (`datarecipient_*.py`)
Handle output formatting and destination.

**Required Interface:**
```python
def __dr_ident__(params: Dict[str, Any]) -> bool:
    """
    Identify if this recipient handles the given output configuration.
    
    Args:
        params: Output configuration parameters
        
    Returns:
        True if this recipient plugin should be used, False otherwise
    """
    pass
```

### Detail Plugins (`detail_*.py`)
Handle specific monitoring details and metrics.

**Required Interface:**
```python
def __detail_ident__(params: Dict[str, Any]) -> bool:
    """
    Identify if this detail plugin handles the given parameters.
    
    Args:
        params: Detail configuration parameters
        
    Returns:
        True if this detail plugin should be used, False otherwise
    """
    pass
```

## CMDB Data Contract

All plugins receive CMDB data as `Dict[str, Any]` with these common fields:

### Host Data
- `host_name: str` - Hostname
- `address: str` - IP address or FQDN
- `type: str` - Host type
- `os: str` - Operating system
- `hardware: str` - Hardware information (optional)
- `virtual: str` - Virtualization info (optional)
- `location: str` - Physical location (optional)
- `department: str` - Department/team (optional)

### Application Data
- `name: str` - Application name
- `type: str` - Application type (e.g., 'mysql', 'apache')
- `component: str` - Component name (optional)
- `version: str` - Version (optional)
- `patchlevel: str` - Patch level (optional)
- `host_name: str` - Associated host

## Plugin Development Best Practices

1. **Type Hints**: Use type hints for all public interfaces
2. **Error Handling**: Use specific exception types, avoid bare `except:`
3. **Documentation**: Document the CMDB fields your plugin expects
4. **Testing**: Create test cases with sample CMDB data
5. **Logging**: Use the `logger` instance for debugging

## Example Plugin

```python
# app_myservice.py
import logging
from typing import Dict, Any
from coshsh.application import Application

logger = logging.getLogger('coshsh')

def __mi_ident__(params: Dict[str, Any]) -> bool:
    """Identify MyService applications."""
    return (
        params.get('type', '').lower() == 'myservice' and
        params.get('component', '').lower() in ['web', 'api']
    )

class MyServiceApplication(Application):
    """Custom monitoring for MyService applications."""
    
    def create_templates(self) -> None:
        """Generate monitoring templates for MyService."""
        logger.debug(f"Creating templates for {self.name}")
        # Implementation here
        pass
```

## Plugin Loading Process

1. Coshsh scans for plugin files matching naming patterns
2. For each CMDB record, calls `__*_ident__` functions with data
3. First plugin returning `True` gets instantiated with the data
4. Plugin class replaces the base class via `self.__class__ = PluginClass`
5. Plugin-specific methods handle monitoring configuration

This architecture allows flexible, data-driven plugin selection without hardcoded rules.