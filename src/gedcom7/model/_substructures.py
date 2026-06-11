"""Reusable substructure blocks (§3.2.3): name structures, and (later)
places, addresses, citations, events, and the like.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..enums import NameType
from ..types import DatePeriod, DateValue, Time


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


@dataclass
class EventDetail:
    """Shared detail for an event or attribute (`EVENT_DETAIL`).

    Place and address are added in a later slice; this carries the date and
    a few common single-value fields.
    """

    date: DateValue | None = None
    date_time: Time | None = None
    date_phrase: str | None = None
    agency: str | None = None  # AGNC
    religion: str | None = None  # RELI
    cause: str | None = None  # CAUS


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
