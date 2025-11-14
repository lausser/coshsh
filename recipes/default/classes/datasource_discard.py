#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Discard Datasource Plugin

This plugin discards/empties all monitoring objects from previous datasources.

Plugin Identification:
---------------------
Identifies datasource configurations with type = "discard".

Purpose:
--------
Empties all monitoring object collections, effectively discarding any data
read by previous datasources in the recipe chain. This is useful for:
    - Resetting state between datasource operations
    - Filtering out all previous data
    - Starting fresh in multi-datasource configurations
    - Testing scenarios requiring empty object collections

Use Cases:
----------
- Reset monitoring configuration between recipe phases
- Discard test data before reading production data
- Clear state when datasources are conditionally applied
- Testing with empty object sets

Behavior:
---------
When this datasource's read() method is called, it:
1. Takes the existing objects dictionary (hosts, applications, contacts, etc.)
2. Empties each collection by setting each to an empty dictionary
3. Preserves the objects structure but removes all content

This effectively clears:
    - objects['hosts'] = {}
    - objects['applications'] = {}
    - objects['contacts'] = {}
    - objects['contactgroups'] = {}
    - objects['appdetails'] = {}
    - (any other object collections)

Configuration Example:
---------------------
Cookbook configuration:
    [datasource_reset]
    type = discard
    name = reset_all

Usage in Recipe:
----------------
In a recipe with multiple datasources:
    [recipe_prod]
    datasources = csv1, discard_ds, csv2

    # csv1 reads initial data
    [datasource_csv1]
    type = csv
    name = initial
    dir = /path/to/csv1

    # discard_ds empties everything
    [datasource_discard_ds]
    type = discard
    name = reset

    # csv2 starts with empty objects
    [datasource_csv2]
    type = csv
    name = final
    dir = /path/to/csv2

Result: Only csv2 data is used; csv1 data is discarded.

When to Use:
------------
Use this datasource when you need to:
- Conditionally filter out all previous data
- Reset state between complex datasource chains
- Test with empty object collections
- Implement custom filtering logic (discard then selectively re-read)

When NOT to Use:
----------------
- For filtering specific objects (use filter parameter instead)
- For merging datasources (just chain them without discard)
- In simple single-datasource recipes (no need to discard)

Classes:
--------
- DsDiscard: Datasource that empties all object collections
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any

import coshsh
from coshsh.datasource import Datasource
from coshsh.util import compare_attr

logger = logging.getLogger('coshsh')


def __ds_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify discard datasource configurations.

    Called by the plugin factory system to determine if a datasource
    configuration should use the DsDiscard class.

    Args:
        params: Datasource configuration dictionary

    Returns:
        DsDiscard class if type="discard"
        None if no match

    Example:
        params = {'type': 'discard', 'name': 'reset'}
        Returns: DsDiscard class

        params = {'type': 'csv', 'name': 'data'}
        Returns: None
    """
    if params is None:
        params = {}

    if coshsh.util.compare_attr("type", params, "^discard$"):
        return DsDiscard
    return None


class DsDiscard(coshsh.datasource.Datasource):
    """Datasource that discards all monitoring objects.

    Empties all object collections, removing any data read by previous
    datasources in the recipe chain.

    This datasource takes the existing objects dictionary and empties
    each collection (hosts, applications, contacts, etc.) by setting
    each to an empty dictionary.

    Attributes:
        objects: Dictionary of object collections (inherited from Datasource)
            After read(): All collections are empty dictionaries

    Configuration:
        [datasource_reset]
        type = discard
        name = reset_all

    Example:
        # Before discard datasource:
        objects = {
            'hosts': {'host1': <Host>, 'host2': <Host>},
            'applications': {'app1': <App>, 'app2': <App>}
        }

        # After discard datasource read():
        objects = {
            'hosts': {},
            'applications': {}
        }
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize discard datasource.

        Args:
            **kwargs: Datasource configuration parameters
                Passed to parent Datasource class
        """
        super().__init__(**kwargs)

    def read(
        self,
        filter: Optional[str] = None,
        objects: Optional[Dict[str, Dict[str, Any]]] = None,
        force: bool = False,
        **kwargs: Any
    ) -> None:
        """Read and discard all monitoring objects.

        Empties all object collections by setting each collection to
        an empty dictionary. This effectively discards all data read
        by previous datasources.

        Args:
            filter: Filter parameter (ignored - all objects are discarded)
            objects: Dictionary of object collections to empty
                If None, uses empty dictionary
            force: Force read even if datasource is not current (ignored)
            **kwargs: Additional parameters (ignored)

        Example:
            datasource = DsDiscard(name='reset', type='discard')

            # Before read:
            objects = {
                'hosts': {'host1': <Host>},
                'applications': {'app1': <App>}
            }

            # Execute discard:
            datasource.read(objects=objects)

            # After read:
            objects = {
                'hosts': {},
                'applications': {}
            }

        Note:
            - All parameters except 'objects' are ignored
            - The filter parameter has no effect (all data is discarded)
            - Object keys are preserved, only contents are emptied
        """
        if objects is None:
            objects = {}

        self.objects = objects
        for k in self.objects.keys():
            self.objects[k] = {}
