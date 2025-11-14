#!/usr/bin/env python
#-*- encoding: utf-8 -*-
#
# Copyright Gerhard Lausser.
# This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Discard datarecipient - outputs nothing (used for dry-run/testing)."""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional
import coshsh
from coshsh.datarecipient import Datarecipient
from coshsh.util import compare_attr


logger = logging.getLogger('coshsh')


def __dr_ident__(params: Optional[Dict[str, Any]] = None) -> Optional[type]:
    """Identify discard datarecipient.

    Args:
        params: Parameters with 'type' key

    Returns:
        DrDiscard class if type matches, None otherwise
    """
    if params is None:
        params = {}
    if compare_attr("type", params, "^discard$"):
        return DrDiscard
    return None


class DrDiscard(coshsh.datarecipient.Datarecipient):
    """Datarecipient that discards all output.

    Used for testing configuration generation without writing output files.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize discard datarecipient.

        Args:
            **kwargs: Configuration parameters including 'name'
        """
        self.name = kwargs["name"]

    def read(self, filter: Optional[Any] = None, objects: Optional[Dict[str, Any]] = None,
             force: bool = False, **kwargs: Any) -> None:
        """Load objects (no-op for discard recipient).

        Args:
            filter: Optional filter (unused)
            objects: Dictionary of objects
            force: Force read flag (unused)
            **kwargs: Additional arguments (unused)
        """
        if objects is None:
            objects = {}
        self.objects = objects

    def output(self) -> None:
        """Output data (no-op - prevents default recipient from running)."""
        pass
