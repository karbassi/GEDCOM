"""Typed enumerations for GEDCOM 7 enumerated payloads (§3.4).

One :class:`enum.StrEnum` per enumeration set, emitting the exact spec
strings. Anywhere the spec permits extension enum values, a ``_``-prefixed
string is accepted via :func:`enum_value` / :func:`enum_list`; bare
standard strings are rejected so callers use the typed enum.
"""

from __future__ import annotations

from enum import StrEnum


class Sex(StrEnum):
    MALE = "M"
    FEMALE = "F"
    INTERSEX = "X"
    UNKNOWN = "U"


class Restriction(StrEnum):
    """`RESN` values (a List:Enum payload)."""

    CONFIDENTIAL = "CONFIDENTIAL"
    LOCKED = "LOCKED"
    PRIVACY = "PRIVACY"


class Medium(StrEnum):
    """`MEDI` source-medium values."""

    AUDIO = "AUDIO"
    BOOK = "BOOK"
    CARD = "CARD"
    ELECTRONIC = "ELECTRONIC"
    FICHE = "FICHE"
    FILM = "FILM"
    MAGAZINE = "MAGAZINE"
    MANUSCRIPT = "MANUSCRIPT"
    MAP = "MAP"
    NEWSPAPER = "NEWSPAPER"
    PHOTO = "PHOTO"
    TOMBSTONE = "TOMBSTONE"
    VIDEO = "VIDEO"
    OTHER = "OTHER"


class Pedigree(StrEnum):
    """`PEDI` child-to-family relationship values."""

    ADOPTED = "ADOPTED"
    BIRTH = "BIRTH"
    FOSTER = "FOSTER"
    SEALING = "SEALING"
    OTHER = "OTHER"


class Quality(StrEnum):
    """`QUAY` certainty values (literal digit strings, not numeric)."""

    UNRELIABLE = "0"
    QUESTIONABLE = "1"
    SECONDARY = "2"
    DIRECT = "3"


class Role(StrEnum):
    """`ROLE` values for associations and source-event roles."""

    CHILD = "CHIL"
    CLERGY = "CLERGY"
    FATHER = "FATH"
    FRIEND = "FRIEND"
    GODPARENT = "GODP"
    HUSBAND = "HUSB"
    MOTHER = "MOTH"
    MULTIPLE = "MULTIPLE"
    NEIGHBOR = "NGHBR"
    OFFICIATOR = "OFFICIATOR"
    PARENT = "PARENT"
    SPOUSE = "SPOU"
    WIFE = "WIFE"
    WITNESS = "WITN"
    OTHER = "OTHER"


class NameType(StrEnum):
    """`NAME.TYPE` values."""

    AKA = "AKA"
    BIRTH = "BIRTH"
    IMMIGRANT = "IMMIGRANT"
    MAIDEN = "MAIDEN"
    MARRIED = "MARRIED"
    PROFESSIONAL = "PROFESSIONAL"
    OTHER = "OTHER"


class FamcStatus(StrEnum):
    """`FAMC.STAT` values."""

    CHALLENGED = "CHALLENGED"
    DISPROVEN = "DISPROVEN"
    PROVEN = "PROVEN"


class AdoptingParent(StrEnum):
    """`ADOP` (adopting-parent) values."""

    HUSBAND = "HUSB"
    WIFE = "WIFE"
    BOTH = "BOTH"


class OrdinanceStatus(StrEnum):
    """`ord-STAT` LDS ordinance status values."""

    BIC = "BIC"
    CANCELED = "CANCELED"
    CHILD = "CHILD"
    COMPLETED = "COMPLETED"
    DNS = "DNS"
    DNS_CAN = "DNS_CAN"
    EXCLUDED = "EXCLUDED"
    INFANT = "INFANT"
    PRE_1970 = "PRE_1970"
    STILLBORN = "STILLBORN"
    SUBMITTED = "SUBMITTED"
    UNCLEARED = "UNCLEARED"


class ExidType(StrEnum):
    """Registered ``EXID``.``TYPE`` authority URIs (`uri/exid-types`).

    `EXID` without a `TYPE` is deprecated; these are the registered
    external-identifier authorities, each value the exact registry URI.
    Unregistered authorities may still pass a raw URI string.
    """

    AFN = "https://gedcom.io/terms/v7/AFN"
    BILLIONGRAVES_CEMETERY_ID = "https://www.billiongraves.com/cemetery/name/"
    BILLIONGRAVES_GRAVE_ID = "https://www.billiongraves.com/grave/name/"
    FAMILYSEARCH_MEMORY_ID = "https://gedcom.io/exid-type/FamilySearch-MemoryId"
    FAMILYSEARCH_PERSON_ID = "https://gedcom.io/exid-type/FamilySearch-PersonId"
    FAMILYSEARCH_PLACE_ID = "https://gedcom.io/exid-type/FamilySearch-PlaceId"
    FAMILYSEARCH_SOURCE_DESCRIPTION_ID = (
        "https://gedcom.io/exid-type/FamilySearch-SourceDescriptionId"
    )
    FAMILYSEARCH_USER_ID = "https://gedcom.io/exid-type/FamilySearch-UserId"
    FINDAGRAVE_CEMETERY_ID = "https://www.findagrave.com/cemetery/"
    FINDAGRAVE_MEMORIAL_ID = "https://www.findagrave.com/memorial/"
    GOV_ID = "https://gov.genealogy.net/"
    RFN = "https://gedcom.io/terms/v7/RFN"
    RIN = "https://gedcom.io/terms/v7/RIN"
    WIKITREE_PERSON_ID = "https://www.wikitree.com/wiki/"


def enum_value[E: StrEnum](value: E | str, enum_cls: type[E]) -> str:
    """Resolve an enum member or a `_`-prefixed extension string to its payload.

    A bare standard string (not a member, not extension) is rejected so that
    standard values are expressed via the typed enum.
    """
    if isinstance(value, enum_cls):
        return str(value)
    if value.startswith("_"):
        return value
    raise ValueError(
        f"{value!r} is not a permitted {enum_cls.__name__} value; "
        f"use the {enum_cls.__name__} enum, or a '_'-prefixed extension value"
    )


def enum_list[E: StrEnum](values: list[E | str], enum_cls: type[E]) -> str:
    """Resolve a List:Enum payload to its comma-space-joined string."""
    return ", ".join(enum_value(v, enum_cls) for v in values)
