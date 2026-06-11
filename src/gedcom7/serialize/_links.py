"""Derived family-membership index (ADR-0001).

Individuals do not store their `FAMS`/`FAMC` links; the writer derives them
from the `Family` records so the matching back-pointers are emitted without
the caller maintaining both sides.
"""

from __future__ import annotations

from ..model import ChildLink, Document, Family, Individual, VoidPointer


class FamilyIndex:
    """Maps an individual to the families it is a spouse or child in."""

    def __init__(self) -> None:
        self._spouse: dict[int, list[Family]] = {}
        self._child: dict[int, list[Family]] = {}
        self._child_detail: dict[tuple[int, int], ChildLink] = {}

    def spouse_families(self, individual: Individual) -> list[Family]:
        return self._spouse.get(id(individual), [])

    def child_families(self, individual: Individual) -> list[Family]:
        return self._child.get(id(individual), [])

    def child_detail(self, individual: Individual, family: Family) -> ChildLink | None:
        """The membership detail for this child in this family, if any."""
        return self._child_detail.get((id(individual), id(family)))

    def _add_spouse(self, individual: Individual, family: Family) -> None:
        self._spouse.setdefault(id(individual), []).append(family)

    def _add_child(self, individual: Individual, family: Family) -> None:
        self._child.setdefault(id(individual), []).append(family)


def build_family_index(document: Document) -> FamilyIndex:
    index = FamilyIndex()
    for record in document.records:
        if not isinstance(record, Family):
            continue
        if record.husband is not None:
            index._add_spouse(record.husband, record)
        if record.wife is not None:
            index._add_spouse(record.wife, record)
        for child in record.children:
            if isinstance(child, ChildLink):
                index._add_child(child.individual, record)
                index._child_detail[id(child.individual), id(record)] = child
            elif not isinstance(child, VoidPointer):
                index._add_child(child, record)
    return index
