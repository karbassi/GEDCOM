"""The genealogical model: records, the Document aggregate, and value types.

Record types are mutable so references (including the cycles the format
requires) can be wired after construction; value/datatype types are frozen
(ADR-0003). Records link to one another by object reference, not by xref
string (ADR-0001).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Header:
    """Document metadata pseudo-record (`HEAD`)."""

    gedcom_version: str = "7.0"


@dataclass
class Document:
    """Top-level aggregate: a Header plus records, owning the xref namespace.

    The unit you build and hand to the writer. Wire form is
    ``HEAD`` … records … ``TRLR``.
    """

    header: Header = field(default_factory=Header)
    records: list[object] = field(default_factory=list)
