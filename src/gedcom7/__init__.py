"""gedcom7 — a GEDCOM 7.0.18 writer for Python.

Serializes a genealogical data model into the FamilySearch GEDCOM 7 text
format. See the issue tracker under ``.scratch/`` for the build plan.
"""

from __future__ import annotations

from .model import Document, Header
from .writer import dump, dumps

__all__ = ["Document", "Header", "__version__", "dump", "dumps"]

__version__ = "0.0.0"
