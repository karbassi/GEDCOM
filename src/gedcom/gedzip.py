"""GEDZIP (`.gdz`) packaging: a ZIP holding the ``.ged`` plus its local media.

Per the GEDCOM 7 GEDZIP specification the GEDCOM data is stored as the archive
member ``gedcom.ged``; local files referenced by ``OBJE``/``FILE`` are packaged
alongside it at archive-relative paths so the references resolve inside the
container. Remote (URL) ``FILE`` payloads are left untouched and not packaged.
"""

from __future__ import annotations

import os
import re
import warnings
import zipfile
from dataclasses import replace
from pathlib import Path, PurePosixPath
from typing import IO

from .lines import Line, render
from .model import Document
from .serialize import serialize_document
from .validation import validate
from .writer import _BOM
from .xref import build_xref_table

_GEDCOM_MEMBER = "gedcom.ged"
_URL = re.compile(r"[A-Za-z][A-Za-z0-9+.\-]*://")


class GedzipError(ValueError):
    """Raised when a document cannot be packaged as a valid GEDZIP."""


def _is_local(value: str | None) -> bool:
    return bool(value) and _URL.match(value) is None  # type: ignore[arg-type]


def _path_line_indices(lines: list[Line]) -> list[int]:
    """Indices of lines whose value is a file path (``FILE``, or ``FILE.TRAN``)."""
    indices: list[int] = []
    stack: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        while stack and stack[-1][0] >= line.level:
            stack.pop()
        parent_tag = stack[-1][1] if stack else None
        if line.tag == "FILE" or (line.tag == "TRAN" and parent_tag == "FILE"):
            indices.append(i)
        stack.append((line.level, line.tag))
    return indices


def _member_for(path: str, taken: set[str]) -> str:
    """Archive-relative member name for a local file path."""
    pure = PurePosixPath(path.replace("\\", "/"))
    if not pure.is_absolute() and ".." not in pure.parts:
        member = pure.as_posix()
    else:
        member = f"media/{pure.name}"
    if member in taken:  # de-collide distinct sources mapping to the same name
        stem, _, suffix = member.rpartition(".")
        base, ext = (stem, f".{suffix}") if stem else (member, "")
        n = 1
        while f"{base}-{n}{ext}" in taken:
            n += 1
        member = f"{base}-{n}{ext}"
    taken.add(member)
    return member


def dump_gedzip(
    document: Document,
    dest: str | os.PathLike[str] | IO[bytes],
    *,
    eol: str = "\n",
    strict: bool = True,
) -> None:
    """Write a document as a GEDZIP (`.gdz`) archive.

    Local ``FILE`` payloads are packaged and rewritten to their archive-relative
    member paths; URL payloads are left as-is. A referenced local file that does
    not exist raises :class:`GedzipError`.
    """
    for message in validate(document, strict=strict):
        warnings.warn(message, stacklevel=2)

    lines = list(serialize_document(document, build_xref_table(document)))
    sources: dict[str, Path] = {}  # member name -> on-disk file
    taken: set[str] = set()
    for i in _path_line_indices(lines):
        value = lines[i].value
        if not _is_local(value):
            continue
        assert value is not None
        source = Path(value)
        if not source.is_file():
            raise GedzipError(f"referenced local file does not exist: {value}")
        member = _member_for(value, taken)
        sources[member] = source
        lines[i] = replace(lines[i], value=member)  # rewrite FILE to archive path

    ged_bytes = (_BOM + render(iter(lines), eol=eol)).encode("utf-8")

    handle = dest if hasattr(dest, "write") else Path(dest)
    with zipfile.ZipFile(handle, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(_GEDCOM_MEMBER, ged_bytes)
        for member in sorted(sources):
            archive.writestr(member, sources[member].read_bytes())
