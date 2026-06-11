"""Model → ordered sequence of :class:`~gedcom7.lines.Line`.

The per-record and per-substructure encoders live here. As records are
added in later slices, this module grows the encoders that turn each into
its line sequence in the spec-mandated order.
"""

from __future__ import annotations

from collections.abc import Iterator

from .lines import Line
from .model import Document, Header, Record, Submitter
from .xref import XrefTable


def _header_lines(header: Header, table: XrefTable) -> Iterator[Line]:
    yield Line(0, "HEAD")
    yield Line(1, "GEDC")
    yield Line(2, "VERS", header.gedcom_version)
    if header.date is not None:
        yield Line(1, "DATE", header.date.gedcom())
        if header.time is not None:
            yield Line(2, "TIME", header.time.gedcom())
    if header.submitter is not None:
        yield Line(1, "SUBM", table.of(header.submitter), is_pointer=True)
    if header.copyright is not None:
        yield Line(1, "COPR", header.copyright)


def _contact_lines(record: Submitter) -> Iterator[Line]:
    for phone in record.phones:
        yield Line(1, "PHON", phone)
    for email in record.emails:
        yield Line(1, "EMAIL", email)
    for fax in record.faxes:
        yield Line(1, "FAX", fax)
    for www in record.web_pages:
        yield Line(1, "WWW", www)


def _submitter_lines(record: Submitter, table: XrefTable) -> Iterator[Line]:
    yield Line(0, "SUBM", xref=table.of(record))
    yield Line(1, "NAME", record.name)
    yield from _contact_lines(record)


def _record_lines(record: Record, table: XrefTable) -> Iterator[Line]:
    if isinstance(record, Submitter):
        yield from _submitter_lines(record, table)
    else:
        raise TypeError(f"no serializer for record type {type(record).__name__}")


def serialize_document(document: Document, table: XrefTable) -> Iterator[Line]:
    """Yield the logical lines for a whole document, in document order."""
    yield from _header_lines(document.header, table)
    for record in document.records:
        yield from _record_lines(record, table)
    yield Line(0, "TRLR")
