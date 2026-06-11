"""Top-level record types (§3.2.2): the entities that live at level 0.

Records are mutable so references can be wired after construction (ADR-0003)
and link to one another by object reference (ADR-0001). ``xref_id`` is an
optional preferred id (without ``@``); when ``None`` the writer auto-assigns.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..enums import Sex
from ._substructures import PersonalName


@dataclass
class Submitter:
    """The contributor of data in the document (`SUBM`)."""

    name: str
    phones: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    faxes: list[str] = field(default_factory=list)
    web_pages: list[str] = field(default_factory=list)
    xref_id: str | None = None


@dataclass
class Individual:
    """A person (`INDI`)."""

    names: list[PersonalName] = field(default_factory=list)
    sex: Sex | str | None = None
    xref_id: str | None = None
