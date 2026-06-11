"""Reader: GEDCOM 7 text → model, the structural inverse of ``serialize``.

Strict and scoped to round-tripping this library's own output (ADR-0005).
``read_text`` is the public entry point; ``read_path`` (text vs GEDZIP) lands
in a later slice.
"""

from __future__ import annotations

from ..model import Document
from ._records import build_document
from ._tokenize import tokenize
from ._tree import build_tree
from .errors import ParseError

__all__ = ["ParseError", "read_text"]


def read_text(text: str) -> Document:
    """Parse GEDCOM 7 text into a :class:`~gedcom.model.Document`."""
    return build_document(build_tree(tokenize(text)))
