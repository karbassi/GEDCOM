"""Structure nodes → reusable substructure blocks (inverse of
:mod:`gedcom.serialize._substructures`).
"""

from __future__ import annotations

from ..enums import AdoptingParent, Medium, NameType, OrdinanceStatus
from ..extensions import registered_extension_uris
from ..model import (
    Address,
    Attribute,
    Crop,
    Event,
    EventDetail,
    ExtensionStructure,
    Family,
    File,
    FileTranslation,
    Identifier,
    LdsOrdinanceDetail,
    Map,
    NamePieces,
    NameTranslation,
    NonEvent,
    Note,
    NoteTranslation,
    PersonalName,
    Place,
    PlaceTranslation,
)
from ._resolve import Resolver
from ._tree import Node
from ._values import (
    parse_age,
    parse_date_exact,
    parse_date_period,
    parse_date_value,
    parse_enum,
    parse_integer,
    parse_latitude,
    parse_longitude,
    parse_text_list,
    parse_time,
)
from .errors import ParseError

# The fixed §3 event/attribute tag taxonomy: needed to tell an event line from
# an attribute line, which the wire form alone does not distinguish.
EVENT_TAGS = frozenset(
    {
        "BIRT", "CHR", "DEAT", "BURI", "CREM", "ADOP", "BAPM", "BARM", "BASM",
        "CHRA", "CONF", "FCOM", "NATU", "EMIG", "IMMI", "CENS", "PROB", "WILL",
        "GRAD", "RETI", "ORDN", "EVEN",
        "ANUL", "DIV", "DIVF", "ENGA", "MARB", "MARC", "MARR", "MARL", "MARS",
    }
)  # fmt: skip
ATTRIBUTE_TAGS = frozenset(
    {
        "CAST", "DSCR", "EDUC", "IDNO", "NATI", "NCHI", "NMR",
        "OCCU", "PROP", "RELI", "RESI", "SSN", "TITL", "FACT",
    }
)  # fmt: skip


def _require(value: str | None, tag: str, line: int | None) -> str:
    if value is None:
        raise ParseError(f"{tag} requires a value", line=line, tag=tag)
    return value


def _name_pieces(node: Node) -> NamePieces | None:
    fields = {
        "prefix": [c.value or "" for c in node.all("NPFX")],
        "given": [c.value or "" for c in node.all("GIVN")],
        "nickname": [c.value or "" for c in node.all("NICK")],
        "surname_prefix": [c.value or "" for c in node.all("SPFX")],
        "surname": [c.value or "" for c in node.all("SURN")],
        "suffix": [c.value or "" for c in node.all("NSFX")],
    }
    if not any(fields.values()):
        return None
    return NamePieces(**fields)


def parse_personal_name(node: Node) -> PersonalName:
    name = PersonalName(value=node.value or "")
    type_node = node.child("TYPE")
    if type_node is not None and type_node.value is not None:
        name.type = parse_enum(type_node.value, NameType)
        name.type_phrase = type_node.text("PHRASE")
    name.pieces = _name_pieces(node)
    for tran in node.all("TRAN"):
        name.translations.append(
            NameTranslation(
                value=tran.value or "",
                language=_require(tran.text("LANG"), "LANG", tran.line.level),
                pieces=_name_pieces(tran),
            )
        )
    return name


def parse_place(node: Node) -> Place:
    place = Place(names=parse_text_list(node.value or ""))
    form = node.text("FORM")
    if form is not None:
        place.form = parse_text_list(form)
    place.language = node.text("LANG")
    for tran in node.all("TRAN"):
        place.translations.append(
            PlaceTranslation(
                names=parse_text_list(tran.value or ""),
                language=_require(tran.text("LANG"), "LANG", tran.line.level),
            )
        )
    map_node = node.child("MAP")
    if map_node is not None:
        lati = _require(map_node.text("LATI"), "LATI", map_node.line.level)
        long = _require(map_node.text("LONG"), "LONG", map_node.line.level)
        place.map = Map(latitude=parse_latitude(lati), longitude=parse_longitude(long))
    return place


def parse_address(node: Node) -> Address:
    return Address(
        value=node.value or "",
        city=node.text("CITY"),
        state=node.text("STAE"),
        postal_code=node.text("POST"),
        country=node.text("CTRY"),
    )


def parse_file(node: Node) -> File:
    form_node = node.child("FORM")
    file = File(
        path=node.value or "",
        form=_require(form_node.value if form_node else None, "FORM", node.line.level),
        title=node.text("TITL"),
    )
    if form_node is not None and form_node.text("MEDI") is not None:
        medium = form_node.text("MEDI")
        assert medium is not None
        file.medium = parse_enum(medium, Medium)
    for tran in node.all("TRAN"):
        file.translations.append(
            FileTranslation(
                path=tran.value or "",
                form=_require(tran.text("FORM"), "FORM", tran.line.level),
            )
        )
    return file


def parse_crop(node: Node) -> Crop:
    def integer_child(tag: str) -> int | None:
        value = node.text(tag)
        return parse_integer(value) if value is not None else None

    return Crop(
        top=integer_child("TOP"),
        left=integer_child("LEFT"),
        height=integer_child("HEIGHT"),
        width=integer_child("WIDTH"),
    )


def parse_note(node: Node) -> Note:
    note = Note(text=node.value or "", mime=node.text("MIME"), language=node.text("LANG"))
    for tran in node.all("TRAN"):
        note.translations.append(parse_note_translation(tran))
    return note


def parse_note_translation(node: Node) -> NoteTranslation:
    return NoteTranslation(
        text=node.value or "", mime=node.text("MIME"), language=node.text("LANG")
    )


def parse_identifier(node: Node) -> Identifier:
    return Identifier(kind=node.tag, value=node.value or "", type=node.text("TYPE"))


