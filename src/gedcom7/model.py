"""The genealogical model: records, the Document aggregate, and value types.

Record types are mutable so references (including the cycles the format
requires) can be wired after construction; value/datatype types are frozen
(ADR-0003). Records link to one another by object reference, not by xref
string (ADR-0001).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from .enums import NameType, Sex
from .types import DateExact, Time


@runtime_checkable
class Record(Protocol):
    """Anything that can be a top-level record: it carries an optional xref override.

    ``xref_id`` is the inner token (without ``@``); when ``None`` the writer
    auto-assigns a document-local id (ADR-0001).
    """

    xref_id: str | None


@dataclass
class Header:
    """Document metadata pseudo-record (`HEAD`)."""

    gedcom_version: str = "7.0"
    date: DateExact | None = None
    time: Time | None = None
    submitter: Submitter | None = None
    copyright: str | None = None


@dataclass
class Submitter:
    """The contributor of data in the document (`SUBM`)."""

    name: str
    phones: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    faxes: list[str] = field(default_factory=list)
    web_pages: list[str] = field(default_factory=list)
    xref_id: str | None = None


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
class Individual:
    """A person (`INDI`)."""

    names: list[PersonalName] = field(default_factory=list)
    sex: Sex | str | None = None
    xref_id: str | None = None


@dataclass
class Document:
    """Top-level aggregate: a Header plus records, owning the xref namespace.

    The unit you build and hand to the writer. Wire form is
    ``HEAD`` … records … ``TRLR``.
    """

    header: Header = field(default_factory=Header)
    records: list[Record] = field(default_factory=list)
