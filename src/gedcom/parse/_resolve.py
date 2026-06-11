"""Cross-reference resolution: ``@xref@`` pointer payloads → record objects.

The inverse of :class:`gedcom.xref.XrefTable`. Built in the reader's first pass
(every level-0 record registered by its wire id) and consulted in the second
pass to wire object references (ADR-0001). ``@VOID@`` resolves to the shared
:data:`~gedcom.model.VOID` null pointer; any other unresolvable id is a
:class:`~gedcom.parse.errors.ParseError`.
"""

from __future__ import annotations

from ..model import VOID, Record, VoidPointer
from .errors import ParseError


class Resolver:
    """A built mapping from a record's wire ``@xref@`` id to its object."""

    def __init__(self, schema: dict[str, str] | None = None) -> None:
        self._by_xref: dict[str, Record] = {}
        # SCHMA-declared extension identifier (tag/enum) -> URI, parsed from the
        # header; consulted when reconstructing arbitrary extension structures.
        self.schema: dict[str, str] = schema or {}

    def register(self, xref: str, record: Record) -> None:
        if xref in self._by_xref:
            raise ParseError(f"duplicate cross-reference id {xref}")
        self._by_xref[xref] = record

    def _lookup(self, value: str) -> Record:
        try:
            return self._by_xref[value]
        except KeyError:
            raise ParseError(f"pointer {value} does not resolve to a record") from None

    def record[T: Record](self, value: str, expected: type[T]) -> T:
        """Resolve a (non-void) pointer to a record of the expected type."""
        record = self._lookup(value)
        if not isinstance(record, expected):
            raise ParseError(
                f"pointer {value} resolves to {type(record).__name__}, expected {expected.__name__}"
            )
        return record

    def pointer[T: Record](self, value: str, expected: type[T]) -> T | VoidPointer:
        """Resolve a pointer that may be ``@VOID@``."""
        if value == "@VOID@":
            return VOID
        return self.record(value, expected)
