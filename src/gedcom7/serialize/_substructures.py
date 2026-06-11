"""Encoders for reusable substructure blocks (§3.2.3)."""

from __future__ import annotations

from collections.abc import Iterator

from ..enums import NameType, enum_value
from ..lines import Line
from ..model import NamePieces, PersonalName


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
