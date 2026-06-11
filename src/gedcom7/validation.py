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

from .model import Document, Family, Submitter, VoidPointer


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

        if isinstance(record, Family):
            yield from _family_issues(record, known)


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
