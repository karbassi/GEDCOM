"""Encoders for reusable substructure blocks (§3.2.3)."""

from __future__ import annotations

from collections.abc import Iterator

from ..enums import NameType, enum_value
from ..lines import Line
from ..model import Attribute, Event, EventDetail, NamePieces, NonEvent, PersonalName
from ..types import date_value_gedcom


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


def personal_name_lines(name: PersonalName, level: int) -> Iterator[Line]:
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


def contact_lines(
    level: int,
    phones: list[str],
    emails: list[str],
    faxes: list[str],
    web_pages: list[str],
) -> Iterator[Line]:
    for phone in phones:
        yield Line(level, "PHON", phone)
    for email in emails:
        yield Line(level, "EMAIL", email)
    for fax in faxes:
        yield Line(level, "FAX", fax)
    for www in web_pages:
        yield Line(level, "WWW", www)


def event_detail_lines(detail: EventDetail, level: int) -> Iterator[Line]:
    if detail.date is not None:
        yield Line(level, "DATE", date_value_gedcom(detail.date))
        if detail.date_time is not None:
            yield Line(level + 1, "TIME", detail.date_time.gedcom())
        if detail.date_phrase is not None:
            yield Line(level + 1, "PHRASE", detail.date_phrase)
    if detail.agency is not None:
        yield Line(level, "AGNC", detail.agency)
    if detail.religion is not None:
        yield Line(level, "RELI", detail.religion)
    if detail.cause is not None:
        yield Line(level, "CAUS", detail.cause)


def event_lines(event: Event, level: int) -> Iterator[Line]:
    payload = event.text if event.tag == "EVEN" else ("Y" if event.occurred else None)
    yield Line(level, event.tag, payload)
    if event.type is not None:
        yield Line(level + 1, "TYPE", event.type)
    if event.detail is not None:
        yield from event_detail_lines(event.detail, level + 1)


def attribute_lines(attribute: Attribute, level: int) -> Iterator[Line]:
    yield Line(level, attribute.tag, attribute.value)
    if attribute.type is not None:
        yield Line(level + 1, "TYPE", attribute.type)
    if attribute.detail is not None:
        yield from event_detail_lines(attribute.detail, level + 1)


def non_event_lines(non_event: NonEvent, level: int) -> Iterator[Line]:
    yield Line(level, "NO", non_event.event)
    if non_event.date is not None:
        yield Line(level + 1, "DATE", non_event.date.gedcom())
        if non_event.date_phrase is not None:
            yield Line(level + 2, "PHRASE", non_event.date_phrase)
