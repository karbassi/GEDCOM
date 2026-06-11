"""gedcom7 — a GEDCOM 7.0.18 writer for Python.

Serializes a genealogical data model into the FamilySearch GEDCOM 7 text
format. See the issue tracker under ``.scratch/`` for the build plan.
"""

from __future__ import annotations

from .model import (
    VOID,
    Address,
    Attribute,
    Document,
    Event,
    EventDetail,
    Family,
    Header,
    Identifier,
    Individual,
    LdsIndividualOrdinance,
    LdsOrdinanceDetail,
    LdsSpouseSealing,
    Map,
    NamePieces,
    NameTranslation,
    NonEvent,
    PersonalName,
    Place,
    PlaceTranslation,
    Submitter,
)
from .validation import ValidationError, validate
from .writer import dump, dumps

__all__ = [
    "VOID",
    "Address",
    "Attribute",
    "Document",
    "Event",
    "EventDetail",
    "Family",
    "Header",
    "Identifier",
    "Individual",
    "LdsIndividualOrdinance",
    "LdsOrdinanceDetail",
    "LdsSpouseSealing",
    "Map",
    "NamePieces",
    "NameTranslation",
    "NonEvent",
    "PersonalName",
    "Place",
    "PlaceTranslation",
    "Submitter",
    "ValidationError",
    "__version__",
    "dump",
    "dumps",
    "validate",
]

__version__ = "0.0.0"
