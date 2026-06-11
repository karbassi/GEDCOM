"""Top-level record types (§3.2.2): the entities that live at level 0.

Records are mutable so references can be wired after construction (ADR-0003)
and link to one another by object reference (ADR-0001). ``xref_id`` is an
optional preferred id (without ``@``); when ``None`` the writer auto-assigns.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..enums import Quality, Restriction, Role, Sex
from ..types import DateExact, DatePeriod, DateValue, Time
from ._pointers import VoidPointer
from ._substructures import (
    Address,
    Attribute,
    CallNumber,
    Crop,
    Event,
    ExtensionStructure,
    File,
    Identifier,
    LdsOrdinanceDetail,
    NonEvent,
    Note,
    NoteTranslation,
    PersonalName,
    Place,
)


@dataclass
class ChangeDate:
    """When a record was last changed (`CHANGE_DATE`)."""

    date: DateExact
    time: Time | None = None
    notes: list[Note | SharedNote] = field(default_factory=list)


@dataclass
class CreationDate:
    """When a record was created (`CREATION_DATE`); not updated thereafter."""

    date: DateExact
    time: Time | None = None


@dataclass(kw_only=True)
class RecordBase:
    """Fields common to every top-level record.

    ``xref_id`` is an optional preferred cross-reference id (ADR-0001);
    ``change_date``/``creation_date`` are the record's metadata. These are
    keyword-only so they sort after each record's own positional fields.
    """

    xref_id: str | None = None
    change_date: ChangeDate | None = None
    creation_date: CreationDate | None = None
    extensions: list[ExtensionStructure] = field(default_factory=list)


@dataclass
class SharedNote(RecordBase):
    """A reusable note record (`SNOTE`) pointed to by other structures."""

    text: str
    mime: str | None = None
    language: str | None = None
    translations: list[NoteTranslation] = field(default_factory=list)
    source_citations: list[SourceCitation] = field(default_factory=list)
    identifiers: list[Identifier] = field(default_factory=list)


@dataclass
class Multimedia(RecordBase):
    """A record referencing one or more external media files (`OBJE`)."""

    files: list[File] = field(default_factory=list)
    restrictions: list[Restriction | str] = field(default_factory=list)
    notes: list[Note | SharedNote] = field(default_factory=list)
    source_citations: list[SourceCitation] = field(default_factory=list)
    identifiers: list[Identifier] = field(default_factory=list)


@dataclass
class MultimediaLink:
    """A link to a Multimedia record (`MULTIMEDIA_LINK`)."""

    multimedia: Multimedia | VoidPointer
    crop: Crop | None = None
    title: str | None = None


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
class Submitter(RecordBase):
    """The contributor of data in the document (`SUBM`)."""

    name: str
    address: Address | None = None
    phones: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    faxes: list[str] = field(default_factory=list)
    web_pages: list[str] = field(default_factory=list)
    media_links: list[MultimediaLink] = field(default_factory=list)
    notes: list[Note | SharedNote] = field(default_factory=list)
    identifiers: list[Identifier] = field(default_factory=list)


@dataclass
class Individual(RecordBase):
    """A person (`INDI`)."""

    names: list[PersonalName] = field(default_factory=list)
    sex: Sex | str | None = None
    restrictions: list[Restriction | str] = field(default_factory=list)
    attributes: list[Attribute] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    non_events: list[NonEvent] = field(default_factory=list)
    lds_ordinances: list[LdsIndividualOrdinance] = field(default_factory=list)
    associations: list[Association] = field(default_factory=list)
    submitters: list[Submitter] = field(default_factory=list)
    aliases: list[Alias] = field(default_factory=list)
    ancestor_interest: list[Submitter] = field(default_factory=list)
    descendant_interest: list[Submitter] = field(default_factory=list)
    notes: list[Note | SharedNote] = field(default_factory=list)
    source_citations: list[SourceCitation] = field(default_factory=list)
    media_links: list[MultimediaLink] = field(default_factory=list)
    identifiers: list[Identifier] = field(default_factory=list)


@dataclass
class Family(RecordBase):
    """A family unit (`FAM`) linking spouses and children.

    ``children`` is in birth-chronological order; a :data:`VoidPointer`
    entry marks an unknown child in birth order. The matching ``FAMS``/
    ``FAMC`` back-pointers on the linked individuals are derived by the
    writer (ADR-0001), not stored here.
    """

    husband: Individual | None = None
    wife: Individual | None = None
    children: list[Individual | VoidPointer] = field(default_factory=list)
    restrictions: list[Restriction | str] = field(default_factory=list)
    attributes: list[Attribute] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    non_events: list[NonEvent] = field(default_factory=list)
    sealings: list[LdsSpouseSealing] = field(default_factory=list)
    associations: list[Association] = field(default_factory=list)
    submitters: list[Submitter] = field(default_factory=list)
    notes: list[Note | SharedNote] = field(default_factory=list)
    source_citations: list[SourceCitation] = field(default_factory=list)
    media_links: list[MultimediaLink] = field(default_factory=list)
    identifiers: list[Identifier] = field(default_factory=list)


@dataclass
class Repository(RecordBase):
    """An archive or library that holds sources (`REPO`)."""

    name: str
    address: Address | None = None
    phones: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    faxes: list[str] = field(default_factory=list)
    web_pages: list[str] = field(default_factory=list)
    notes: list[Note | SharedNote] = field(default_factory=list)
    identifiers: list[Identifier] = field(default_factory=list)


@dataclass
class SourceRepositoryCitation:
    """A citation from a Source to a Repository (`SOURCE_REPOSITORY_CITATION`)."""

    repository: Repository
    call_numbers: list[CallNumber] = field(default_factory=list)


@dataclass
class SourceDataEvent:
    """An event the source records data about (`SOUR.DATA.EVEN`)."""

    events: list[str]
    date: DatePeriod | None = None
    date_phrase: str | None = None
    place: Place | None = None


@dataclass
class SourceData:
    """Data the source provides (`SOUR.DATA`)."""

    events: list[SourceDataEvent] = field(default_factory=list)
    agency: str | None = None
    notes: list[Note | SharedNote] = field(default_factory=list)


@dataclass
class Source(RecordBase):
    """A citable source of genealogical information (`SOUR`)."""

    author: str | None = None
    title: str | None = None
    abbreviation: str | None = None
    publication: str | None = None
    text: str | None = None
    text_mime: str | None = None
    text_language: str | None = None
    data: SourceData | None = None
    repository_citations: list[SourceRepositoryCitation] = field(default_factory=list)
    notes: list[Note | SharedNote] = field(default_factory=list)
    media_links: list[MultimediaLink] = field(default_factory=list)
    identifiers: list[Identifier] = field(default_factory=list)


@dataclass
class SourceCitation:
    """A citation pointing at a Source (`SOURCE_CITATION`).

    ``source`` may be a :data:`VoidPointer` when no Source record exists,
    with ``page`` describing the whole source.
    """

    source: Source | VoidPointer
    page: str | None = None
    data_date: DateValue | None = None
    data_texts: list[str] = field(default_factory=list)
    event: str | None = None
    event_phrase: str | None = None
    role: Role | str | None = None
    role_phrase: str | None = None
    quality: Quality | str | None = None
    notes: list[Note | SharedNote] = field(default_factory=list)
    media_links: list[MultimediaLink] = field(default_factory=list)


@dataclass
class Association:
    """A relationship to another individual (`ASSOCIATION_STRUCTURE`).

    ``person`` may be a :data:`VoidPointer` (with ``phrase`` describing
    someone not in any record). ``role`` is required.
    """

    person: Individual | VoidPointer
    role: Role | str
    phrase: str | None = None
    role_phrase: str | None = None
    notes: list[Note | SharedNote] = field(default_factory=list)
    source_citations: list[SourceCitation] = field(default_factory=list)


@dataclass
class Alias:
    """An alternate self of an individual (`ALIA`)."""

    individual: Individual
    phrase: str | None = None
