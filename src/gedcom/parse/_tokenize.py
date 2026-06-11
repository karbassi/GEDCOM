"""Physical GEDCOM text → logical :class:`~gedcom.lines.Line` sequence.

The inverse of :func:`gedcom.lines.render_line`: it parses the §1.3 byte
grammar (level, optional cross-reference id, tag, optional value), reassembles
``CONT`` continuations into a single ``\\n``-joined value, undoes the
leading-``@`` text escape, and classifies pointer values. Everything the
tokenizer emits is a logical ``Line`` the writer would accept back.
"""

from __future__ import annotations

import re
from dataclasses import replace

from ..lines import Line
from .errors import ParseError

_NEWLINE_RE = re.compile(r"\r\n|\r|\n")
_LINE_RE = re.compile(r"^(?P<level>0|[1-9][0-9]*) (?P<rest>.*)$")
_XREF_RE = re.compile(r"^(?P<xref>@[^@\s]+@) (?P<rest>.*)$")
_TAG_RE = re.compile(r"^(?P<tag>[A-Za-z0-9_]+)(?: (?P<value>.*))?$")
_POINTER_RE = re.compile(r"^@[^@\s]+@$")
_BOM = "﻿"


def _parse_physical(text: str, lineno: int) -> Line:
    """Parse one physical line string into a raw (pre-``CONT``-fold) ``Line``."""
    m = _LINE_RE.match(text)
    if m is None:
        raise ParseError(f"not a GEDCOM line: {text!r}", line=lineno)
    level = int(m.group("level"))
    rest = m.group("rest")

    xref: str | None = None
    xm = _XREF_RE.match(rest)
    if xm is not None:
        xref = xm.group("xref")
        rest = xm.group("rest")

    tm = _TAG_RE.match(rest)
    if tm is None:
        raise ParseError(f"missing or malformed tag: {text!r}", line=lineno)
    tag = tm.group("tag")
    value = tm.group("value")  # None when the line has no payload

    return Line(level=level, tag=tag, value=value, xref=xref)


def _unescape(segment: str) -> str:
    """Undo render's leading-``@`` escape (``@@foo`` → ``@foo``)."""
    return segment[1:] if segment.startswith("@@") else segment


def tokenize(text: str) -> list[Line]:
    """Tokenize GEDCOM text into logical lines (``CONT`` already folded)."""
    if text.startswith(_BOM):
        text = text[len(_BOM) :]

    physical = _NEWLINE_RE.split(text)
    if physical and physical[-1] == "":
        physical.pop()  # the terminator after the final line, not a real line

    logical: list[Line] = []
    for index, raw_text in enumerate(physical, start=1):
        raw = _parse_physical(raw_text, index)

        if raw.tag == "CONT":
            if not logical:
                raise ParseError("CONT with no preceding line", line=index)
            prev = logical[-1]
            base = prev.value if prev.value is not None else ""
            segment = _unescape(raw.value) if raw.value is not None else ""
            logical[-1] = replace(prev, value=f"{base}\n{segment}")
            continue

        if raw.value is not None and _POINTER_RE.match(raw.value):
            logical.append(replace(raw, is_pointer=True))
        elif raw.value is not None:
            logical.append(replace(raw, value=_unescape(raw.value)))
        else:
            logical.append(raw)

    return logical
