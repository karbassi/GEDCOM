"""Structure forest → :class:`~gedcom.model.Document` (inverse of
:mod:`gedcom.serialize._records` and :mod:`gedcom.serialize.__init__`).

Two passes resolve the object graph (ADR-0001): the first builds every level-0
record shell and registers it by wire id; the second populates each record,
resolving pointer payloads to objects. A final pass lifts ``INDI.FAMC``
membership detail onto the owning family's child entries (ADR-0004).
"""

from __future__ import annotations

from ..enums import FamcStatus, Pedigree, Quality, Restriction, Role, Sex
from ..model import (
    Alias,
    Association,
    CallNumber,
    ChangeDate,
    ChildLink,
    CreationDate,
    Document,
    Family,
    Identifier,
    Individual,
    LdsIndividualOrdinance,
    LdsSpouseSealing,
    Multimedia,
    MultimediaLink,
    Note,
    Record,
    Repository,
    SharedNote,
    Source,
    SourceCitation,
    SourceData,
    SourceDataEvent,
    SourceRepositoryCitation,
    Submitter,
)
from ._header import parse_header, parse_schema
from ._resolve import Resolver
from ._substructures import (
    ATTRIBUTE_TAGS,
    EVENT_TAGS,
    parse_attribute,
    parse_crop,
    parse_event,
    parse_extension_structure,
    parse_file,
    parse_identifier,
    parse_non_event,
    parse_note,
    parse_note_translation,
    parse_ordinance_detail,
    parse_personal_name,
    parse_place,
)
from ._tree import Node
from ._values import (
    parse_date_exact,
    parse_date_period,
    parse_date_value,
    parse_enum,
    parse_enum_list,
    parse_text_list,
    parse_time,
)
from .errors import ParseError

_INDI_ORDINANCE_TAGS = frozenset({"BAPL", "CONL", "ENDL", "INIL", "SLGC"})
_IDENTIFIER_TAGS = frozenset({"REFN", "UID", "EXID"})


def _need(value: str | None, tag: str, node: Node) -> str:
    if value is None:
        raise ParseError(f"{tag} requires a value", line=node.line.level, tag=tag)
    return value


# --- shared blocks ----------------------------------------------------------


def _notes(node: Node, resolver: Resolver) -> list[Note | SharedNote]:
    out: list[Note | SharedNote] = []
    for child in node.children:
        if child.tag == "NOTE":
            out.append(parse_note(child))
        elif child.tag == "SNOTE":
            out.append(resolver.record(_need(child.value, "SNOTE", child), SharedNote))
    return out


def _restrictions(node: Node) -> list[Restriction | str]:
    resn = node.text("RESN")
    return parse_enum_list(resn, Restriction) if resn is not None else []


def _identifiers(node: Node) -> list[Identifier]:
    return [parse_identifier(c) for c in node.children if c.tag in _IDENTIFIER_TAGS]


def _source_citations(node: Node, resolver: Resolver) -> list[SourceCitation]:
    return [parse_source_citation(c, resolver) for c in node.all("SOUR")]


def _media_links(node: Node, resolver: Resolver) -> list[MultimediaLink]:
    return [parse_multimedia_link(c, resolver) for c in node.all("OBJE")]


def _contacts(node: Node) -> tuple[list[str], list[str], list[str], list[str]]:
    return (
        [c.value or "" for c in node.all("PHON")],
        [c.value or "" for c in node.all("EMAIL")],
        [c.value or "" for c in node.all("FAX")],
        [c.value or "" for c in node.all("WWW")],
    )


def parse_source_citation(node: Node, resolver: Resolver) -> SourceCitation:
    citation = SourceCitation(source=resolver.pointer(_need(node.value, "SOUR", node), Source))
    citation.page = node.text("PAGE")
    data = node.child("DATA")
    if data is not None:
        date_node = data.child("DATE")
        if date_node is not None and date_node.value is not None:
            citation.data_date = parse_date_value(date_node.value, line=date_node.line.level)
        citation.data_texts = [c.value or "" for c in data.all("TEXT")]
    even = node.child("EVEN")
    if even is not None:
        citation.event = even.value
        citation.event_phrase = even.text("PHRASE")
        role = even.child("ROLE")
        if role is not None and role.value is not None:
            citation.role = parse_enum(role.value, Role)
            citation.role_phrase = role.text("PHRASE")
    quay = node.text("QUAY")
    if quay is not None:
        citation.quality = parse_enum(quay, Quality)
    citation.media_links = _media_links(node, resolver)
    citation.notes = _notes(node, resolver)
    return citation


