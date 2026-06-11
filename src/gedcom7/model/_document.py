"""The Document aggregate, the Header, and the Record protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from ..types import DateExact, Time
from ._records import Submitter


@runtime_checkable
class Record(Protocol):
    """A top-level record: it carries an optional xref override (ADR-0001)."""

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
class Document:
    """Top-level aggregate: a Header plus records, owning the xref namespace.

    The unit you build and hand to the writer. Wire form is
    ``HEAD`` … records … ``TRLR``.
    """

    header: Header = field(default_factory=Header)
    records: list[Record] = field(default_factory=list)
