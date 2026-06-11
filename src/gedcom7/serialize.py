"""Model → ordered sequence of :class:`~gedcom7.lines.Line`.

The per-record and per-substructure encoders live here. As records are
added in later slices, this module grows the encoders that turn each into
its line sequence in the spec-mandated order.
"""

from __future__ import annotations

from collections.abc import Iterator

from .lines import Line
from .model import Document


def serialize_document(document: Document) -> Iterator[Line]:
    """Yield the logical lines for a whole document, in document order."""
    yield Line(0, "HEAD")
    yield Line(1, "GEDC")
    yield Line(2, "VERS", document.header.gedcom_version)
    # Records are emitted here as record types are added (slices 05+).
    yield Line(0, "TRLR")
