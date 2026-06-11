"""Translate a parsed authoring document into a :class:`~gedcom7.Document`.

``build_document`` is a pure function from a mapping (as produced by the
format reader) to a fully-linked ``Document`` ready for the writer. It owns
the authoring dialect — the friendly key names, the handle-reference system,
and the mapping of words to the model's enums and value types.

Records are linked by **handle** (each record's ``xref``). Construction is two
passes: every record is created and registered first, then populated, so a
family may reference a child defined later in the file. Bad references, dates,
and enum values raise a located :class:`LoadError`.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from typing import Any, TypeVar

from ..enums import (
    ExidType,
    FamcStatus,
    Medium,
    NameType,
    OrdinanceStatus,
    Pedigree,
    Quality,
    Restriction,
    Role,
    Sex,
)
from ..model import (
    VOID,
    Address,
    Alias,
    Association,
    Attribute,
    CallNumber,
    ChangeDate,
    ChildLink,
    CreationDate,
    Crop,
    Document,
    Event,
    EventDetail,
    Family,
    File,
    FileTranslation,
    Header,
    HeaderSource,
    Identifier,
    Individual,
    LdsIndividualOrdinance,
    LdsOrdinanceDetail,
    LdsSpouseSealing,
    Map,
    Multimedia,
    MultimediaLink,
    NamePieces,
    NameTranslation,
    NonEvent,
    Note,
    NoteTranslation,
    PersonalName,
    Place,
    PlaceTranslation,
    RecordBase,
    Repository,
    SharedNote,
    Source,
    SourceCitation,
    SourceData,
    SourceDataEvent,
    SourceRepositoryCitation,
    Submitter,
)
from ..model._pointers import VoidPointer
from ..types import Age, DatePeriod, Latitude, Longitude, Time
from .dates import parse_date, parse_date_exact
from .errors import LoadError, at

E = TypeVar("E", bound=StrEnum)
R = TypeVar("R", bound=RecordBase)

# Authoring section key -> (model type, xref prefix). Order is output order.
_SECTIONS: tuple[tuple[str, type[RecordBase], str], ...] = (
    ("submitters", Submitter, "U"),
    ("individuals", Individual, "I"),
    ("families", Family, "F"),
    ("sources", Source, "S"),
    ("repositories", Repository, "R"),
    ("multimedia", Multimedia, "O"),
    ("shared_notes", SharedNote, "N"),
)


def build_document(mapping: dict[str, Any]) -> Document:
    """Build a linked :class:`Document` from a parsed authoring mapping."""
    return _Builder(mapping).build()


# --- mapping helpers --------------------------------------------------------


def _mapping(node: object, what: str) -> dict[str, Any]:
    if not isinstance(node, dict):
        raise LoadError(f"expected a mapping for {what}, got {type(node).__name__}")
    return node


def _get(node: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in node and node[key] is not None:
            return node[key]
    return None


def _items(node: dict[str, Any], *keys: str) -> list[Any]:
    value = _get(node, *keys)
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _text(value: object, what: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise LoadError(f"{what} must be text, got {type(value).__name__}")
    return str(value)


def _opt_text(node: dict[str, Any], *keys: str) -> str | None:
    value = _get(node, *keys)
    return None if value is None else _text(value, keys[0])


def _text_list(value: object, what: str) -> list[str]:
    if isinstance(value, list):
        return [_text(item, what) for item in value]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",")]
    return [_text(value, what)]


def _int(value: object, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        if isinstance(value, str) and value.lstrip("-").isdigit():
            return int(value)
        raise LoadError(f"{what} must be an integer")
    return value


def _float(value: object, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        try:
            return float(_text(value, what))
        except ValueError:
            raise LoadError(f"{what} must be a number") from None
    return float(value)


class _Builder:
    """Holds the handle registry and the ordered records during a build."""

    def __init__(self, mapping: dict[str, Any]) -> None:
        self._mapping = _mapping(mapping, "document")
        self._by_handle: dict[str, RecordBase] = {}
        self._records: list[RecordBase] = []
        # (record, raw node, location path) pending population in pass two.
        self._pending: list[tuple[RecordBase, dict[str, Any], str]] = []

    def build(self) -> Document:
        for key, record_type, prefix in _SECTIONS:
            with at(f".{key}"):
                self._register_section(key, record_type, prefix)
        for record, node, location in self._pending:
            with at(location):
                self._populate(record, node)
        header = self._build_header()
        return Document(header=header, records=self._records)

    # -- pass one: create + register ----------------------------------------

    def _register_section(self, key: str, record_type: type[RecordBase], prefix: str) -> None:
        for index, raw in enumerate(_items(self._mapping, key)):
            with at(f"[{index}]"):
                node = _mapping(raw, key)
                record = self._create(record_type, node)
                handle = _opt_text(node, "xref", "id")
                if handle is not None:
                    record.xref_id = handle
                    if handle in self._by_handle:
                        raise LoadError(f"duplicate handle {handle!r}")
                    self._by_handle[handle] = record
                self._records.append(record)
                self._pending.append((record, node, f".{key}[{index}]"))

    def _create(self, record_type: type[RecordBase], node: dict[str, Any]) -> RecordBase:
        # Records with required positional fields are read in pass one; the
        # rest are empty shells populated once all handles are known.
        if record_type is Submitter:
            return Submitter(name=_req_text(node, "submitter", "name"))
        if record_type is Repository:
            return Repository(name=_req_text(node, "repository", "name"))
        if record_type is SharedNote:
            return SharedNote(text=_req_text(node, "shared note", "text", "value"))
        return record_type()

    # -- references ---------------------------------------------------------

    def _resolve(self, value: object, expected: type[R], what: str) -> R:
        handle = _text(value, f"{what} reference").strip().strip("@")
        record = self._by_handle.get(handle)
        if record is None:
            raise LoadError(f"{what} reference {handle!r} matches no record")
        if not isinstance(record, expected):
            raise LoadError(
                f"{what} reference {handle!r} points to a {type(record).__name__}, "
                f"expected {expected.__name__}"
            )
        return record

    def _resolve_or_void(self, value: object, expected: type[R], what: str) -> R | VoidPointer:
        if value is None:
            return VOID
        handle = _text(value, what).strip().strip("@")
        if handle == "" or handle.upper() == "VOID":
            return VOID
        return self._resolve(handle, expected, what)

    # -- enums --------------------------------------------------------------

    def _enum(self, value: object, enum_cls: type[E], what: str) -> E | str | None:
        if value is None:
            return None
        text = _text(value, what)
        if text.startswith("_"):
            return text
        candidate = text.upper().replace("-", "_").replace(" ", "_")
        if candidate in enum_cls.__members__:
            return enum_cls[candidate]
        for member in enum_cls:
            if member.value.upper() == text.upper():
                return member
        allowed = ", ".join(member.name.lower() for member in enum_cls)
        raise LoadError(f"{text!r} is not a valid {what}; allowed: {allowed}")

    def _enum_required(self, value: object, enum_cls: type[E], what: str) -> E | str:
        result = self._enum(value, enum_cls, what)
        if result is None:
            raise LoadError(f"missing required {what}")
        return result

    def _exid_type(self, value: object) -> ExidType | str | None:
        if value is None:
            return None
        text = _text(value, "EXID type")
        if "://" in text:
            return text
        candidate = text.upper().replace("-", "_")
        if candidate in ExidType.__members__:
            return ExidType[candidate]
        allowed = ", ".join(member.name.lower() for member in ExidType)
        raise LoadError(f"{text!r} is not a registered EXID type (or a URI); allowed: {allowed}")

    def _each(self, node: dict[str, Any], fn: Callable[[Any], Any], *keys: str) -> list[Any]:
        out: list[Any] = []
        primary = keys[0]
        for index, item in enumerate(_items(node, *keys)):
            with at(f".{primary}[{index}]"):
                out.append(fn(item))
        return out

    # -- pass two: populate per record type ---------------------------------

    def _populate(self, record: RecordBase, node: dict[str, Any]) -> None:
        if isinstance(record, Individual):
            self._fill_individual(record, node)
        elif isinstance(record, Family):
            self._fill_family(record, node)
        elif isinstance(record, Source):
            self._fill_source(record, node)
        elif isinstance(record, Repository):
            self._fill_repository(record, node)
        elif isinstance(record, Multimedia):
            self._fill_multimedia(record, node)
        elif isinstance(record, SharedNote):
            self._fill_shared_note(record, node)
        elif isinstance(record, Submitter):
            self._fill_submitter(record, node)
        self._fill_metadata(record, node)

    def _fill_metadata(self, record: RecordBase, node: dict[str, Any]) -> None:
        change = _get(node, "change_date", "changed")
        if change is not None:
            with at(".change_date"):
                record.change_date = self._change_date(change)
        creation = _get(node, "creation_date", "created")
        if creation is not None:
            with at(".creation_date"):
                record.creation_date = self._creation_date(creation)

    def _fill_individual(self, indi: Individual, node: dict[str, Any]) -> None:
        names: list[PersonalName] = []
        single = _get(node, "name")
        if single is not None:
            with at(".name"):
                names.append(self._name(single))
        names.extend(self._each(node, self._name, "names"))
        indi.names = names
        with at(".sex"):
            indi.sex = self._enum(_get(node, "sex"), Sex, "sex")
        indi.restrictions = self._enum_list(node, Restriction, "restrictions", "restriction")
        indi.attributes = self._each(node, self._attribute, "attributes")
        indi.events = self._each(node, self._event, "events")
        indi.non_events = self._each(node, self._non_event, "non_events")
        indi.lds_ordinances = self._each(node, self._lds_individual, "lds_ordinances", "ordinances")
        indi.associations = self._each(node, self._association, "associations")
        indi.aliases = self._each(node, self._alias, "aliases")
        indi.submitters = self._refs(node, Submitter, "submitters")
        indi.ancestor_interest = self._refs(node, Submitter, "ancestor_interest")
        indi.descendant_interest = self._refs(node, Submitter, "descendant_interest")
        indi.notes = self._notes(node)
        indi.source_citations = self._citations(node)
        indi.media_links = self._media(node)
        indi.identifiers = self._each(node, self._identifier, "identifiers")

    def _fill_family(self, family: Family, node: dict[str, Any]) -> None:
        husband = _get(node, "husband", "father")
        if husband is not None:
            with at(".husband"):
                family.husband = self._resolve(husband, Individual, "husband")
        wife = _get(node, "wife", "mother")
        if wife is not None:
            with at(".wife"):
                family.wife = self._resolve(wife, Individual, "wife")
        family.children = self._each(node, self._child, "children")
        family.restrictions = self._enum_list(node, Restriction, "restrictions", "restriction")
        family.attributes = self._each(node, self._attribute, "attributes")
        family.events = self._each(node, self._event, "events")
        family.non_events = self._each(node, self._non_event, "non_events")
        family.sealings = self._each(node, self._spouse_sealing, "sealings")
        family.associations = self._each(node, self._association, "associations")
        family.submitters = self._refs(node, Submitter, "submitters")
        family.notes = self._notes(node)
        family.source_citations = self._citations(node)
        family.media_links = self._media(node)
        family.identifiers = self._each(node, self._identifier, "identifiers")

    def _fill_source(self, source: Source, node: dict[str, Any]) -> None:
        source.author = _opt_text(node, "author")
        source.title = _opt_text(node, "title")
        source.abbreviation = _opt_text(node, "abbreviation", "abbr")
        source.publication = _opt_text(node, "publication", "publ")
        source.text = _opt_text(node, "text")
        source.text_mime = _opt_text(node, "text_mime")
        source.text_language = _opt_text(node, "text_language", "text_lang")
        data = _get(node, "data")
        if data is not None:
            with at(".data"):
                source.data = self._source_data(data)
        source.repository_citations = self._each(
            node, self._repo_citation, "repository_citations", "repositories"
        )
        source.notes = self._notes(node)
        source.media_links = self._media(node)
        source.identifiers = self._each(node, self._identifier, "identifiers")

    def _fill_repository(self, repo: Repository, node: dict[str, Any]) -> None:
        repo.address = self._opt_address(node)
        repo.phones = self._strings(node, "phones", "phone")
        repo.emails = self._strings(node, "emails", "email")
        repo.faxes = self._strings(node, "faxes", "fax")
        repo.web_pages = self._strings(node, "web_pages", "www")
        repo.notes = self._notes(node)
        repo.identifiers = self._each(node, self._identifier, "identifiers")

    def _fill_multimedia(self, obje: Multimedia, node: dict[str, Any]) -> None:
        obje.files = self._each(node, self._file, "files")
        obje.restrictions = self._enum_list(node, Restriction, "restrictions", "restriction")
        obje.notes = self._notes(node)
        obje.source_citations = self._citations(node)
        obje.identifiers = self._each(node, self._identifier, "identifiers")

    def _fill_shared_note(self, snote: SharedNote, node: dict[str, Any]) -> None:
        snote.mime = _opt_text(node, "mime")
        snote.language = _opt_text(node, "language", "lang")
        snote.translations = self._each(node, self._note_translation, "translations")
        snote.source_citations = self._citations(node)
        snote.identifiers = self._each(node, self._identifier, "identifiers")

    def _fill_submitter(self, subm: Submitter, node: dict[str, Any]) -> None:
        subm.address = self._opt_address(node)
        subm.phones = self._strings(node, "phones", "phone")
        subm.emails = self._strings(node, "emails", "email")
        subm.faxes = self._strings(node, "faxes", "fax")
        subm.web_pages = self._strings(node, "web_pages", "www")
        subm.media_links = self._media(node)
        subm.notes = self._notes(node)
        subm.identifiers = self._each(node, self._identifier, "identifiers")

    # -- substructure builders ----------------------------------------------

    def _name(self, value: object) -> PersonalName:
        if isinstance(value, str):
            return PersonalName(value)
        node = _mapping(value, "name")
        with at(".type"):
            name_type = self._enum(_get(node, "type"), NameType, "name type")
        return PersonalName(
            _req_text(node, "name", "value", "name"),
            type=name_type,
            type_phrase=_opt_text(node, "type_phrase"),
            pieces=self._pieces(_get(node, "pieces")),
            translations=self._each(node, self._name_translation, "translations"),
        )

    def _pieces(self, value: object) -> NamePieces | None:
        if value is None:
            return None
        node = _mapping(value, "name pieces")
        return NamePieces(
            prefix=self._strings(node, "prefix", "npfx"),
            given=self._strings(node, "given", "givn"),
            nickname=self._strings(node, "nickname", "nick"),
            surname_prefix=self._strings(node, "surname_prefix", "spfx"),
            surname=self._strings(node, "surname", "surn"),
            suffix=self._strings(node, "suffix", "nsfx"),
        )

    def _name_translation(self, value: object) -> NameTranslation:
        node = _mapping(value, "name translation")
        return NameTranslation(
            _req_text(node, "name translation", "value", "name"),
            _req_text(node, "name translation", "language", "lang"),
            pieces=self._pieces(_get(node, "pieces")),
        )

    def _event(self, value: object) -> Event:
        node = _mapping(value, "event")
        tag = _req_text(node, "event", "tag").upper()
        text = _opt_text(node, "text")
        with at(".type"):
            event_type = _opt_text(node, "type")
        detail = self._event_detail(node)
        occurred = self._bool(node, "occurred")
        if occurred is None:
            occurred = detail is None and text is None
        return Event(tag, occurred=occurred, text=text, type=event_type, detail=detail)

    def _attribute(self, value: object) -> Attribute:
        node = _mapping(value, "attribute")
        return Attribute(
            _req_text(node, "attribute", "tag").upper(),
            _req_text(node, "attribute", "value"),
            type=_opt_text(node, "type"),
            detail=self._event_detail(node),
        )

    def _event_detail(self, node: dict[str, Any]) -> EventDetail | None:
        detail = EventDetail()
        present = False
        date = _get(node, "date")
        if date is not None:
            with at(".date"):
                detail.date = parse_date(date)
            detail.date_time = self._time(node, "time")
            detail.date_phrase = _opt_text(node, "date_phrase")
            present = True
        sort_date = _get(node, "sort_date", "sdate")
        if sort_date is not None:
            with at(".sort_date"):
                detail.sort_date = parse_date(sort_date)
            detail.sort_date_time = self._time(node, "sort_time")
            detail.sort_date_phrase = _opt_text(node, "sort_phrase")
            present = True
        age = _get(node, "age")
        if age is not None:
            with at(".age"):
                detail.age = self._age(age)
            detail.age_phrase = _opt_text(node, "age_phrase")
            present = True
        for key, age_attr, phrase_attr in (
            ("husband_age", "husband_age", "husband_age_phrase"),
            ("wife_age", "wife_age", "wife_age_phrase"),
        ):
            raw = _get(node, key)
            if raw is not None:
                with at(f".{key}"):
                    setattr(detail, age_attr, self._age(raw))
                setattr(detail, phrase_attr, _opt_text(node, f"{key}_phrase"))
                present = True
        place = _get(node, "place")
        if place is not None:
            with at(".place"):
                detail.place = self._place(place)
            present = True
        address = self._opt_address(node)
        if address is not None:
            detail.address = address
            present = True
        for attr, keys in (
            ("phones", ("phones", "phone")),
            ("emails", ("emails", "email")),
            ("faxes", ("faxes", "fax")),
            ("web_pages", ("web_pages", "www")),
        ):
            values = self._strings(node, *keys)
            if values:
                setattr(detail, attr, values)
                present = True
        for attr in ("agency", "religion", "cause"):
            value = _opt_text(node, attr)
            if value is not None:
                setattr(detail, attr, value)
                present = True
        famc = _get(node, "family_child", "famc")
        if famc is not None:
            with at(".family_child"):
                detail.family_child = self._resolve(famc, Family, "family_child")
            with at(".adopting_parent"):
                detail.adopting_parent = self._enum(
                    _get(node, "adopting_parent"), _AdoptingParent, "adopting parent"
                )
            detail.adopting_parent_phrase = _opt_text(node, "adopting_parent_phrase")
            present = True
        return detail if present else None

    def _non_event(self, value: object) -> NonEvent:
        node = _mapping(value, "non-event")
        period: DatePeriod | None = None
        date = _get(node, "date")
        if date is not None:
            with at(".date"):
                parsed = parse_date(date)
                if not isinstance(parsed, DatePeriod):
                    raise LoadError("a non-event date must be a period (e.g. 'FROM 1900 TO 1910')")
                period = parsed
        return NonEvent(
            _req_text(node, "non-event", "tag", "event").upper(),
            date=period,
            date_phrase=_opt_text(node, "date_phrase"),
        )

    def _child(self, value: object) -> Individual | ChildLink | VoidPointer:
        if isinstance(value, str):
            if value.strip().strip("@").upper() in ("", "VOID"):
                return VOID
            return self._resolve(value, Individual, "child")
        node = _mapping(value, "child")
        ref = _get(node, "individual", "child", "ref", "xref")
        with at(".individual"):
            individual = self._resolve(ref, Individual, "child")
        with at(".pedigree"):
            pedigree = self._enum(_get(node, "pedigree"), Pedigree, "pedigree")
        with at(".status"):
            status = self._enum(_get(node, "status"), FamcStatus, "child status")
        return ChildLink(
            individual,
            pedigree=pedigree,
            pedigree_phrase=_opt_text(node, "pedigree_phrase"),
            status=status,
            status_phrase=_opt_text(node, "status_phrase"),
        )

    def _association(self, value: object) -> Association:
        node = _mapping(value, "association")
        ref = _get(node, "person", "individual", "ref")
        with at(".person"):
            person = self._resolve_or_void(ref, Individual, "association person")
        with at(".role"):
            role = self._enum_required(_get(node, "role"), Role, "role")
        return Association(
            person,
            role,
            phrase=_opt_text(node, "phrase"),
            role_phrase=_opt_text(node, "role_phrase"),
            notes=self._notes(node),
            source_citations=self._citations(node),
        )

    def _alias(self, value: object) -> Alias:
        if isinstance(value, str):
            return Alias(self._resolve(value, Individual, "alias"))
        node = _mapping(value, "alias")
        ref = _get(node, "individual", "ref")
        with at(".individual"):
            individual = self._resolve(ref, Individual, "alias")
        return Alias(individual, phrase=_opt_text(node, "phrase"))

    def _lds_individual(self, value: object) -> LdsIndividualOrdinance:
        node = _mapping(value, "ordinance")
        family = None
        ref = _get(node, "family", "famc")
        if ref is not None:
            with at(".family"):
                family = self._resolve(ref, Family, "ordinance family")
        return LdsIndividualOrdinance(
            _req_text(node, "ordinance", "tag").upper(),
            detail=self._ordinance_detail(_get(node, "detail") or node),
            family=family,
        )

    def _spouse_sealing(self, value: object) -> LdsSpouseSealing:
        node = _mapping(value, "sealing")
        return LdsSpouseSealing(detail=self._ordinance_detail(_get(node, "detail") or node))

    def _ordinance_detail(self, value: object) -> LdsOrdinanceDetail | None:
        node = _mapping(value, "ordinance detail")
        detail = LdsOrdinanceDetail()
        present = False
        date = _get(node, "date")
        if date is not None:
            with at(".date"):
                detail.date = parse_date(date)
            detail.date_time = self._time(node, "time")
            detail.date_phrase = _opt_text(node, "date_phrase")
            present = True
        temple = _opt_text(node, "temple", "temp")
        if temple is not None:
            detail.temple = temple
            present = True
        place = _get(node, "place")
        if place is not None:
            with at(".place"):
                detail.place = self._place(place)
            present = True
        status = _get(node, "status")
        if status is not None:
            with at(".status"):
                detail.status = self._enum(status, OrdinanceStatus, "ordinance status")
            with at(".status_date"):
                detail.status_date = parse_date_exact(_require(node, "status_date", "ordinance"))
            detail.status_time = self._time(node, "status_time")
            present = True
        return detail if present else None

    def _identifier(self, value: object) -> Identifier:
        node = _mapping(value, "identifier")
        kind = _req_text(node, "identifier", "kind", "type_of").upper()
        identifier_type: str | ExidType | None
        if kind == "EXID":
            with at(".type"):
                identifier_type = self._exid_type(_get(node, "type"))
        else:
            identifier_type = _opt_text(node, "type")
        return Identifier(kind, _req_text(node, "identifier", "value"), type=identifier_type)

    def _note(self, value: object) -> Note | SharedNote:
        if isinstance(value, str):
            return Note(value)
        node = _mapping(value, "note")
        ref = _get(node, "ref", "shared", "snote")
        if ref is not None:
            return self._resolve(ref, SharedNote, "note")
        return Note(
            _req_text(node, "note", "text", "value"),
            mime=_opt_text(node, "mime"),
            language=_opt_text(node, "language", "lang"),
            translations=self._each(node, self._note_translation, "translations"),
        )

    def _note_translation(self, value: object) -> NoteTranslation:
        node = _mapping(value, "note translation")
        return NoteTranslation(
            _req_text(node, "note translation", "text", "value"),
            mime=_opt_text(node, "mime"),
            language=_opt_text(node, "language", "lang"),
        )

    def _citation(self, value: object) -> SourceCitation:
        if isinstance(value, str):
            return SourceCitation(self._resolve_or_void(value, Source, "source citation"))
        node = _mapping(value, "source citation")
        ref = _get(node, "source", "ref")
        with at(".source"):
            source = self._resolve_or_void(ref, Source, "source citation")
        with at(".role"):
            role = self._enum(_get(node, "role"), Role, "role")
        with at(".quality"):
            quality = self._enum(_get(node, "quality"), Quality, "quality")
        data_date = _get(node, "data_date")
        parsed_date = None
        if data_date is not None:
            with at(".data_date"):
                parsed_date = parse_date(data_date)
        return SourceCitation(
            source,
            page=_opt_text(node, "page"),
            data_date=parsed_date,
            data_texts=self._strings(node, "data_texts", "text"),
            event=_opt_text(node, "event"),
            event_phrase=_opt_text(node, "event_phrase"),
            role=role,
            role_phrase=_opt_text(node, "role_phrase"),
            quality=quality,
            notes=self._notes(node),
            media_links=self._media(node),
        )

    def _media_link(self, value: object) -> MultimediaLink:
        if isinstance(value, str):
            return MultimediaLink(self._resolve_or_void(value, Multimedia, "media link"))
        node = _mapping(value, "media link")
        ref = _get(node, "multimedia", "object", "ref")
        with at(".multimedia"):
            multimedia = self._resolve_or_void(ref, Multimedia, "media link")
        crop = _get(node, "crop")
        return MultimediaLink(
            multimedia,
            crop=self._crop(crop) if crop is not None else None,
            title=_opt_text(node, "title"),
        )

    def _crop(self, value: object) -> Crop:
        node = _mapping(value, "crop")
        return Crop(
            top=self._opt_int(node, "top"),
            left=self._opt_int(node, "left"),
            height=self._opt_int(node, "height"),
            width=self._opt_int(node, "width"),
        )

    def _file(self, value: object) -> File:
        node = _mapping(value, "file")
        with at(".medium"):
            medium = self._enum(_get(node, "medium", "medi"), Medium, "medium")
        return File(
            _req_text(node, "file", "path"),
            _req_text(node, "file", "form", "format"),
            medium=medium,
            title=_opt_text(node, "title"),
            translations=self._each(node, self._file_translation, "translations"),
        )

    def _file_translation(self, value: object) -> FileTranslation:
        node = _mapping(value, "file translation")
        return FileTranslation(
            _req_text(node, "file translation", "path"),
            _req_text(node, "file translation", "form", "format"),
        )

    def _repo_citation(self, value: object) -> SourceRepositoryCitation:
        if isinstance(value, str):
            return SourceRepositoryCitation(self._resolve(value, Repository, "repository"))
        node = _mapping(value, "repository citation")
        ref = _get(node, "repository", "repo", "ref")
        with at(".repository"):
            repository = self._resolve(ref, Repository, "repository")
        return SourceRepositoryCitation(
            repository,
            call_numbers=self._each(node, self._call_number, "call_numbers"),
        )

    def _call_number(self, value: object) -> CallNumber:
        if isinstance(value, str):
            return CallNumber(value)
        node = _mapping(value, "call number")
        with at(".medium"):
            medium = self._enum(_get(node, "medium", "medi"), Medium, "medium")
        return CallNumber(_req_text(node, "call number", "value"), medium=medium)

    def _source_data(self, value: object) -> SourceData:
        node = _mapping(value, "source data")
        return SourceData(
            events=self._each(node, self._source_data_event, "events"),
            agency=_opt_text(node, "agency"),
            notes=self._notes(node),
        )

    def _source_data_event(self, value: object) -> SourceDataEvent:
        node = _mapping(value, "source data event")
        events = [_text(item, "event tag").upper() for item in _items(node, "events", "tags")]
        period: DatePeriod | None = None
        date = _get(node, "date")
        if date is not None:
            with at(".date"):
                parsed = parse_date(date)
                if not isinstance(parsed, DatePeriod):
                    raise LoadError("a source-data event date must be a period")
                period = parsed
        place = _get(node, "place")
        return SourceDataEvent(
            events,
            date=period,
            date_phrase=_opt_text(node, "date_phrase"),
            place=self._place(place) if place is not None else None,
        )

    def _place(self, value: object) -> Place:
        if isinstance(value, (str, list)):
            return Place(_text_list(value, "place"))
        node = _mapping(value, "place")
        form = _get(node, "form")
        map_value = _get(node, "map")
        return Place(
            _text_list(_require(node, "names", "place"), "place"),
            form=_text_list(form, "place form") if form is not None else None,
            language=_opt_text(node, "language", "lang"),
            translations=self._each(node, self._place_translation, "translations"),
            map=self._map(map_value) if map_value is not None else None,
        )

    def _place_translation(self, value: object) -> PlaceTranslation:
        node = _mapping(value, "place translation")
        return PlaceTranslation(
            _text_list(_require(node, "names", "place translation"), "place translation"),
            _req_text(node, "place translation", "language", "lang"),
        )

    def _map(self, value: object) -> Map:
        if isinstance(value, list):
            if len(value) != 2:
                raise LoadError("a map must be [latitude, longitude]")
            latitude, longitude = value[0], value[1]
        else:
            node = _mapping(value, "map")
            latitude = _require(node, "latitude", "map", "lat")
            longitude = _require(node, "longitude", "map", "long", "lon")
        return Map(
            Latitude(_float(latitude, "latitude")), Longitude(_float(longitude, "longitude"))
        )

    def _opt_address(self, node: dict[str, Any]) -> Address | None:
        value = _get(node, "address")
        if value is None:
            return None
        if isinstance(value, str):
            return Address(value)
        address = _mapping(value, "address")
        return Address(
            _req_text(address, "address", "value", "full"),
            city=_opt_text(address, "city"),
            state=_opt_text(address, "state", "stae"),
            postal_code=_opt_text(address, "postal_code", "post"),
            country=_opt_text(address, "country", "ctry"),
        )

    def _age(self, value: object) -> Age:
        if isinstance(value, dict):
            return Age(
                years=self._opt_int(value, "years"),
                months=self._opt_int(value, "months"),
                weeks=self._opt_int(value, "weeks"),
                days=self._opt_int(value, "days"),
                bound=_opt_text(value, "bound"),
            )
        if isinstance(value, int) and not isinstance(value, bool):
            return Age(years=value)
        return _parse_age(_text(value, "age"))

    def _time(self, node: dict[str, Any], key: str) -> Time | None:
        value = _get(node, key)
        if value is None:
            return None
        with at(f".{key}"):
            if isinstance(value, dict):
                return Time(
                    _int(_require(value, "hour", "time"), "hour"),
                    _int(_require(value, "minute", "time"), "minute"),
                    second=self._opt_int(value, "second"),
                    fraction=self._opt_int(value, "fraction"),
                    utc=bool(_get(value, "utc")),
                )
            return _parse_time(_text(value, "time"))

    # -- small list helpers --------------------------------------------------

    def _strings(self, node: dict[str, Any], *keys: str) -> list[str]:
        return [_text(item, keys[0]) for item in _items(node, *keys)]

    def _refs(self, node: dict[str, Any], expected: type[R], *keys: str) -> list[R]:
        out: list[R] = []
        for index, item in enumerate(_items(node, *keys)):
            with at(f".{keys[0]}[{index}]"):
                out.append(self._resolve(item, expected, keys[0]))
        return out

    def _notes(self, node: dict[str, Any]) -> list[Note | SharedNote]:
        return self._each(node, self._note, "notes")

    def _citations(self, node: dict[str, Any]) -> list[SourceCitation]:
        return self._each(node, self._citation, "sources", "source_citations")

    def _media(self, node: dict[str, Any]) -> list[MultimediaLink]:
        return self._each(node, self._media_link, "media", "media_links")

    def _enum_list(self, node: dict[str, Any], enum_cls: type[E], *keys: str) -> list[E | str]:
        out: list[E | str] = []
        for index, item in enumerate(_items(node, *keys)):
            with at(f".{keys[0]}[{index}]"):
                out.append(self._enum_required(item, enum_cls, keys[0]))
        return out

    def _bool(self, node: dict[str, Any], key: str) -> bool | None:
        value = _get(node, key)
        if value is None:
            return None
        if not isinstance(value, bool):
            raise LoadError(f"{key!r} must be true or false", path=f".{key}")
        return value

    def _opt_int(self, node: dict[str, Any], key: str) -> int | None:
        value = _get(node, key)
        return None if value is None else _int(value, key)

    def _change_date(self, value: object) -> ChangeDate:
        node = _mapping(value, "change date")
        return ChangeDate(
            parse_date_exact(_require(node, "date", "change date")),
            time=self._time(node, "time"),
            notes=self._notes(node),
        )

    def _creation_date(self, value: object) -> CreationDate:
        node = _mapping(value, "creation date")
        return CreationDate(
            parse_date_exact(_require(node, "date", "creation date")),
            time=self._time(node, "time"),
        )

    # -- header --------------------------------------------------------------

    def _build_header(self) -> Header:
        from .. import __version__

        raw = _get(self._mapping, "header")
        node = _mapping(raw, "header") if raw is not None else {}
        with at(".header"):
            source = self._header_source(_get(node, "source"))
            if source is None:
                source = HeaderSource(product="gedcom7", version=__version__)
            submitter = None
            ref = _get(node, "submitter")
            if ref is not None:
                with at(".submitter"):
                    submitter = self._resolve(ref, Submitter, "header submitter")
            date = _get(node, "date")
            place_form = _get(node, "place_form")
            note = _get(node, "note")
            schema_raw = _get(node, "schema")
            return Header(
                gedcom_version=_opt_text(self._mapping, "gedcom_version") or "7.0",
                source=source,
                destination=_opt_text(node, "destination", "dest"),
                date=parse_date_exact(date) if date is not None else None,
                time=self._time(node, "time"),
                submitter=submitter,
                language=_opt_text(node, "language", "lang"),
                place_form=_text_list(place_form, "place form") if place_form is not None else None,
                copyright=_opt_text(node, "copyright"),
                note=self._inline_note(note) if note is not None else None,
                schema=self._schema(schema_raw),
            )

    def _header_source(self, value: object) -> HeaderSource | None:
        if value is None:
            return None
        if isinstance(value, str):
            return HeaderSource(product=value)
        node = _mapping(value, "header source")
        return HeaderSource(
            product=_req_text(node, "header source", "product", "name"),
            version=_opt_text(node, "version"),
            name=_opt_text(node, "full_name", "title"),
            corporation=_opt_text(node, "corporation", "corp"),
        )

    def _inline_note(self, value: object) -> Note:
        note = self._note(value)
        if isinstance(note, SharedNote):
            raise LoadError("the header note must be an inline note, not a shared-note reference")
        return note

    def _schema(self, value: object) -> dict[str, str]:
        if value is None:
            return {}
        node = _mapping(value, "schema")
        return {_text(key, "schema tag"): _text(uri, "schema uri") for key, uri in node.items()}


# --- module-level value parsers (no registry needed) ------------------------

# AdoptingParent lives in enums but is only needed here; import lazily-friendly.
from ..enums import AdoptingParent as _AdoptingParent  # noqa: E402


def _require(node: dict[str, Any], key: str, what: str, *aliases: str) -> Any:
    value = _get(node, key, *aliases)
    if value is None:
        raise LoadError(f"missing required {key!r} for {what}")
    return value


def _req_text(node: dict[str, Any], what: str, *keys: str) -> str:
    value = _opt_text(node, *keys)
    if value is None:
        raise LoadError(f"missing required {keys[0]!r} for {what}")
    return value


def _parse_time(text: str) -> Time:
    raw = text.strip()
    utc = raw.endswith(("Z", "z"))
    if utc:
        raw = raw[:-1]
    parts = raw.split(":")
    if len(parts) not in (2, 3):
        raise LoadError(f"{text!r} is not a valid time (HH:MM[:SS])")
    hour = _int(parts[0], "hour")
    minute = _int(parts[1], "minute")
    second: int | None = None
    fraction: int | None = None
    if len(parts) == 3:
        sec_text = parts[2]
        if "." in sec_text:
            whole, frac = sec_text.split(".", 1)
            second = _int(whole, "second")
            fraction = _int(frac, "fraction")
        else:
            second = _int(sec_text, "second")
    return Time(hour, minute, second=second, fraction=fraction, utc=utc)


def _parse_age(text: str) -> Age:
    tokens = text.upper().split()
    if not tokens:
        raise LoadError("empty age")
    bound: str | None = None
    if tokens[0] in ("<", ">"):
        bound = tokens.pop(0)
    units: dict[str, int] = {}
    suffixes = {"Y": "years", "M": "months", "W": "weeks", "D": "days"}
    for token in tokens:
        if len(token) < 2 or token[-1] not in suffixes or not token[:-1].isdigit():
            raise LoadError(f"{token!r} in age {text!r} is not a count like '72y'")
        units[suffixes[token[-1]]] = int(token[:-1])
    if not units and bound is None:
        raise LoadError(f"{text!r} is not a valid age")
    return Age(
        years=units.get("years"),
        months=units.get("months"),
        weeks=units.get("weeks"),
        days=units.get("days"),
        bound=bound,
    )
