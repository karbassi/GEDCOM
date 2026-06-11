"""gedcom7 — a GEDCOM 7.0.18 writer for Python.

Serializes a genealogical data model into the FamilySearch GEDCOM 7 text
format. See the issue tracker under ``.scratch/`` for the build plan.
"""

from __future__ import annotations

from .model import (
    VOID,
    Document,
    Family,
    Header,
    Individual,
    NamePieces,
    NameTranslation,
    PersonalName,
    Submitter,
)
from .validation import ValidationError, validate
from .writer import dump, dumps

__all__ = [
    "VOID",
    "Document",
    "Family",
    "Header",
    "Individual",
    "NamePieces",
    "NameTranslation",
    "PersonalName",
    "Submitter",
    "ValidationError",
    "__version__",
    "dump",
    "dumps",
    "validate",
]

__version__ = "0.0.0"
