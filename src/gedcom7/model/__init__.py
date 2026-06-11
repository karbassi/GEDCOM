"""The genealogical model: records, the Document aggregate, and substructures.

Organized by the spec's own division — top-level records (§3.2.2) in
``_records`` and reusable substructure blocks (§3.2.3) in ``_substructures``,
with the aggregate and Record protocol in ``_document``. Value/datatype
objects live in :mod:`gedcom7.types`.
"""

from __future__ import annotations

from ._document import Document, Header, Record
from ._records import Individual, Submitter
from ._substructures import NamePieces, NameTranslation, PersonalName

__all__ = [
    "Document",
    "Header",
    "Individual",
    "NamePieces",
    "NameTranslation",
    "PersonalName",
    "Record",
    "Submitter",
]
