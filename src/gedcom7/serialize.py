"""Model → ordered sequence of :class:`~gedcom7.lines.Line`.

The per-record and per-substructure encoders live here. As records are
added in later slices, this module grows the encoders that turn each into
its line sequence in the spec-mandated order.
"""

from __future__ import annotations

from collections.abc import Iterator

from .enums import NameType, Sex, enum_value
from .lines import Line
from .model import (
    Document,
    Header,
    Individual,
    NamePieces,
    PersonalName,
    Record,
    Submitter,
)
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


def _name_pieces_lines(pieces: NamePieces, level: int) -> Iterator[Line]:
    for tag, values in (
        ("NPFX", pieces.prefix),
        ("GIVN", pieces.given),
        ("NICK", pieces.nickname),
        ("SPFX", pieces.surname_prefix),
        ("SURN", pieces.surname),
        ("NSFX", pieces.suffix),
    ):
        for value in values:
            yield Line(level, tag, value)


def _personal_name_lines(name: PersonalName, level: int) -> Iterator[Line]:
    yield Line(level, "NAME", name.value)
    if name.type is not None:
        yield Line(level + 1, "TYPE", enum_value(name.type, NameType))
        if name.type_phrase is not None:
            yield Line(level + 2, "PHRASE", name.type_phrase)
    if name.pieces is not None:
        yield from _name_pieces_lines(name.pieces, level + 1)
    for tran in name.translations:
        yield Line(level + 1, "TRAN", tran.value)
        yield Line(level + 2, "LANG", tran.language)
        if tran.pieces is not None:
            yield from _name_pieces_lines(tran.pieces, level + 2)


def _individual_lines(record: Individual, table: XrefTable) -> Iterator[Line]:
    yield Line(0, "INDI", xref=table.of(record))
    for name in record.names:
        yield from _personal_name_lines(name, 1)
    if record.sex is not None:
        yield Line(1, "SEX", enum_value(record.sex, Sex))


def _record_lines(record: Record, table: XrefTable) -> Iterator[Line]:
    if isinstance(record, Submitter):
        yield from _submitter_lines(record, table)
    elif isinstance(record, Individual):
        yield from _individual_lines(record, table)
    else:
        raise TypeError(f"no serializer for record type {type(record).__name__}")


def serialize_document(document: Document, table: XrefTable) -> Iterator[Line]:
    """Yield the logical lines for a whole document, in document order."""
    yield from _header_lines(document.header, table)
    for record in document.records:
        yield from _record_lines(record, table)
    yield Line(0, "TRLR")
