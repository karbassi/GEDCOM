"""Model → ordered :class:`~gedcom.lines.Line` sequence.

``serialize_document`` walks the document in wire order. Record dispatch is
explicit (no magic registry): each record type maps to its encoder in
``_records``; substructure encoders live in ``_substructures``.
"""

from __future__ import annotations

from collections.abc import Iterator

from ..extensions import registered_extension_uris
from ..lines import Line
from ..model import (
    Document,
    ExtensionStructure,
    Family,
    Individual,
    Multimedia,
    Record,
    Repository,
    SharedNote,
    Source,
    Submitter,
)
from ..xref import XrefTable
from ._context import Context
from ._header import header_lines
from ._links import build_family_index
from ._records import (
    family_lines,
    individual_lines,
    meta_lines,
    multimedia_lines,
    repository_lines,
    shared_note_lines,
    source_lines,
    submitter_lines,
)
from ._substructures import extension_structure_lines


def _typed_record_lines(record: Record, ctx: Context) -> Iterator[Line]:
    if isinstance(record, Submitter):
        yield from submitter_lines(record, ctx)
    elif isinstance(record, Individual):
        yield from individual_lines(record, ctx)
    elif isinstance(record, Family):
        yield from family_lines(record, ctx)
    elif isinstance(record, Source):
        yield from source_lines(record, ctx)
    elif isinstance(record, Repository):
        yield from repository_lines(record, ctx)
    elif isinstance(record, Multimedia):
        yield from multimedia_lines(record, ctx)
    elif isinstance(record, SharedNote):
        yield from shared_note_lines(record, ctx)
    else:
        raise TypeError(f"no serializer for record type {type(record).__name__}")


def _record_lines(record: Record, ctx: Context) -> Iterator[Line]:
    yield from _typed_record_lines(record, ctx)
    for ext in record.extensions:
        yield from extension_structure_lines(ext, 1)
    # CHANGE_DATE/CREATION_DATE come last for every record.
    yield from meta_lines(record.change_date, record.creation_date, ctx)


def _extension_schema(records: list[Record]) -> dict[str, str]:
    """Collect each used extension structure's tag -> declared SCHMA URI."""
    declared: dict[str, str] = {}

    def walk(extensions: list[ExtensionStructure]) -> None:
        for ext in extensions:
            declared.setdefault(ext.tag, ext.schema_uri)
            walk(list(ext.children))

    for record in records:
        walk(record.extensions)
    return declared


def _used_schema_entries(body: list[Line], schema: dict[str, str]) -> list[tuple[str, str]]:
    """Find declared extension identifiers actually used, sorted for stability."""
    used: set[str] = set()
    for line in body:
        if line.tag in schema:
            used.add(line.tag)
        if line.value is not None and line.value in schema:
            used.add(line.value)
    return [(identifier, schema[identifier]) for identifier in sorted(used)]


def serialize_document(document: Document, table: XrefTable) -> Iterator[Line]:
    """Yield the logical lines for a whole document, in document order."""
    ctx = Context(table=table, families=build_family_index(document))
    body = [line for record in document.records for line in _record_lines(record, ctx)]
    # Extension structures declare their URIs (registered default or a
    # user-supplied uri); an explicit header.schema entry overrides them.
    declared = {
        **registered_extension_uris(),
        **_extension_schema(document.records),
        **document.header.schema,
    }
    schema_entries = _used_schema_entries(body, declared)
    yield from header_lines(document.header, ctx, schema_entries)
    yield from body
    yield Line(0, "TRLR")


__all__ = ["serialize_document"]
