"""Encoders for top-level records (§3.2.2)."""

from __future__ import annotations

from collections.abc import Iterator

from ..enums import Sex, enum_value
from ..lines import Line
from ..model import Family, Identifier, Individual, Submitter
from ._context import Context
from ._substructures import (
    address_lines,
    attribute_lines,
    contact_lines,
    event_lines,
    identifier_lines,
    non_event_lines,
    personal_name_lines,
)


def _identifier_lines(identifiers: list[Identifier], level: int) -> Iterator[Line]:
    for identifier in identifiers:
        yield from identifier_lines(identifier, level)


def submitter_lines(record: Submitter, ctx: Context) -> Iterator[Line]:
    yield Line(0, "SUBM", xref=ctx.table.of(record))
    yield Line(1, "NAME", record.name)
    if record.address is not None:
        yield from address_lines(record.address, 1)
    yield from contact_lines(1, record.phones, record.emails, record.faxes, record.web_pages)
    yield from _identifier_lines(record.identifiers, 1)


def individual_lines(record: Individual, ctx: Context) -> Iterator[Line]:
    yield Line(0, "INDI", xref=ctx.table.of(record))
    for name in record.names:
        yield from personal_name_lines(name, 1)
    if record.sex is not None:
        yield Line(1, "SEX", enum_value(record.sex, Sex))
    for attribute in record.attributes:
        yield from attribute_lines(attribute, 1)
    for event in record.events:
        yield from event_lines(event, 1)
    for non_event in record.non_events:
        yield from non_event_lines(non_event, 1)
    # Derived family memberships (ADR-0001).
    for family in ctx.families.child_families(record):
        yield Line(1, "FAMC", ctx.table.of(family), is_pointer=True)
    for family in ctx.families.spouse_families(record):
        yield Line(1, "FAMS", ctx.table.of(family), is_pointer=True)
    yield from _identifier_lines(record.identifiers, 1)


def family_lines(record: Family, ctx: Context) -> Iterator[Line]:
    yield Line(0, "FAM", xref=ctx.table.of(record))
    for attribute in record.attributes:
        yield from attribute_lines(attribute, 1)
    for event in record.events:
        yield from event_lines(event, 1)
    for non_event in record.non_events:
        yield from non_event_lines(non_event, 1)
    if record.husband is not None:
        yield Line(1, "HUSB", ctx.table.of(record.husband), is_pointer=True)
    if record.wife is not None:
        yield Line(1, "WIFE", ctx.table.of(record.wife), is_pointer=True)
    for child in record.children:
        yield Line(1, "CHIL", ctx.table.resolve(child), is_pointer=True)
    yield from _identifier_lines(record.identifiers, 1)