def parse_multimedia_link(node: Node, resolver: Resolver) -> MultimediaLink:
    link = MultimediaLink(multimedia=resolver.pointer(_need(node.value, "OBJE", node), Multimedia))
    crop = node.child("CROP")
    if crop is not None:
        link.crop = parse_crop(crop)
    link.title = node.text("TITL")
    return link


def parse_association(node: Node, resolver: Resolver) -> Association:
    role_node = node.child("ROLE")
    if role_node is None or role_node.value is None:
        raise ParseError("ASSO requires a ROLE", line=node.line.level, tag="ASSO")
    assoc = Association(
        person=resolver.pointer(_need(node.value, "ASSO", node), Individual),
        role=parse_enum(role_node.value, Role),
    )
    assoc.phrase = node.text("PHRASE")
    assoc.role_phrase = role_node.text("PHRASE")
    assoc.notes = _notes(node, resolver)
    assoc.source_citations = _source_citations(node, resolver)
    return assoc


def parse_repository_citation(node: Node, resolver: Resolver) -> SourceRepositoryCitation:
    citation = SourceRepositoryCitation(
        repository=resolver.record(_need(node.value, "REPO", node), Repository)
    )
    for caln in node.all("CALN"):
        call_number = CallNumber(value=caln.value or "")
        medium = caln.text("MEDI")
        if medium is not None:
            from ..enums import Medium

            call_number.medium = parse_enum(medium, Medium)
        citation.call_numbers.append(call_number)
    return citation


def parse_source_data(node: Node, resolver: Resolver) -> SourceData:
    data = SourceData()
    for even in node.all("EVEN"):
        source_event = SourceDataEvent(events=parse_text_list(even.value or ""))
        date_node = even.child("DATE")
        if date_node is not None and date_node.value is not None:
            source_event.date = parse_date_period(date_node.value, line=date_node.line.level)
            source_event.date_phrase = date_node.text("PHRASE")
        place = even.child("PLAC")
        if place is not None:
            source_event.place = parse_place(place)
        data.events.append(source_event)
    data.agency = node.text("AGNC")
    data.notes = _notes(node, resolver)
    return data


def _change_date(node: Node, resolver: Resolver) -> ChangeDate | None:
    chan = node.child("CHAN")
    if chan is None:
        return None
    date_node = chan.child("DATE")
    if date_node is None or date_node.value is None:
        raise ParseError("CHAN requires a DATE", line=chan.line.level, tag="CHAN")
    change = ChangeDate(date=parse_date_exact(date_node.value, line=date_node.line.level))
    time = date_node.text("TIME")
    if time is not None:
        change.time = parse_time(time, line=date_node.line.level)
    change.notes = _notes(chan, resolver)
    return change


def _creation_date(node: Node) -> CreationDate | None:
    crea = node.child("CREA")
    if crea is None:
        return None
    date_node = crea.child("DATE")
    if date_node is None or date_node.value is None:
        raise ParseError("CREA requires a DATE", line=crea.line.level, tag="CREA")
    creation = CreationDate(date=parse_date_exact(date_node.value, line=date_node.line.level))
    time = date_node.text("TIME")
    if time is not None:
        creation.time = parse_time(time, line=date_node.line.level)
    return creation


# --- record shells (pass 1) -------------------------------------------------


def _make_record(node: Node) -> Record:
    xref = node.line.xref
    xref_id = xref[1:-1] if xref is not None else None
    tag = node.tag
    if tag == "INDI":
        return Individual(xref_id=xref_id)
    if tag == "FAM":
        return Family(xref_id=xref_id)
    if tag == "OBJE":
        return Multimedia(xref_id=xref_id)
    if tag == "SOUR":
        return Source(xref_id=xref_id)
    if tag == "REPO":
        return Repository(name=node.text("NAME") or "", xref_id=xref_id)
    if tag == "SNOTE":
        return SharedNote(text=node.value or "", xref_id=xref_id)
    if tag == "SUBM":
        return Submitter(name=node.text("NAME") or "", xref_id=xref_id)
    raise ParseError(f"unsupported top-level record: {tag}", tag=tag, line=node.line.level)


# --- record population (pass 2) ---------------------------------------------


