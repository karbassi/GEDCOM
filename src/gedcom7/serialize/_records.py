"""Encoders for top-level records (§3.2.2)."""

from __future__ import annotations

from collections.abc import Iterator

from ..enums import Medium, Quality, Sex, enum_value
from ..lines import Line
from ..model import (
    Family,
    Identifier,
    Individual,
    LdsIndividualOrdinance,
    LdsSpouseSealing,
    Multimedia,
    MultimediaLink,
    Repository,
    Source,
    SourceCitation,
    SourceRepositoryCitation,
    Submitter,
)
from ._context import Context
from ._substructures import (
    address_lines,
    attribute_lines,
    contact_lines,
    crop_lines,
    event_lines,
    file_lines,
    identifier_lines,
    non_event_lines,
    ordinance_detail_lines,
    personal_name_lines,
)


def _identifier_lines(identifiers: list[Identifier], level: int) -> Iterator[Line]:
    for identifier in identifiers:
        yield from identifier_lines(identifier, level)


def _ordinance_lines(ordinance: LdsIndividualOrdinance, ctx: Context, level: int) -> Iterator[Line]:
    yield Line(level, ordinance.tag)
    if ordinance.detail is not None:
        yield from ordinance_detail_lines(ordinance.detail, level + 1)
    if ordinance.family is not None:
        yield Line(level + 1, "FAMC", ctx.table.of(ordinance.family), is_pointer=True)


def _sealing_lines(sealing: LdsSpouseSealing, level: int) -> Iterator[Line]:
    yield Line(level, "SLGS")
    if sealing.detail is not None:
        yield from ordinance_detail_lines(sealing.detail, level + 1)


def source_citation_lines(citation: SourceCitation, ctx: Context, level: int) -> Iterator[Line]:
    yield Line(level, "SOUR", ctx.table.resolve(citation.source), is_pointer=True)
    if citation.page is not None:
        yield Line(level + 1, "PAGE", citation.page)
    if citation.quality is not None:
        yield Line(level + 1, "QUAY", enum_value(citation.quality, Quality))


def _source_citations(citations: list[SourceCitation], ctx: Context, level: int) -> Iterator[Line]:
    for citation in citations:
        yield from source_citation_lines(citation, ctx, level)


def multimedia_link_lines(link: MultimediaLink, ctx: Context, level: int) -> Iterator[Line]:
    yield Line(level, "OBJE", ctx.table.resolve(link.multimedia), is_pointer=True)
    if link.crop is not None:
        yield from crop_lines(link.crop, level + 1)
    if link.title is not None:
        yield Line(level + 1, "TITL", link.title)


def _media_links(links: list[MultimediaLink], ctx: Context, level: int) -> Iterator[Line]:
    for link in links:
        yield from multimedia_link_lines(link, ctx, level)


def multimedia_lines(record: Multimedia, ctx: Context) -> Iterator[Line]:
    yield Line(0, "OBJE", xref=ctx.table.of(record))
    for file in record.files:
        yield from file_lines(file, 1)
    yield from _identifier_lines(record.identifiers, 1)


def _repository_citation_lines(
    citation: SourceRepositoryCitation, ctx: Context, level: int
) -> Iterator[Line]:
    yield Line(level, "REPO", ctx.table.of(citation.repository), is_pointer=True)
    for call_number in citation.call_numbers:
        yield Line(level + 1, "CALN", call_number.value)
        if call_number.medium is not None:
            yield Line(level + 2, "MEDI", enum_value(call_number.medium, Medium))


def source_lines(record: Source, ctx: Context) -> Iterator[Line]:
    yield Line(0, "SOUR", xref=ctx.table.of(record))
    if record.author is not None:
        yield Line(1, "AUTH", record.author)
    if record.title is not None:
        yield Line(1, "TITL", record.title)
    if record.abbreviation is not None:
        yield Line(1, "ABBR", record.abbreviation)
    if record.publication is not None:
        yield Line(1, "PUBL", record.publication)
    if record.text is not None:
        yield Line(1, "TEXT", record.text)
    for repository_citation in record.repository_citations:
        yield from _repository_citation_lines(repository_citation, ctx, 1)
    yield from _identifier_lines(record.identifiers, 1)


def repository_lines(record: Repository, ctx: Context) -> Iterator[Line]:
    yield Line(0, "REPO", xref=ctx.table.of(record))
    yield Line(1, "NAME", record.name)
    if record.address is not None:
        yield from address_lines(record.address, 1)
    yield from contact_lines(1, record.phones, record.emails, record.faxes, record.web_pages)
    yield from _identifier_lines(record.identifiers, 1)


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
    for ordinance in record.lds_ordinances:
        yield from _ordinance_lines(ordinance, ctx, 1)
    # Derived family memberships (ADR-0001).
    for family in ctx.families.child_families(record):
        yield Line(1, "FAMC", ctx.table.of(family), is_pointer=True)
    for family in ctx.families.spouse_families(record):
        yield Line(1, "FAMS", ctx.table.of(family), is_pointer=True)
    yield from _identifier_lines(record.identifiers, 1)
    yield from _source_citations(record.source_citations, ctx, 1)
    yield from _media_links(record.media_links, ctx, 1)


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
    for sealing in record.sealings:
        yield from _sealing_lines(sealing, 1)
    yield from _identifier_lines(record.identifiers, 1)
    yield from _source_citations(record.source_citations, ctx, 1)
    yield from _media_links(record.media_links, ctx, 1)
