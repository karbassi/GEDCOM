"""The reader's single error type."""

from __future__ import annotations


class ParseError(ValueError):
    """Raised when input is not well-formed GEDCOM 7 this library could emit.

    The reader is strict (ADR-0005): malformed grammar, undeclared tags, and
    values that violate the model's construction invariants all raise here.
    ``line`` is the 1-based physical line number when known; ``tag`` is the
    offending structure tag.
    """

    def __init__(self, message: str, *, line: int | None = None, tag: str | None = None) -> None:
        self.line = line
        self.tag = tag
        location = f" (line {line})" if line is not None else ""
        super().__init__(f"{message}{location}")
