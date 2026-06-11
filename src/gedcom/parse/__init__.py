"""Reader: GEDCOM 7 text → model, the structural inverse of ``serialize``.

Strict and scoped to round-tripping this library's own output (ADR-0005).
``read_text`` is the public entry point; ``read_path`` (text vs GEDZIP) lands
in a later slice.
"""

from __future__ import annotations

import os
from pathlib import Path

from ..model import Document
from ._records import build_document
from ._tokenize import tokenize
from ._tree import build_tree
from .errors import ParseError

__all__ = ["ParseError", "read_path", "read_text"]


def read_text(text: str) -> Document:
    """Parse GEDCOM 7 text into a :class:`~gedcom.model.Document`."""
    return build_document(build_tree(tokenize(text)))


def read_path(path: str | os.PathLike[str]) -> Document:
    """Read a `.ged` file or `.gdz` GEDZIP archive into a Document.

    Dispatches on the file extension, mirroring ``dump``/``dump_gedzip``: a
    ``.gdz`` suffix reads the GEDZIP package, anything else is read as UTF-8
    text (a leading BOM is tolerated).
    """
    p = Path(path)
    if p.suffix.lower() == ".gdz":
        from ._gedzip import read_gedzip

        return read_gedzip(p)
    return read_text(p.read_text(encoding="utf-8-sig"))
