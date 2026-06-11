"""Encoders for top-level records (§3.2.2)."""

from __future__ import annotations

from collections.abc import Iterator

from ..enums import Medium, Quality, Restriction, Role, Sex, enum_list, enum_value
from ..lines import Line
from ..model import (
    Association,
    ChangeDate,
    CreationDate,
    Family,
    Identifier,
    Individual,
    LdsIndividualOrdinance,
    LdsSpouseSealing,
    Multimedia,
    MultimediaLink,
    Note,
    Repository,
    SharedNote,
    Source,
    SourceCitation,
    SourceData,
    SourceRepositoryCitation,
    Submitter,
)
from ..types import date_value_gedcom, text_list
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
    note_lines,
    note_translation_lines,
    ordinance_detail_lines,
    personal_name_lines,
    place_lines,
)


def _identifier_lines(identifiers: list[Identifier], level: int) -> Iterator[Line]:
    for identifier in identifiers:
        yield from identifier_lines(identifier, level)


def _note_lines(notes: list[Note | SharedNote], ctx: Context, level: int) -> Iterator[Line]:
    for note in notes:
        if isinstance(note, SharedNote):
            yield Line(level, "SNOTE", ctx.table.of(note), is_pointer=True)
        else:
            yield from note_lines(note, level)


def _restriction_lines(restrictions: list[Restriction | str], level: int) -> Iterator[Line]:
    if restrictions:
        yield Line(level, "RESN", enum_list(restrictions, Restriction))


def association_lines(assoc: Association, ctx: Context, level: int) -> Iterator[Line]:
    yield Line(level, "ASSO", ctx.table.resolve(assoc.person), is_pointer=True)
    if assoc.phrase is not None:
        yield Line(level + 1, "PHRASE", assoc.phrase)
    yield Line(level + 1, "ROLE", enum_value(assoc.role, Role))
    if assoc.role_phrase is not None:
        yield Line(level + 2, "PHRASE", assoc.role_phrase)
    yield from _note_lines(assoc.notes, ctx, level + 1)
    yield from _source_citations(assoc.source_citations, ctx, level + 1)


def _associations(assocs: list[Association], ctx: Context, level: int) -> Iterator[Line]:
    for assoc in assocs:
        yield from association_lines(assoc, ctx, level)


def meta_lines(
    change_date: ChangeDate | None, creation_date: CreationDate | None, ctx: Context
) -> Iterator[Line]:
    if change_date is not None:
        yield Line(1, "CHAN")
        yield Line(2, "DATE", change_date.date.gedcom())
        if change_date.time is not None:
            yield Line(3, "TIME", change_date.time.gedcom())
        yield from _note_lines(change_date.notes, ctx, 2)
    if creation_date is not None:
        yield Line(1, "CREA")
        yield Line(2, "DATE", creation_date.date.gedcom())
        if creation_date.time is not None:
            yield Line(3, "TIME", creation_date.time.gedcom())


def shared_note_lines(record: SharedNote, ctx: Context) -> Iterator[Line]:
    yield Line(0, "SNOTE", record.text, xref=ctx.table.of(record))
    if record.mime is not None:
        yield Line(1, "MIME", record.mime)
    if record.language is not None:
        yield Line(1, "LANG", record.language)
    for tran in record.translations:
        yield from note_translation_lines(tran, 1)
    yield from _source_citations(record.source_citations, ctx, 1)
    yield from _identifier_lines(record.identifiers, 1)


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
    if citation.data_date is not None or citation.data_texts:
        yield Line(level + 1, "DATA")
        if citation.data_date is not None:
            yield Line(level + 2, "DATE", date_value_gedcom(citation.data_date))
        for text in citation.data_texts:
            yield Line(level + 2, "TEXT", text)
    if citation.event is not None:
        yield Line(level + 1, "EVEN", citation.event)
        if citation.event_phrase is not None:
            yield Line(level + 2, "PHRASE", citation.event_phrase)
        if citation.role is not None:
            yield Line(level + 2, "ROLE", enum_value(citation.role, Role))
            if citation.role_phrase is not None:
                yield Line(level + 3, "PHRASE", citation.role_phrase)
    if citation.quality is not None:
        yield Line(level + 1, "QUAY", enum_value(citation.quality, Quality))
    yield from _media_links(citation.media_links, ctx, level + 1)
    yield from _note_lines(citation.notes, ctx, level + 1)


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
    yield from _restriction_lines(record.restrictions, 1)
    for file in record.files:
        yield from file_lines(file, 1)
    yield from _note_lines(record.notes, ctx, 1)
    yield from _source_citations(record.source_citations, ctx, 1)
    yield from _identifier_lines(record.identifiers, 1)


