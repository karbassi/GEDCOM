"""Public writer surface: serialize a Document to GEDCOM 7 text or bytes."""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import IO

from .lines import render
from .model import Document
from .serialize import serialize_document
from .validation import validate
from .xref import build_xref_table

_BOM = "﻿"


def dumps(document: Document, *, eol: str = "\n", strict: bool = True) -> str:
    """Serialize a document to a GEDCOM 7 string (no BOM).

    In strict mode (default) a document-level rule violation raises
    :class:`~gedcom.validation.ValidationError`. In lenient mode each issue
    is emitted as a warning and best-effort output is produced anyway.
    """
    for message in validate(document, strict=strict):
        warnings.warn(message, stacklevel=2)
    table = build_xref_table(document)
    return render(serialize_document(document, table), eol=eol)


def dump(
    document: Document,
    dest: str | os.PathLike[str] | IO[bytes],
    *,
    eol: str = "\n",
    strict: bool = True,
) -> None:
    """Write a document as a UTF-8 byte stream (with a leading BOM).

    ``dest`` may be a filesystem path or an open binary stream.
    """
    data = (_BOM + dumps(document, eol=eol, strict=strict)).encode("utf-8")
    if isinstance(dest, (str, os.PathLike)):
        Path(dest).write_bytes(data)
    else:
        dest.write(data)
