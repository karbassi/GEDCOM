"""Structure tree → :class:`~gedcom.model.Header` (inverse of
:func:`gedcom.serialize._header.header_lines`).
"""

from __future__ import annotations

from ..model import Header, HeaderSource
from ._resolve import Resolver
from ._tree import Node
from ._values import parse_date_exact, parse_text_list, parse_time


def parse_schema(head: Node) -> dict[str, str]:
    """Build the SCHMA extension map (tag/enum identifier → URI) from a HEAD."""
    schema: dict[str, str] = {}
    schma = head.child("SCHMA")
    if schma is not None:
        for tag_node in schma.all("TAG"):
            identifier, _, uri = (tag_node.value or "").partition(" ")
            schema[identifier] = uri
    return schema


def parse_header(node: Node, resolver: Resolver) -> Header:
    """Build a Header from a ``HEAD`` structure node (pointers resolved)."""
    header = Header(schema=dict(resolver.schema))

    gedc = node.child("GEDC")
    if gedc is not None:
        version = gedc.text("VERS")
        if version is not None:
            header.gedcom_version = version

    source = node.child("SOUR")
    if source is not None:
        header.source = HeaderSource(
            product=source.value or "",
            version=source.text("VERS"),
            name=source.text("NAME"),
            corporation=source.text("CORP"),
        )

    header.destination = node.text("DEST")

    date_node = node.child("DATE")
    if date_node is not None and date_node.value is not None:
        header.date = parse_date_exact(date_node.value, line=date_node.line.level)
        time = date_node.text("TIME")
        if time is not None:
            header.time = parse_time(time, line=date_node.line.level)

    submitter = node.text("SUBM")
    if submitter is not None:
        from ..model import Submitter

        header.submitter = resolver.record(submitter, Submitter)

    header.copyright = node.text("COPR")
    header.language = node.text("LANG")

    place = node.child("PLAC")
    if place is not None:
        form = place.text("FORM")
        header.place_form = parse_text_list(form) if form is not None else []

    note = node.child("NOTE")
    if note is not None:
        from ._substructures import parse_note

        header.note = parse_note(note)

    return header