def _repository_citation_lines(
    citation: SourceRepositoryCitation, ctx: Context, level: int
) -> Iterator[Line]:
    yield Line(level, "REPO", ctx.table.of(citation.repository), is_pointer=True)
    for call_number in citation.call_numbers:
        yield Line(level + 1, "CALN", call_number.value)
        if call_number.medium is not None:
            yield Line(level + 2, "MEDI", enum_value(call_number.medium, Medium))


def source_data_lines(data: SourceData, ctx: Context, level: int) -> Iterator[Line]:
    yield Line(level, "DATA")
    for source_event in data.events:
        yield Line(level + 1, "EVEN", text_list(source_event.events))
        if source_event.date is not None:
            yield Line(level + 2, "DATE", source_event.date.gedcom())
            if source_event.date_phrase is not None:
                yield Line(level + 3, "PHRASE", source_event.date_phrase)
        if source_event.place is not None:
            yield from place_lines(source_event.place, level + 2)
    if data.agency is not None:
        yield Line(level + 1, "AGNC", data.agency)
    yield from _note_lines(data.notes, ctx, level + 1)


def source_lines(record: Source, ctx: Context) -> Iterator[Line]:
    yield Line(0, "SOUR", xref=ctx.table.of(record))
    if record.data is not None:
        yield from source_data_lines(record.data, ctx, 1)
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
        if record.text_mime is not None:
            yield Line(2, "MIME", record.text_mime)
        if record.text_language is not None:
            yield Line(2, "LANG", record.text_language)
    for repository_citation in record.repository_citations:
        yield from _repository_citation_lines(repository_citation, ctx, 1)
    yield from _identifier_lines(record.identifiers, 1)
    yield from _note_lines(record.notes, ctx, 1)
    yield from _media_links(record.media_links, ctx, 1)


def repository_lines(record: Repository, ctx: Context) -> Iterator[Line]:
    yield Line(0, "REPO", xref=ctx.table.of(record))
    yield Line(1, "NAME", record.name)
    if record.address is not None:
        yield from address_lines(record.address, 1)
    yield from contact_lines(1, record.phones, record.emails, record.faxes, record.web_pages)
    yield from _note_lines(record.notes, ctx, 1)
    yield from _identifier_lines(record.identifiers, 1)


def submitter_lines(record: Submitter, ctx: Context) -> Iterator[Line]:
    yield Line(0, "SUBM", xref=ctx.table.of(record))
    yield Line(1, "NAME", record.name)
    if record.address is not None:
        yield from address_lines(record.address, 1)
    yield from contact_lines(1, record.phones, record.emails, record.faxes, record.web_pages)
    yield from _media_links(record.media_links, ctx, 1)
    yield from _note_lines(record.notes, ctx, 1)
    yield from _identifier_lines(record.identifiers, 1)


def individual_lines(record: Individual, ctx: Context) -> Iterator[Line]:
    yield Line(0, "INDI", xref=ctx.table.of(record))
    yield from _restriction_lines(record.restrictions, 1)
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
    yield from _associations(record.associations, ctx, 1)
    yield from _note_lines(record.notes, ctx, 1)
    yield from _identifier_lines(record.identifiers, 1)
    yield from _source_citations(record.source_citations, ctx, 1)
    yield from _media_links(record.media_links, ctx, 1)


def family_lines(record: Family, ctx: Context) -> Iterator[Line]:
    yield Line(0, "FAM", xref=ctx.table.of(record))
    yield from _restriction_lines(record.restrictions, 1)
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
    yield from _associations(record.associations, ctx, 1)
    yield from _note_lines(record.notes, ctx, 1)
    yield from _identifier_lines(record.identifiers, 1)
    yield from _source_citations(record.source_citations, ctx, 1)
    yield from _media_links(record.media_links, ctx, 1)
