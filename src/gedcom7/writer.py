"""Public writer surface: serialize a Document to GEDCOM 7 text or bytes."""

from __future__ import annotations

import os
from pathlib import Path
from typing import IO

from .lines import render
from .model import Document
from .serialize import serialize_document
from .xref import build_xref_table

_BOM = "﻿"


def dumps(document: Document, *, eol: str = "\n") -> str:
    """Serialize a document to a GEDCOM 7 string (no BOM)."""
    table = build_xref_table(document)
    return render(serialize_document(document, table), eol=eol)


def dump(
    document: Document,
    dest: str | os.PathLike[str] | IO[bytes],
    *,
    eol: str = "\n",
) -> None:
    """Write a document as a UTF-8 byte stream (with a leading BOM).

    ``dest`` may be a filesystem path or an open binary stream.
    """
    data = (_BOM + dumps(document, eol=eol)).encode("utf-8")
    if isinstance(dest, (str, os.PathLike)):
        Path(dest).write_bytes(data)
    else:
        dest.write(data)
