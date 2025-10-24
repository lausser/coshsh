#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file belongs to coshsh.
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from __future__ import annotations

from configparser import RawConfigParser
from typing import List, Union


class CoshshConfigParser(RawConfigParser):
    """Extended ConfigParser with inheritance support via 'isa' directive.

    This parser extends RawConfigParser to support configuration inheritance.
    If a section contains an 'isa' key, it inherits all keys from the referenced
    section (unless already defined in the current section).

    This allows DRY configuration where common settings can be defined once
    and inherited by multiple sections.

    Example:
        [base_datasource]
        dir = /data
        type = csv

        [datasource_prod]
        isa = base_datasource
        name = production
        # Inherits: dir=/data, type=csv

        [datasource_test]
        isa = base_datasource
        name = test
        dir = /testdata  # Override inherited dir
    """

    def read(self, files: Union[str, List[str]]) -> List[str]:
        """Read and parse configuration files with inheritance support.

        After reading the files normally, processes 'isa' directives to
        implement configuration inheritance.

        Args:
            files: Filename or list of filenames to read

        Returns:
            List of successfully read filenames
        """
        result = super().read(files)

        # Process inheritance: sections with 'isa' key inherit from referenced section
        for section in self._sections.values():
            if "isa" in section and section["isa"] in self._sections:
                parent_section = self._sections[section["isa"]]
                for key in parent_section:
                    # Inherit key if not already defined and not the 'isa' directive itself
                    if key not in section and key != "isa":
                        section[key] = parent_section[key]

        return result

