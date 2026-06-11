"""Encoders for top-level records (§3.2.2)."""

from __future__ import annotations

from collections.abc import Iterator

from ..enums import Sex, enum_value
from ..lines import Line
from ..model import Individual, Submitter
from ..xref import XrefTable
from ._substructures import contact_lines, personal_name_lines


def submitter_lines(record: Submitter, table: XrefTable) -> Iterator[Line]:
    yield Line(0, "SUBM", xref=table.of(record))
    yield Line(1, "NAME", record.name)
    yield from contact_lines(1, record.phones, record.emails, record.faxes, record.web_pages)


def individual_lines(record: Individual, table: XrefTable) -> Iterator[Line]:
    yield Line(0, "INDI", xref=table.of(record))
    for name in record.names:
        yield from personal_name_lines(name, 1)
    if record.sex is not None:
        yield Line(1, "SEX", enum_value(record.sex, Sex))