def _ordinance(node: Node, resolver: Resolver) -> LdsIndividualOrdinance:
    ordinance = LdsIndividualOrdinance(tag=node.tag, detail=parse_ordinance_detail(node))
    famc = node.child("FAMC")
    if famc is not None and famc.value is not None:
        ordinance.family = resolver.record(famc.value, Family)
    return ordinance


def _populate_individual(record: Individual, node: Node, resolver: Resolver) -> None:
    record.restrictions = _restrictions(node)
    record.names = [parse_personal_name(c) for c in node.all("NAME")]
    sex = node.text("SEX")
    if sex is not None:
        record.sex = parse_enum(sex, Sex)
    record.attributes = [
        parse_attribute(c, resolver) for c in node.children if c.tag in ATTRIBUTE_TAGS
    ]
    record.events = [parse_event(c, resolver) for c in node.children if c.tag in EVENT_TAGS]
    record.non_events = [parse_non_event(c) for c in node.all("NO")]
    record.lds_ordinances = [
        _ordinance(c, resolver) for c in node.children if c.tag in _INDI_ORDINANCE_TAGS
    ]
    # FAMC/FAMS are derived from FAM records (ADR-0001); not stored on the
    # individual. Per-child FAMC detail is lifted onto the family in pass 3.
    record.associations = [parse_association(c, resolver) for c in node.all("ASSO")]
    record.submitters = [
        resolver.record(_need(c.value, "SUBM", c), Submitter) for c in node.all("SUBM")
    ]
    record.aliases = [
        Alias(
            individual=resolver.record(_need(c.value, "ALIA", c), Individual),
            phrase=c.text("PHRASE"),
        )
        for c in node.all("ALIA")
    ]
    record.ancestor_interest = [
        resolver.record(_need(c.value, "ANCI", c), Submitter) for c in node.all("ANCI")
    ]
    record.descendant_interest = [
        resolver.record(_need(c.value, "DESI", c), Submitter) for c in node.all("DESI")
    ]
    record.notes = _notes(node, resolver)
    record.identifiers = _identifiers(node)
    record.source_citations = _source_citations(node, resolver)
    record.media_links = _media_links(node, resolver)


def _populate_family(record: Family, node: Node, resolver: Resolver) -> None:
    record.restrictions = _restrictions(node)
    record.attributes = [
        parse_attribute(c, resolver) for c in node.children if c.tag in ATTRIBUTE_TAGS
    ]
    record.events = [parse_event(c, resolver) for c in node.children if c.tag in EVENT_TAGS]
    record.non_events = [parse_non_event(c) for c in node.all("NO")]
    husband = node.text("HUSB")
    if husband is not None:
        record.husband = resolver.record(husband, Individual)
    wife = node.text("WIFE")
    if wife is not None:
        record.wife = resolver.record(wife, Individual)
    record.children = [
        resolver.pointer(_need(c.value, "CHIL", c), Individual) for c in node.all("CHIL")
    ]
    record.sealings = [LdsSpouseSealing(detail=parse_ordinance_detail(c)) for c in node.all("SLGS")]
    record.associations = [parse_association(c, resolver) for c in node.all("ASSO")]
    record.submitters = [
        resolver.record(_need(c.value, "SUBM", c), Submitter) for c in node.all("SUBM")
    ]
    record.notes = _notes(node, resolver)
    record.identifiers = _identifiers(node)
    record.source_citations = _source_citations(node, resolver)
    record.media_links = _media_links(node, resolver)


def _populate_multimedia(record: Multimedia, node: Node, resolver: Resolver) -> None:
    record.restrictions = _restrictions(node)
    record.files = [parse_file(c) for c in node.all("FILE")]
    record.notes = _notes(node, resolver)
    record.source_citations = _source_citations(node, resolver)
    record.identifiers = _identifiers(node)


def _populate_source(record: Source, node: Node, resolver: Resolver) -> None:
    data = node.child("DATA")
    if data is not None:
        record.data = parse_source_data(data, resolver)
    record.author = node.text("AUTH")
    record.title = node.text("TITL")
    record.abbreviation = node.text("ABBR")
    record.publication = node.text("PUBL")
    text_node = node.child("TEXT")
    if text_node is not None:
        record.text = text_node.value
        record.text_mime = text_node.text("MIME")
        record.text_language = text_node.text("LANG")
    record.repository_citations = [parse_repository_citation(c, resolver) for c in node.all("REPO")]
    record.identifiers = _identifiers(node)
    record.notes = _notes(node, resolver)
    record.media_links = _media_links(node, resolver)


