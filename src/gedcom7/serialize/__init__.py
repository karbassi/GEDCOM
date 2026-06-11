"""Model → ordered :class:`~gedcom7.lines.Line` sequence.

``serialize_document`` walks the document in wire order. Record dispatch is
explicit (no magic registry): each record type maps to its encoder in
``_records``; substructure encoders live in ``_substructures``.
"""

from __future__ import annotations

from collections.abc import Iterator

from ..lines import Line
from ..model import Document, Individual, Record, Submitter
from ..xref import XrefTable
from ._header import header_lines
from ._records import individual_lines, submitter_lines


def _record_lines(record: Record, table: XrefTable) -> Iterator[Line]:
    if isinstance(record, Submitter):
        yield from submitter_lines(record, table)
    elif isinstance(record, Individual):
        yield from individual_lines(record, table)
    else:
        raise TypeError(f"no serializer for record type {type(record).__name__}")


def serialize_document(document: Document, table: XrefTable) -> Iterator[Line]:
    """Yield the logical lines for a whole document, in document order."""
    yield from header_lines(document.header, table)
    for record in document.records:
        yield from _record_lines(record, table)
    yield Line(0, "TRLR")


__all__ = ["serialize_document"]