def parse_extension_structure(node: Node, resolver: Resolver) -> ExtensionStructure:
    """Reconstruct an extension structure, resolving its declared URI.

    A registered tag uses its registry URI (``uri=None``); an arbitrary tag
    takes the URI declared for it in ``HEAD.SCHMA``. An undeclared, unregistered
    extension tag is a strict error (ADR-0005).
    """
    children = tuple(parse_extension_structure(c, resolver) for c in node.children)
    tag = node.tag
    if tag in registered_extension_uris():
        uri: str | None = None
    elif tag in resolver.schema:
        uri = resolver.schema[tag]
    else:
        raise ParseError(
            f"extension tag {tag!r} is not declared in HEAD.SCHMA", tag=tag, line=node.line.level
        )
    return ExtensionStructure(tag=tag, value=node.value, children=children, uri=uri)


def parse_non_event(node: Node) -> NonEvent:
    non_event = NonEvent(event=node.value or "")
    date_node = node.child("DATE")
    if date_node is not None:
        non_event.date = parse_date_period(date_node.value or "", line=date_node.line.level)
        non_event.date_phrase = date_node.text("PHRASE")
    return non_event


def parse_event_detail(node: Node, resolver: Resolver) -> EventDetail | None:
    detail = EventDetail()
    found = False

    date_node = node.child("DATE")
    if date_node is not None and date_node.value is not None:
        found = True
        detail.date = parse_date_value(date_node.value, line=date_node.line.level)
        time = date_node.text("TIME")
        if time is not None:
            detail.date_time = parse_time(time, line=date_node.line.level)
        detail.date_phrase = date_node.text("PHRASE")

    sdate_node = node.child("SDATE")
    if sdate_node is not None and sdate_node.value is not None:
        found = True
        detail.sort_date = parse_date_value(sdate_node.value, line=sdate_node.line.level)
        time = sdate_node.text("TIME")
        if time is not None:
            detail.sort_date_time = parse_time(time, line=sdate_node.line.level)
        detail.sort_date_phrase = sdate_node.text("PHRASE")

    age_node = node.child("AGE")
    if age_node is not None and age_node.value is not None:
        found = True
        detail.age = parse_age(age_node.value, line=age_node.line.level)
        detail.age_phrase = age_node.text("PHRASE")

    for tag, age_attr, phrase_attr in (
        ("HUSB", "husband_age", "husband_age_phrase"),
        ("WIFE", "wife_age", "wife_age_phrase"),
    ):
        spouse_node = node.child(tag)
        if spouse_node is not None:
            inner = spouse_node.child("AGE")
            if inner is not None and inner.value is not None:
                found = True
                setattr(detail, age_attr, parse_age(inner.value, line=inner.line.level))
                setattr(detail, phrase_attr, inner.text("PHRASE"))

    place_node = node.child("PLAC")
    if place_node is not None:
        found = True
        detail.place = parse_place(place_node)
    addr_node = node.child("ADDR")
    if addr_node is not None:
        found = True
        detail.address = parse_address(addr_node)

    for tag, attr in (
        ("PHON", "phones"),
        ("EMAIL", "emails"),
        ("FAX", "faxes"),
        ("WWW", "web_pages"),
    ):
        values = [c.value or "" for c in node.all(tag)]
        if values:
            found = True
            setattr(detail, attr, values)

    for tag, attr in (("AGNC", "agency"), ("RELI", "religion"), ("CAUS", "cause")):
        value = node.text(tag)
        if value is not None:
            found = True
            setattr(detail, attr, value)

    famc_node = node.child("FAMC")
    if famc_node is not None and famc_node.value is not None:
        found = True
        detail.family_child = resolver.record(famc_node.value, Family)
        adop = famc_node.child("ADOP")
        if adop is not None and adop.value is not None:
            detail.adopting_parent = parse_enum(adop.value, AdoptingParent)
            detail.adopting_parent_phrase = adop.text("PHRASE")

    return detail if found else None


def parse_event(node: Node, resolver: Resolver) -> Event:
    event = Event(tag=node.tag)
    if node.tag == "EVEN":
        event.text = node.value
    else:
        event.occurred = node.value == "Y"
    event.type = node.text("TYPE")
    event.detail = parse_event_detail(node, resolver)
    return event


def parse_attribute(node: Node, resolver: Resolver) -> Attribute:
    attribute = Attribute(tag=node.tag, value=node.value or "")
    attribute.type = node.text("TYPE")
    attribute.detail = parse_event_detail(node, resolver)
    return attribute


def parse_ordinance_detail(node: Node) -> LdsOrdinanceDetail | None:
    detail = LdsOrdinanceDetail()
    found = False

    date_node = node.child("DATE")
    if date_node is not None and date_node.value is not None:
        found = True
        detail.date = parse_date_value(date_node.value, line=date_node.line.level)
        time = date_node.text("TIME")
        if time is not None:
            detail.date_time = parse_time(time, line=date_node.line.level)
        detail.date_phrase = date_node.text("PHRASE")

    temple = node.text("TEMP")
    if temple is not None:
        found = True
        detail.temple = temple

    place_node = node.child("PLAC")
    if place_node is not None:
        found = True
        detail.place = parse_place(place_node)

    stat_node = node.child("STAT")
    if stat_node is not None and stat_node.value is not None:
        found = True
        detail.status = parse_enum(stat_node.value, OrdinanceStatus)
        stat_date = stat_node.child("DATE")
        if stat_date is not None and stat_date.value is not None:
            detail.status_date = parse_date_exact(stat_date.value, line=stat_date.line.level)
            time = stat_date.text("TIME")
            if time is not None:
                detail.status_time = parse_time(time, line=stat_date.line.level)

    return detail if found else None
