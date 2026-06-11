"""The genealogical model: records, the Document aggregate, and substructures.

Organized by the spec's own division — top-level records (§3.2.2) in
``_records`` and reusable substructure blocks (§3.2.3) in ``_substructures``,
with the aggregate and Record protocol in ``_document``. Value/datatype
objects live in :mod:`gedcom7.types`.
"""

from __future__ import annotations

from ._document import Document, Header, Record
from ._pointers import VOID, VoidPointer
from ._records import (
    Family,
    Individual,
    LdsIndividualOrdinance,
    LdsSpouseSealing,
    Multimedia,
    MultimediaLink,
    Repository,
    Source,
    SourceCitation,
    SourceRepositoryCitation,
    Submitter,
)
from ._substructures import (
    Address,
    Attribute,
    CallNumber,
    Crop,
    Event,
    EventDetail,
    File,
    FileTranslation,
    Identifier,
    LdsOrdinanceDetail,
    Map,
    NamePieces,
    NameTranslation,
    NonEvent,
    PersonalName,
    Place,
    PlaceTranslation,
)

__all__ = [
    "VOID",
    "Address",
    "Attribute",
    "CallNumber",
    "Crop",
    "Document",
    "Event",
    "EventDetail",
    "Family",
    "File",
    "FileTranslation",
    "Header",
    "Identifier",
    "Individual",
    "LdsIndividualOrdinance",
    "LdsOrdinanceDetail",
    "LdsSpouseSealing",
    "Map",
    "Multimedia",
    "MultimediaLink",
    "NamePieces",
    "NameTranslation",
    "NonEvent",
    "PersonalName",
    "Place",
    "PlaceTranslation",
    "Record",
    "Repository",
    "Source",
    "SourceCitation",
    "SourceRepositoryCitation",
    "Submitter",
    "VoidPointer",
]
