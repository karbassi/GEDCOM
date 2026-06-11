"""Command-line tool: build GEDCOM 7 files from a declarative authoring document.

This subpackage is intentionally separate from the library core so importing
:mod:`gedcom7` never drags in argument parsing or the (optional) YAML reader.
The public entry point is :func:`main`.
"""

from __future__ import annotations

from .app import main
from .errors import LoadError
from .loader import build_document

__all__ = ["LoadError", "build_document", "main"]
