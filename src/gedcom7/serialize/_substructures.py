"""Encoders for reusable substructure blocks (§3.2.3)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from ..enums import AdoptingParent, Medium, NameType, OrdinanceStatus, enum_value
from ..lines import Line
from ..model import (
    Address,
    Attribute,
    Crop,
    Event,
    EventDetail,
    ExtensionStructure,
    File,
    Identifier,
    LdsOrdinanceDetail,
    NamePieces,
    NonEvent,
    Note,
    NoteTranslation,
    PersonalName,
    Place,
)
from ..types import date_value_gedcom, integer, text_list

if TYPE_CHECKING:
    from ._context import Context


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


def place_lines(place: Place, level: int) -> Iterator[Line]:
    yield Line(level, "PLAC", text_list(place.names))
    if place.form is not None:
        yield Line(level + 1, "FORM", text_list(place.form))
    if place.language is not None:
        yield Line(level + 1, "LANG", place.language)
    for tran in place.translations:
        yield Line(level + 1, "TRAN", text_list(tran.names))
        yield Line(level + 2, "LANG", tran.language)
    if place.map is not None:
        yield Line(level + 1, "MAP")
        yield Line(level + 2, "LATI", place.map.latitude.gedcom())
        yield Line(level + 2, "LONG", place.map.longitude.gedcom())


def address_lines(address: Address, level: int) -> Iterator[Line]:
    yield Line(level, "ADDR", address.value)
    if address.city is not None:
        yield Line(level + 1, "CITY", address.city)
    if address.state is not None:
        yield Line(level + 1, "STAE", address.state)
    if address.postal_code is not None:
        yield Line(level + 1, "POST", address.postal_code)
    if address.country is not None:
        yield Line(level + 1, "CTRY", address.country)


def file_lines(file: File, level: int) -> Iterator[Line]:
    yield Line(level, "FILE", file.path)
    yield Line(level + 1, "FORM", file.form)
    if file.medium is not None:
        yield Line(level + 2, "MEDI", enum_value(file.medium, Medium))
    if file.title is not None:
        yield Line(level + 1, "TITL", file.title)
    for tran in file.translations:
        yield Line(level + 1, "TRAN", tran.path)
        yield Line(level + 2, "FORM", tran.form)


def crop_lines(crop: Crop, level: int) -> Iterator[Line]:
    yield Line(level, "CROP")
    for tag, value in (
        ("TOP", crop.top),
        ("LEFT", crop.left),
        ("HEIGHT", crop.height),
        ("WIDTH", crop.width),
    ):
        if value is not None:
            yield Line(level + 1, tag, integer(value))


def note_translation_lines(tran: NoteTranslation, level: int) -> Iterator[Line]:
    yield Line(level, "TRAN", tran.text)
    if tran.mime is not None:
        yield Line(level + 1, "MIME", tran.mime)
    if tran.language is not None:
        yield Line(level + 1, "LANG", tran.language)


def note_lines(note: Note, level: int) -> Iterator[Line]:
    yield Line(level, "NOTE", note.text)
    if note.mime is not None:
        yield Line(level + 1, "MIME", note.mime)
    if note.language is not None:
        yield Line(level + 1, "LANG", note.language)
    for tran in note.translations:
        yield from note_translation_lines(tran, level + 1)


def extension_structure_lines(ext: ExtensionStructure, level: int) -> Iterator[Line]:
    yield Line(level, ext.tag, ext.value)
    for child in ext.children:
        yield from extension_structure_lines(child, level + 1)


def identifier_lines(identifier: Identifier, level: int) -> Iterator[Line]:
    yield Line(level, identifier.kind, identifier.value)
    if identifier.type is not None and identifier.kind in ("REFN", "EXID"):
        yield Line(level + 1, "TYPE", str(identifier.type))


def event_detail_lines(detail: EventDetail, level: int, ctx: Context) -> Iterator[Line]:
    if detail.date is not None:
        yield Line(level, "DATE", date_value_gedcom(detail.date))
        if detail.date_time is not None:
            yield Line(level + 1, "TIME", detail.date_time.gedcom())
        if detail.date_phrase is not None:
            yield Line(level + 1, "PHRASE", detail.date_phrase)
    if detail.place is not None:
        yield from place_lines(detail.place, level)
    if detail.address is not None:
        yield from address_lines(detail.address, level)
    yield from contact_lines(level, detail.phones, detail.emails, detail.faxes, detail.web_pages)
    if detail.agency is not None:
        yield Line(level, "AGNC", detail.agency)
    if detail.religion is not None:
        yield Line(level, "RELI", detail.religion)
    if detail.cause is not None:
        yield Line(level, "CAUS", detail.cause)
    if detail.family_child is not None:  # event-level FAMC (BIRT/CHR/ADOP)
        yield Line(level, "FAMC", ctx.table.of(detail.family_child), is_pointer=True)
        if detail.adopting_parent is not None:
            yield Line(level + 1, "ADOP", enum_value(detail.adopting_parent, AdoptingParent))
            if detail.adopting_parent_phrase is not None:
                yield Line(level + 2, "PHRASE", detail.adopting_parent_phrase)


def event_lines(event: Event, level: int, ctx: Context) -> Iterator[Line]:
    payload = event.text if event.tag == "EVEN" else ("Y" if event.occurred else None)
    yield Line(level, event.tag, payload)
    if event.type is not None:
        yield Line(level + 1, "TYPE", event.type)
    if event.detail is not None:
        yield from event_detail_lines(event.detail, level + 1, ctx)


def attribute_lines(attribute: Attribute, level: int, ctx: Context) -> Iterator[Line]:
    yield Line(level, attribute.tag, attribute.value)
    if attribute.type is not None:
        yield Line(level + 1, "TYPE", attribute.type)
    if attribute.detail is not None:
        yield from event_detail_lines(attribute.detail, level + 1, ctx)


def non_event_lines(non_event: NonEvent, level: int) -> Iterator[Line]:
    yield Line(level, "NO", non_event.event)
    if non_event.date is not None:
        yield Line(level + 1, "DATE", non_event.date.gedcom())
        if non_event.date_phrase is not None:
            yield Line(level + 2, "PHRASE", non_event.date_phrase)


def ordinance_detail_lines(detail: LdsOrdinanceDetail, level: int) -> Iterator[Line]:
    if detail.date is not None:
        yield Line(level, "DATE", date_value_gedcom(detail.date))
        if detail.date_time is not None:
            yield Line(level + 1, "TIME", detail.date_time.gedcom())
        if detail.date_phrase is not None:
            yield Line(level + 1, "PHRASE", detail.date_phrase)
    if detail.temple is not None:
        yield Line(level, "TEMP", detail.temple)
    if detail.place is not None:
        yield from place_lines(detail.place, level)
    if detail.status is not None:
        yield Line(level, "STAT", enum_value(detail.status, OrdinanceStatus))
        # STAT requires DATE (enforced at construction).
        assert detail.status_date is not None
        yield Line(level + 1, "DATE", detail.status_date.gedcom())
        if detail.status_time is not None:
            yield Line(level + 2, "TIME", detail.status_time.gedcom())
