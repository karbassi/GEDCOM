"""The deliberate null pointer (`@VOID@`)."""

from __future__ import annotations


class VoidPointer:
    """A deliberate null pointer, serialized as ``@VOID@`` (§1.3)."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "VOID"


VOID = VoidPointer()
