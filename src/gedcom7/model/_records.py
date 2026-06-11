"""Top-level record types (§3.2.2): the entities that live at level 0.

Records are mutable so references can be wired after construction (ADR-0003)
and link to one another by object reference (ADR-0001). ``xref_id`` is an
optional preferred id (without ``@``); when ``None`` the writer auto-assigns.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..enums import Sex
from ._pointers import VoidPointer
from ._substructures import (
    Address,
    Attribute,
    Event,
    Identifier,
    LdsOrdinanceDetail,
    NonEvent,
    PersonalName,
)


@dataclass
class LdsIndividualOrdinance:
    """An individual LDS ordinance (`BAPL`/`CONL`/`ENDL`/`INIL`/`SLGC`).

    ``SLGC`` (sealing child to parents) requires ``family`` (`FAMC`); the
    others do not use it.
    """

    tag: str
    detail: LdsOrdinanceDetail | None = None
    family: Family | None = None


@dataclass
class LdsSpouseSealing:
    """A spouse sealing (`SLGS`), a family-level LDS ordinance."""

    detail: LdsOrdinanceDetail | None = None


@dataclass
class Submitter:
    """The contributor of data in the document (`SUBM`)."""

    name: str
    address: Address | None = None
    phones: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    faxes: list[str] = field(default_factory=list)
    web_pages: list[str] = field(default_factory=list)
    identifiers: list[Identifier] = field(default_factory=list)
    xref_id: str | None = None


@dataclass
class Individual:
    """A person (`INDI`)."""

    names: list[PersonalName] = field(default_factory=list)
    sex: Sex | str | None = None
    attributes: list[Attribute] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    non_events: list[NonEvent] = field(default_factory=list)
    lds_ordinances: list[LdsIndividualOrdinance] = field(default_factory=list)
    identifiers: list[Identifier] = field(default_factory=list)
    xref_id: str | None = None


@dataclass
class Family:
    """A family unit (`FAM`) linking spouses and children.

    ``children`` is in birth-chronological order; a :data:`VoidPointer`
    entry marks an unknown child in birth order. The matching ``FAMS``/
    ``FAMC`` back-pointers on the linked individuals are derived by the
    writer (ADR-0001), not stored here.
    """

    husband: Individual | None = None
    wife: Individual | None = None
    children: list[Individual | VoidPointer] = field(default_factory=list)
    attributes: list[Attribute] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    non_events: list[NonEvent] = field(default_factory=list)
    sealings: list[LdsSpouseSealing] = field(default_factory=list)
    identifiers: list[Identifier] = field(default_factory=list)
    xref_id: str | None = None
