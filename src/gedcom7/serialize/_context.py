"""Shared serialization context passed to every encoder."""

from __future__ import annotations

from dataclasses import dataclass

from ..xref import XrefTable
from ._links import FamilyIndex


@dataclass(frozen=True)
class Context:
    """Cross-cutting state an encoder needs: the xref table and family links."""

    table: XrefTable
    families: FamilyIndex
