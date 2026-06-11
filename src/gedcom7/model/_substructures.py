"""Reusable substructure blocks (§3.2.3): name structures, and (later)
places, addresses, citations, events, and the like.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..enums import AdoptingParent, ExidType, Medium, NameType, OrdinanceStatus
from ..types import DateExact, DatePeriod, DateValue, Latitude, Longitude, Time

if TYPE_CHECKING:
    from ._records import Family


@dataclass(frozen=True)
class NamePieces:
    """Optional structured pieces of a personal name (`PERSONAL_NAME_PIECES`)."""

    prefix: list[str] = field(default_factory=list)  # NPFX
    given: list[str] = field(default_factory=list)  # GIVN
    nickname: list[str] = field(default_factory=list)  # NICK
    surname_prefix: list[str] = field(default_factory=list)  # SPFX
    surname: list[str] = field(default_factory=list)  # SURN
    suffix: list[str] = field(default_factory=list)  # NSFX


@dataclass
class NameTranslation:
    """A translated form of a personal name (`NAME.TRAN`); `LANG` is required."""

    value: str
    language: str
    pieces: NamePieces | None = None


@dataclass
class PersonalName:
    """A personal name (`PERSONAL_NAME_STRUCTURE`).

    ``value`` is the authoritative name with the surname delimited by
    slashes, e.g. ``"Joseph /Allen/"``.
    """

    value: str
    type: NameType | str | None = None
    type_phrase: str | None = None
    pieces: NamePieces | None = None
    translations: list[NameTranslation] = field(default_factory=list)


@dataclass(frozen=True)
class Map:
    """A geographic coordinate (`MAP`); both LATI and LONG are required."""

    latitude: Latitude
    longitude: Longitude


@dataclass
class PlaceTranslation:
    """A translated place name (`PLAC.TRAN`); `LANG` is required."""

    names: list[str]
    language: str


@dataclass
class Place:
    """A hierarchical place (`PLACE_STRUCTURE`), smallest jurisdiction first."""

    names: list[str]
    form: list[str] | None = None
    language: str | None = None
    translations: list[PlaceTranslation] = field(default_factory=list)
    map: Map | None = None


@dataclass
class Address:
    """A mailing address (`ADDRESS_STRUCTURE`).

    ``value`` is the full formatted address (the authoritative ``ADDR``
    payload, which may be multi-line); the structured fields are optional.
    The deprecated ``ADR1/ADR2/ADR3`` lines are never emitted.
    """

    value: str
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None


@dataclass
class NoteTranslation:
    """A translated form of a note (`NOTE.TRAN`/`SNOTE.TRAN`).

    Must carry a ``mime`` and/or a ``language``.
    """

    text: str
    mime: str | None = None
    language: str | None = None


@dataclass
class Note:
    """An inline note (`NOTE`) with its text carried directly."""

    text: str
    mime: str | None = None
    language: str | None = None
    translations: list[NoteTranslation] = field(default_factory=list)


@dataclass
class CallNumber:
    """A repository call number (`CALN`) with an optional medium (`MEDI`)."""

    value: str
    medium: Medium | str | None = None


@dataclass
class FileTranslation:
    """An alternate-format copy of a media file (`FILE.TRAN`); FORM required."""

    path: str
    form: str


@dataclass
class File:
    """A media file reference (`FILE`); FORM (media type) is required."""

    path: str
    form: str
    medium: Medium | str | None = None
    title: str | None = None
    translations: list[FileTranslation] = field(default_factory=list)


@dataclass
class Crop:
    """A crop region within a linked image (`CROP`)."""

    top: int | None = None
    left: int | None = None
    height: int | None = None
    width: int | None = None


@dataclass
class Identifier:
    """An identifier (`IDENTIFIER_STRUCTURE`): one of ``REFN``, ``UID``, ``EXID``.

    ``type`` is the ``TYPE`` substructure (Text for ``REFN``, URI for
    ``EXID``); ``UID`` takes no type. Emitting ``EXID`` without a ``type`` is
    deprecated. For ``EXID`` prefer an :class:`~gedcom7.enums.ExidType` (a
    registered authority URI); a raw URI string is also accepted.
    """

    kind: str
    value: str
    type: str | ExidType | None = None


@dataclass
class EventDetail:
    """Shared detail for an event or attribute (`EVENT_DETAIL`)."""

    date: DateValue | None = None
    date_time: Time | None = None
    date_phrase: str | None = None
    place: Place | None = None
    address: Address | None = None
    phones: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    faxes: list[str] = field(default_factory=list)
    web_pages: list[str] = field(default_factory=list)
    agency: str | None = None  # AGNC
    religion: str | None = None  # RELI
    cause: str | None = None  # CAUS
    # Event-level FAMC (BIRT/CHR/ADOP): the family the event links the child to.
    family_child: Family | None = None  # FAMC
    adopting_parent: AdoptingParent | str | None = None  # ADOP.FAMC.ADOP
    adopting_parent_phrase: str | None = None


@dataclass
class Event:
    """An individual or family event.

    Standard event tags (`BIRT`, `DEAT`, `MARR`, …) carry a ``[Y|<NULL>]``
    payload: ``occurred=True`` emits ``Y``. The generic ``EVEN`` tag instead
    carries ``text`` and requires ``type``.
    """

    tag: str
    occurred: bool = False
    text: str | None = None
    type: str | None = None
    detail: EventDetail | None = None


@dataclass
class Attribute:
    """An individual or family attribute (`OCCU`, `RESI`, `NCHI`, `IDNO`, …).

    Presence asserts the attribute applied. ``IDNO`` and the generic ``FACT``
    require ``type``.
    """

    tag: str
    value: str
    type: str | None = None
    detail: EventDetail | None = None


@dataclass
class NonEvent:
    """An asserted non-occurrence (`NO`), e.g. ``NO MARR``."""

    event: str
    date: DatePeriod | None = None
    date_phrase: str | None = None


@dataclass
class LdsOrdinanceDetail:
    """Shared detail for an LDS ordinance (`LDS_ORDINANCE_DETAIL`).

    If ``status`` is set, ``status_date`` is required. Ordinance dates use
    the Gregorian calendar and should be 1830 or later.
    """

    date: DateValue | None = None
    date_time: Time | None = None
    date_phrase: str | None = None
    temple: str | None = None  # TEMP
    place: Place | None = None
    status: OrdinanceStatus | str | None = None  # STAT
    status_date: DateExact | None = None
    status_time: Time | None = None

    def __post_init__(self) -> None:
        if self.status is not None and self.status_date is None:
            raise ValueError("an ordinance STAT requires a DATE")


@dataclass(frozen=True)
class ExtensionStructure:
    """A `_`-prefixed extension structure (see :mod:`gedcom7.extensions`).

    Supply ``uri`` to declare an arbitrary, user-defined extension (any
    ``_``-tag); omit it to use a *registered* extension, whose URI is resolved
    from the registry. Either way the URI is auto-declared in ``HEAD.SCHMA``.
    ``children`` carries nested extension substructures. Construction rejects a
    tag without a ``_`` prefix, and an unregistered tag given no ``uri``.
    """

    tag: str
    value: str | None = None
    children: tuple[ExtensionStructure, ...] = ()
    uri: str | None = None

    def __post_init__(self) -> None:
        from ..extensions import registered_extension_uris

        if not self.tag.startswith("_"):
            raise ValueError(f"extension tag {self.tag!r} must start with '_'")
        if self.uri is None and self.tag not in registered_extension_uris():
            raise ValueError(
                f"{self.tag!r} is not a registered extension structure; pass "
                f"uri= to declare it, or use a registered tag: "
                f"{sorted(registered_extension_uris())}"
            )

    @property
    def schema_uri(self) -> str:
        """The URI declared in ``HEAD.SCHMA`` for this extension's tag."""
        from ..extensions import registered_extension_uris

        return self.uri or registered_extension_uris()[self.tag]
