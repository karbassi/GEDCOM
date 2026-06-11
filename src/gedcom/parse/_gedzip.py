"""GEDZIP (`.gdz`) reading: the inverse of :mod:`gedcom.gedzip`.

Opens the archive, reads the ``gedcom.ged`` member, and parses it via the text
path. Even within the bounded "our own output" promise (ADR-0005) this is the
one place the reader touches archive-shaped bytes, so the unzip is guarded
against path-traversal and zip-bomb members.
"""

from __future__ import annotations

import os
import zipfile
from pathlib import Path, PurePosixPath

from ..model import Document
from .errors import ParseError

_GEDCOM_MEMBER = "gedcom.ged"
_MAX_TOTAL_BYTES = 1 << 30  # 1 GiB of decompressed content across the archive
_MAX_RATIO = 1000  # per-member decompressed:compressed ratio ceiling
_RATIO_FLOOR = 1 << 16  # only police the ratio once a member exceeds 64 KiB


def _guard(archive: zipfile.ZipFile) -> None:
    """Reject path-traversal and zip-bomb members before extracting anything."""
    total = 0
    for info in archive.infolist():
        pure = PurePosixPath(info.filename)
        if pure.is_absolute() or ".." in pure.parts:
            raise ParseError(f"unsafe archive member path: {info.filename!r}")
        total += info.file_size
        if total > _MAX_TOTAL_BYTES:
            raise ParseError("GEDZIP decompresses to too much data (possible zip bomb)")
        if (
            info.compress_size > 0
            and info.file_size > _RATIO_FLOOR
            and info.file_size / info.compress_size > _MAX_RATIO
        ):
            raise ParseError(
                f"member {info.filename!r} has a suspicious compression ratio (possible zip bomb)"
            )


def read_gedzip(path: str | os.PathLike[str]) -> Document:
    """Parse a GEDZIP (`.gdz`) archive's GEDCOM payload into a Document."""
    from . import read_text

    try:
        archive = zipfile.ZipFile(Path(path))
    except zipfile.BadZipFile as exc:
        raise ParseError(f"not a valid GEDZIP archive: {exc}") from None
    with archive:
        _guard(archive)
        try:
            data = archive.read(_GEDCOM_MEMBER)
        except KeyError:
            raise ParseError(f"GEDZIP archive has no {_GEDCOM_MEMBER!r} member") from None
        return read_text(data.decode("utf-8-sig"))
