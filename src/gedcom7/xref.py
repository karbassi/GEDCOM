"""Cross-reference id allocation and pointer resolution (ADR-0001).

The writer owns the document-local xref namespace. Ids are assigned
deterministically by record order (so output is stable and diffable);
records may pin a preferred id via ``xref_id``. Pointers are resolved by
object identity. ``VOID`` is the deliberate null pointer.
"""

from __future__ import annotations

from .model import Document, Individual, Record, Submitter

# Record class → xref id prefix. Extended as record types are added.
_PREFIXES: list[tuple[type, str]] = [
    (Individual, "I"),
    (Submitter, "U"),
]


class _Void:
    """Sentinel for a deliberate null pointer (`@VOID@`)."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "VOID"


VOID = _Void()


class XrefError(ValueError):
    """Raised on duplicate or unresolvable cross-reference ids."""


def _prefix_for(record: Record) -> str:
    for cls, prefix in _PREFIXES:
        if isinstance(record, cls):
            return prefix
    raise XrefError(f"no xref prefix is defined for {type(record).__name__}")


class XrefTable:
    """A built mapping from record object identity to its `@xref@` id."""

    def __init__(self) -> None:
        self._ids: dict[int, str] = {}
        self._keep: list[Record] = []  # hold refs so id() can't be reused
        self._used: set[str] = set()

    def _register(self, record: Record, xref: str) -> None:
        if xref in self._used:
            raise XrefError(f"duplicate cross-reference id {xref}")
        self._used.add(xref)
        self._ids[id(record)] = xref
        self._keep.append(record)

    def of(self, record: Record) -> str:
        try:
            return self._ids[id(record)]
        except KeyError:
            raise XrefError(
                f"{type(record).__name__} is referenced but was not added to the Document's records"
            ) from None

    def resolve(self, ref: Record | _Void) -> str:
        """Resolve a pointer target to its id, or `@VOID@` for the null pointer."""
        if isinstance(ref, _Void):
            return "@VOID@"
        return self.of(ref)


def build_xref_table(document: Document) -> XrefTable:
    """Assign ids to every record, honoring overrides and skipping collisions."""
    table = XrefTable()
    for record in document.records:
        if record.xref_id is not None:
            table._register(record, f"@{record.xref_id}@")

    counters: dict[str, int] = {}
    for record in document.records:
        if id(record) in table._ids:
            continue
        prefix = _prefix_for(record)
        seq = counters.get(prefix, 0)
        candidate = f"@{prefix}{seq + 1}@"
        while candidate in table._used:
            seq += 1
            candidate = f"@{prefix}{seq + 1}@"
        counters[prefix] = seq + 1
        table._register(record, candidate)
    return table
