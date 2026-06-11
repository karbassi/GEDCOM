"""Encoder for the document header (`HEAD`)."""

from __future__ import annotations

from collections.abc import Iterator

from ..lines import Line
from ..model import Header
from ..xref import XrefTable


def header_lines(header: Header, table: XrefTable) -> Iterator[Line]:
    yield Line(0, "HEAD")
    yield Line(1, "GEDC")
    yield Line(2, "VERS", header.gedcom_version)
    if header.date is not None:
        yield Line(1, "DATE", header.date.gedcom())
        if header.time is not None:
            yield Line(2, "TIME", header.time.gedcom())
    if header.submitter is not None:
        yield Line(1, "SUBM", table.of(header.submitter), is_pointer=True)
    if header.copyright is not None:
        yield Line(1, "COPR", header.copyright)
