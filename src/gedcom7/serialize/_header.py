"""Encoder for the document header (`HEAD`)."""

from __future__ import annotations

from collections.abc import Iterator

from ..lines import Line
from ..model import Header
from ..types import text_list
from ._context import Context


def header_lines(
    header: Header, ctx: Context, schema_entries: list[tuple[str, str]]
) -> Iterator[Line]:
    yield Line(0, "HEAD")
    yield Line(1, "GEDC")
    yield Line(2, "VERS", header.gedcom_version)
    if schema_entries:
        yield Line(1, "SCHMA")
        for tag, uri in schema_entries:
            yield Line(2, "TAG", f"{tag} {uri}")
    if header.date is not None:
        yield Line(1, "DATE", header.date.gedcom())
        if header.time is not None:
            yield Line(2, "TIME", header.time.gedcom())
    if header.submitter is not None:
        yield Line(1, "SUBM", ctx.table.of(header.submitter), is_pointer=True)
    if header.place_form is not None:
        yield Line(1, "PLAC")
        yield Line(2, "FORM", text_list(header.place_form))
    if header.copyright is not None:
        yield Line(1, "COPR", header.copyright)
