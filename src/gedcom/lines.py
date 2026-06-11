"""The GEDCOM line primitive and renderer.

This module is the only place that knows the §1.3 byte grammar: how a
structure's level, cross-reference id, tag, and value become physical
lines of text, including ``CONT`` continuation splitting, the leading-``@``
escape, banned-character rejection, and the chosen line terminator.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

_NEWLINE_RE = re.compile(r"\r\n|\r|\n")


class BannedCharacterError(ValueError):
    """Raised when a payload contains a character GEDCOM 7 forbids (§1.1)."""


def _is_banned(cp: int) -> bool:
    return (
        cp <= 0x08
        or cp in (0x0B, 0x0C)
        or 0x0E <= cp <= 0x1F
        or cp == 0x7F
        or 0x80 <= cp <= 0x9F
        or 0xD800 <= cp <= 0xDFFF
        or cp in (0xFFFE, 0xFFFF)
    )


@dataclass(frozen=True)
class Line:
    """A single logical GEDCOM structure line.

    ``value`` holds the payload as a string. When ``is_pointer`` is true the
    value is a cross-reference pointer (e.g. ``@I1@`` or ``@VOID@``) and is
    emitted verbatim; otherwise it is a line string subject to ``CONT``
    splitting and the leading-``@`` escape.
    """

    level: int
    tag: str
    value: str | None = None
    xref: str | None = None
    is_pointer: bool = False


def _escape(segment: str) -> str:
    return "@" + segment if segment.startswith("@") else segment


def _check_banned(segment: str) -> None:
    for ch in segment:
        if _is_banned(ord(ch)):
            raise BannedCharacterError(f"U+{ord(ch):04X} is not permitted in GEDCOM 7 output")


def render_line(line: Line) -> list[str]:
    """Render one logical line into one or more physical line strings."""
    parts = [str(line.level)]
    if line.xref is not None:
        parts.append(line.xref)
    parts.append(line.tag)
    head = " ".join(parts)

    if line.value is None:
        return [head]

    if line.is_pointer:
        _check_banned(line.value)
        return [f"{head} {line.value}"]

    segments = _NEWLINE_RE.split(line.value)
    first = segments[0]
    _check_banned(first)
    physical = [head if first == "" else f"{head} {_escape(first)}"]

    cont_head = f"{line.level + 1} CONT"
    for seg in segments[1:]:
        _check_banned(seg)
        physical.append(cont_head if seg == "" else f"{cont_head} {_escape(seg)}")
    return physical


def render(lines: Iterable[Line], *, eol: str = "\n") -> str:
    """Render a sequence of logical lines to GEDCOM text with the given EOL."""
    out: list[str] = []
    for line in lines:
        out.extend(render_line(line))
    return "".join(s + eol for s in out)