def _populate_repository(record: Repository, node: Node, resolver: Resolver) -> None:
    address = node.child("ADDR")
    if address is not None:
        from ._substructures import parse_address

        record.address = parse_address(address)
    record.phones, record.emails, record.faxes, record.web_pages = _contacts(node)
    record.notes = _notes(node, resolver)
    record.identifiers = _identifiers(node)


def _populate_submitter(record: Submitter, node: Node, resolver: Resolver) -> None:
    address = node.child("ADDR")
    if address is not None:
        from ._substructures import parse_address

        record.address = parse_address(address)
    record.phones, record.emails, record.faxes, record.web_pages = _contacts(node)
    record.media_links = _media_links(node, resolver)
    record.notes = _notes(node, resolver)
    record.identifiers = _identifiers(node)


def _populate_shared_note(record: SharedNote, node: Node, resolver: Resolver) -> None:
    record.mime = node.text("MIME")
    record.language = node.text("LANG")
    record.translations = [parse_note_translation(c) for c in node.all("TRAN")]
    record.source_citations = _source_citations(node, resolver)
    record.identifiers = _identifiers(node)


def _populate_record(record: Record, node: Node, resolver: Resolver) -> None:
    if isinstance(record, Individual):
        _populate_individual(record, node, resolver)
    elif isinstance(record, Family):
        _populate_family(record, node, resolver)
    elif isinstance(record, Multimedia):
        _populate_multimedia(record, node, resolver)
    elif isinstance(record, Source):
        _populate_source(record, node, resolver)
    elif isinstance(record, Repository):
        _populate_repository(record, node, resolver)
    elif isinstance(record, Submitter):
        _populate_submitter(record, node, resolver)
    elif isinstance(record, SharedNote):  # pragma: no branch - exhaustive over made records
        _populate_shared_note(record, node, resolver)
    record.extensions = [
        parse_extension_structure(c, resolver) for c in node.children if c.tag.startswith("_")
    ]
    record.change_date = _change_date(node, resolver)
    record.creation_date = _creation_date(node)


# --- ChildLink membership detail (pass 3, ADR-0004) -------------------------


def _apply_child_link_detail(pairs: list[tuple[Record, Node]], resolver: Resolver) -> None:
    for record, node in pairs:
        if not isinstance(record, Individual):
            continue
        for famc in node.all("FAMC"):
            pedi = famc.child("PEDI")
            stat = famc.child("STAT")
            if pedi is None and stat is None:
                continue
            if famc.value is None:
                continue
            family = resolver.record(famc.value, Family)
            link = ChildLink(
                individual=record,
                pedigree=parse_enum(pedi.value, Pedigree) if pedi and pedi.value else None,
                pedigree_phrase=pedi.text("PHRASE") if pedi else None,
                status=parse_enum(stat.value, FamcStatus) if stat and stat.value else None,
                status_phrase=stat.text("PHRASE") if stat else None,
            )
            for index, child in enumerate(family.children):
                if child is record:
                    family.children[index] = link
                    break


# --- orchestration ----------------------------------------------------------


def build_document(roots: list[Node]) -> Document:
    """Assemble a Document from its level-0 structure trees (two-pass)."""
    head_node: Node | None = None
    trailer = False
    record_nodes: list[Node] = []

    for node in roots:
        if node.tag == "HEAD":
            if head_node is not None:
                raise ParseError("more than one HEAD", tag="HEAD")
            head_node = node
        elif node.tag == "TRLR":
            trailer = True
        else:
            record_nodes.append(node)

    if head_node is None:
        raise ParseError("document has no HEAD")
    if not trailer:
        raise ParseError("document has no TRLR")

    resolver = Resolver(parse_schema(head_node))

    pairs: list[tuple[Record, Node]] = []
    for node in record_nodes:
        record = _make_record(node)
        if node.line.xref is None:
            raise ParseError(f"{node.tag} record has no cross-reference id", tag=node.tag)
        resolver.register(node.line.xref, record)
        pairs.append((record, node))

    for record, node in pairs:
        _populate_record(record, node, resolver)

    header = parse_header(head_node, resolver)
    _apply_child_link_detail(pairs, resolver)
    return Document(header=header, records=[record for record, _ in pairs])
