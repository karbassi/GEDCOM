"""Document-level validation (ADR-0002).

Cross-record rules that can only be checked once the object graph is
complete: references resolve within the Document, xref ids are unique,
required substructures are present, forbidden record cycles are absent, and
deprecated constructs are flagged. Value-level invariants are enforced
earlier, at construction, by the value types themselves.

Strict mode raises on any error; lenient mode returns all messages (errors
and warnings) so the caller can warn and still emit best-effort output.
Later slices extend :func:`_issues` with their own rules.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from .cardinality import check_tree, load_rules
from .model import (
    Document,
    Family,
    Individual,
    Multimedia,
    Note,
    SharedNote,
    Submitter,
    VoidPointer,
)
from .serialize import serialize_document
from .xref import XrefError, build_xref_table


class ValidationError(ValueError):
    """Raised by :func:`validate` in strict mode when an error rule fails."""


@dataclass(frozen=True)
class Issue:
    message: str
    is_error: bool = True


def _issues(document: Document) -> Iterator[Issue]:
    known = {id(record) for record in document.records}

    submitter = document.header.submitter
    if submitter is not None and id(submitter) not in known:
        yield Issue("HEAD.SUBM points to a Submitter not added to the Document")

    seen_overrides: set[str] = set()
    for record in document.records:
        if record.xref_id is not None:
            key = f"@{record.xref_id}@"
            if key in seen_overrides:
                yield Issue(f"duplicate cross-reference id {key}")
            seen_overrides.add(key)

        if isinstance(record, Submitter) and not record.name:
            yield Issue("SUBM requires a non-empty NAME")

        if isinstance(record, Multimedia):
            if not record.files:
                yield Issue("OBJE requires at least one FILE")
            for file in record.files:
                if not file.form:
                    yield Issue("every OBJE.FILE requires a non-empty FORM")

        if isinstance(record, SharedNote):
            yield from _note_translation_issues(record)

        for note in getattr(record, "notes", []):
            if isinstance(note, Note):
                yield from _note_translation_issues(note)

        if isinstance(record, Family):
            yield from _family_issues(record, known)

        if isinstance(record, Individual | Family):
            yield from _event_attribute_issues(record)

        if isinstance(record, Individual):
            for ordinance in record.lds_ordinances:
                if ordinance.tag == "SLGC" and ordinance.family is None:
                    yield Issue("SLGC requires a FAMC pointing to the sealed family")

        identifiers = getattr(record, "identifiers", [])
        for identifier in identifiers:
            if identifier.kind == "EXID" and identifier.type is None:
                yield Issue(
                    "EXID without a TYPE is deprecated (TYPE becomes required in 8.0)",
                    is_error=False,
                )

    yield from _cardinality_issues(document)


def _cardinality_issues(document: Document) -> Iterator[Issue]:
    """Check the emitted structure tree against the spec cardinality rules."""
    try:
        lines = list(serialize_document(document, build_xref_table(document)))
    except XrefError:
        return  # reference rules above already report the underlying problem
    stream = ((line.level, line.tag) for line in lines)
    for violation in check_tree(stream, load_rules()):
        yield Issue(violation.message)


# Tags whose TYPE substructure is required (§3.3).
_TYPE_REQUIRED_ATTRIBUTES = frozenset({"IDNO", "FACT"})


def _event_attribute_issues(record: Individual | Family) -> Iterator[Issue]:
    for event in record.events:
        if event.tag == "EVEN":
            if not event.text:
                yield Issue("a generic EVEN requires a non-empty text payload")
            if event.type is None:
                yield Issue("a generic EVEN requires a TYPE")
    for attribute in record.attributes:
        if attribute.tag in _TYPE_REQUIRED_ATTRIBUTES and attribute.type is None:
            yield Issue(f"{attribute.tag} requires a TYPE")


def _note_translation_issues(note: Note | SharedNote) -> Iterator[Issue]:
    for tran in note.translations:
        if tran.mime is None and tran.language is None:
            yield Issue("a note TRAN requires a MIME and/or a LANG")


def _family_issues(family: Family, known: set[int]) -> Iterator[Issue]:
    for role, person in (("HUSB", family.husband), ("WIFE", family.wife)):
        if person is not None and id(person) not in known:
            yield Issue(f"FAM.{role} points to an Individual not added to the Document")

    seen_children: set[int] = set()
    for child in family.children:
        if isinstance(child, VoidPointer):
            continue
        if id(child) not in known:
            yield Issue("FAM.CHIL points to an Individual not added to the Document")
        if id(child) in seen_children:
            yield Issue("FAM lists the same Individual as a child more than once")
        seen_children.add(id(child))


def validate(document: Document, *, strict: bool = True) -> list[str]:
    """Validate a document; raise in strict mode, else return all messages."""
    issues = list(_issues(document))
    if strict:
        errors = [issue.message for issue in issues if issue.is_error]
        if errors:
            raise ValidationError("; ".join(errors))
    return [issue.message for issue in issues]
