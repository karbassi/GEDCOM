"""The located error type shared across the CLI's reader and loader."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager


class LoadError(ValueError):
    """An authoring-document error carrying a dotted path to the bad node.

    ``raw`` is the bare message; ``path`` is the location built up as the
    loader descends (e.g. ``individuals[2].events[0].date``). The string form
    prefixes the location when present.
    """

    def __init__(self, message: str, path: str = "") -> None:
        self.raw = message
        self.path = path
        location = path.lstrip(".")
        super().__init__(f"{location}: {message}" if location else message)


@contextmanager
def at(segment: str) -> Iterator[None]:
    """Prefix any :class:`LoadError` raised in the block with ``segment``.

    ``segment`` is ``".key"`` for a mapping key or ``"[i]"`` for a list index;
    nesting composes a full dotted/indexed path from the outside in.
    """
    try:
        yield
    except LoadError as error:
        raise LoadError(error.raw, segment + error.path) from None
