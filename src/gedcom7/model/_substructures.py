"""Reusable substructure blocks (§3.2.3): name structures, and (later)
places, addresses, citations, events, and the like.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..enums import NameType


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
