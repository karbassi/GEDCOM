"""The Document aggregate, the Header, and the Record protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from ..types import DateExact, Time
from ._records import ChangeDate, CreationDate, Submitter
from ._substructures import Note


def _empty_schema() -> dict[str, str]:
    return {}


@runtime_checkable
class Record(Protocol):
    """A top-level record: an optional xref override and change/creation dates."""

    xref_id: str | None
    change_date: ChangeDate | None
    creation_date: CreationDate | None


@dataclass
class HeaderSource:
    """The product that produced the file (`HEAD.SOUR`)."""

    product: str
    version: str | None = None
    name: str | None = None
    corporation: str | None = None


@dataclass
class Header:
    """Document metadata pseudo-record (`HEAD`)."""

    gedcom_version: str = "7.0"
    source: HeaderSource | None = None
    destination: str | None = None
    date: DateExact | None = None
    time: Time | None = None
    submitter: Submitter | None = None
    language: str | None = None
    place_form: list[str] | None = None
    copyright: str | None = None
    note: Note | None = None
    # Extension identifier (tag or enum value, ``_``-prefixed) → URI. A
    # SCHMA block is auto-emitted for the entries actually used (§1.5).
    schema: dict[str, str] = field(default_factory=_empty_schema)


@dataclass
class Document:
    """Top-level aggregate: a Header plus records, owning the xref namespace.

    The unit you build and hand to the writer. Wire form is
    ``HEAD`` … records … ``TRLR``.
    """

    header: Header = field(default_factory=Header)
    records: list[Record] = field(default_factory=list)
